"""
*******************
Dallas OneWire Core
*******************

:Author: Michael Murton
"""
# Copyright (c) 2019-2025 MQTTany contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

__all__ = ["load", "start", "stop", "device_message", "poll_message"]

import typing as t
from threading import Timer

from config import parse_config

from common import SubscribeMessage, validate_id

from . import bus, device
from .bus.base import OneWireBus
from .common import (
    CONF_KEY_ADDRESS,
    CONF_KEY_BUS,
    CONF_KEY_BUS_SCAN,
    CONF_KEY_FIRST_INDEX,
    CONF_KEY_NAME,
    CONF_KEY_POLL_INT,
    CONF_OPTIONS,
    CONFIG,
    log,
    nodes,
)
from .device.base import OneWireDevice

ow_bus: OneWireBus = None  # type: ignore
devices: t.Dict[str, OneWireDevice] = {}
polling_timer = None


def build_device(
    device_id: str,
    device_config: t.Dict[str, t.Any] = {},
    device_name: t.Optional[str] = None,
    address: t.Optional[str] = None,
    index: t.Optional[int] = None,
) -> t.Union[OneWireDevice, None]:
    if not validate_id(device_id):
        log.warn("'%s' is not a valid ID and will be ignored", device_id)
        return None

    valid_address = ow_bus.validateAddress(
        address or device_config.get(CONF_KEY_ADDRESS, None)
    )
    if valid_address:
        device_type = device.getDeviceTypeByFamily(valid_address)
        clazz = device.getDevice(valid_address)
        if clazz:
            device_id = (
                device_id
                if index is None
                else f"{device_id}-{index + device_config[CONF_KEY_FIRST_INDEX]}"
            )
            device_name = (
                device_name
                # use address for devices discovered on bus scan
                or f"{device_config.get(CONF_KEY_NAME, valid_address)}"
                f"{'' if index is None else f' {index + device_config[CONF_KEY_FIRST_INDEX]}'}"
            )
            device_name = device_name.format(
                device_id=device_id, device_type=device_type, address=valid_address
            )
            log.debug(
                "Configuring %s '%s' at address '%s'",
                device_type,
                device_name,
                valid_address,
            )
            return clazz(
                id=device_id,
                name=device_name,
                device=device_type,
                address=valid_address,
                bus=ow_bus,
                device_config=device_config,
            )
        else:
            log.warn("%s '%s' is not a supported device", device_type, device_name)
    else:
        log.warn(
            "Device '%s' has an invalid address '%s'",
            device_name,
            address or device_config.get(CONF_KEY_ADDRESS, ""),
        )
    return None


def load(config_raw: t.Dict[str, t.Any] = {}) -> bool:
    """
    Initializes the module
    """
    conf_options = CONF_OPTIONS
    # add device options from device modules
    conf_options["regex:.+"] = device.updateConfOptions(conf_options["regex:.+"])
    # add bus types from bus modules
    conf_options[CONF_KEY_BUS]["selection"].extend(bus.getConfBusTypes())
    # add bus options from bus modules
    conf_options = bus.updateConfOptions(conf_options)
    # make sure wildcard regex match is at the end
    conf_options.move_to_end("regex:.+")

    config_data = parse_config(config_raw, conf_options, log)
    del config_raw
    if config_data:
        log.debug("Config loaded")
        CONFIG.update(config_data)
        del config_data

        bus_cls = bus.getBus(CONFIG[CONF_KEY_BUS])
        if bus_cls is None or not bus_cls.valid():
            log.error("OneWire bus is not available")
            return False
        global ow_bus
        ow_bus = bus_cls()

        for device_id in [key for key in CONFIG if isinstance(CONFIG[key], dict)]:
            device_config: t.Dict[str, t.Any] = CONFIG.pop(device_id)

            if isinstance(device_config[CONF_KEY_ADDRESS], list):
                for index in range(len(device_config[CONF_KEY_ADDRESS])):
                    device_object = build_device(
                        device_id=device_id,
                        device_config=device_config,
                        device_name=device_config[CONF_KEY_NAME][index]
                        if isinstance(device_config[CONF_KEY_NAME], list)
                        else None,
                        address=device_config[CONF_KEY_ADDRESS][index],
                        index=index,
                    )
                    if device_object:
                        devices[device_id] = device_object
                        nodes[device_id] = device_object.get_node()
            else:
                device_object = build_device(
                    device_id=device_id, device_config=device_config
                )
                if device_object:
                    devices[device_id] = device_object
                    nodes[device_id] = device_object.get_node()

        if CONFIG[CONF_KEY_BUS_SCAN]:
            log.info("Scanning OneWire bus for unconfigured devices")
            scan_results = ow_bus.scan()
            for address in scan_results:
                address = ow_bus.validateAddress(address)
                if address is not None:
                    if not [id for id in devices if devices[id].address == address]:
                        log.debug(
                            "Scan found unconfigured device at address '%s',address"
                        )
                        device_object = build_device(address, address=address)
                        if device_object:
                            devices[device_object.id] = device_object
                            nodes[device_object.id] = device_object.get_node()
                            log.info(
                                "Scan added '%s' at address '%s'",
                                device_object.device,
                                address,
                            )

        return True
    else:
        log.error("Error loading config")
        return False


def start() -> None:
    """
    Actions to be done in the subprocess before the loop starts
    """
    log.info("Setting up devices")
    for id in devices:
        if devices[id].setup():
            log.debug(
                "Successfully setup %s '%s'", devices[id].device, devices[id].name
            )
        else:
            log.warn("Failed to setup '%s'", devices[id].name)
            # del devices[id]

    if CONFIG[CONF_KEY_POLL_INT] > 0:
        log.debug(
            "Starting polling timer with interval of %ds", CONFIG[CONF_KEY_POLL_INT]
        )
        global polling_timer
        polling_timer = Timer(CONFIG[CONF_KEY_POLL_INT], poll_interval)
        polling_timer.start()

    poll_all()


def stop() -> None:
    """
    Actions to be done in the subprocess after the loop is exited
    """
    if polling_timer is not None:
        log.debug("Stopping polling timer")
        polling_timer.cancel()

    log.debug("Cleaning up devices")
    for id in devices:
        devices[id].cleanup()


def device_message(message: SubscribeMessage) -> None:
    """
    Callback for device messages
    """
    path = message.path.strip("/").split("/")  # strip '/'
    if path[0] in devices:
        devices[path[0]].message_callback(message)
    else:
        log.debug("Received message on unregistered path: %s", message)


def poll_message(message: SubscribeMessage) -> None:
    """
    Callback for poll all
    """
    if message.path.strip("/") == "onewire/poll-all/set":
        poll_all()
    else:
        log.debug("Received message on unregistered path: %s", message)


def poll_all() -> None:
    """
    Polls all devices
    """
    log.debug("Polling all devices")
    for device_id in devices:
        devices[device_id].publish_state()


def poll_interval() -> None:
    """
    Polls all devices and restarts the timer
    """
    log.debug("Polling timer fired")
    global polling_timer
    polling_timer = Timer(CONFIG[CONF_KEY_POLL_INT], poll_interval)
    polling_timer.start()
    poll_all()
