"""
********
I2C Core
********
:Author: Michael Murton
"""
# Copyright (c) 2019-2021 MQTTany contributors
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

from .common import CONF_KEY_ADDRESS  # pylint: disable=unused-import
from .common import CONF_KEY_BUS_SCAN  # type: ignore
from .common import (
    CONF_KEY_BUS,
    CONF_KEY_DEVICE,
    CONF_KEY_NAME,
    CONF_KEY_POLL_INT,
    CONF_OPTIONS,
    CONFIG,
    log,
    nodes,
    validateAddress,
    validateBus,
)
from .device import getDeviceClass, updateConfOptions
from .device.base import I2CDevice

buses: t.Dict[str, t.Any] = {}
devices: t.Dict[str, I2CDevice] = {}
polling_timer = None


def build_device(
    device_id: str, device_config: t.Dict[str, t.Any]
) -> t.Union[I2CDevice, None]:
    from smbus2 import SMBus

    if not validate_id(device_id):
        log.warn("'%s' is not a valid ID and will be ignored", device_id)
        return None

    device: str = device_config[CONF_KEY_DEVICE]
    bus = validateBus(device_config[CONF_KEY_BUS])
    address = validateAddress(device_config[CONF_KEY_ADDRESS])
    name: str = device_config[CONF_KEY_NAME].format(
        device_id=device_id, address=address, device=device.upper()
    )
    clazz = getDeviceClass(device)

    if bus is not None:
        if bus not in buses:
            buses[bus] = SMBus()
    else:
        log.error("Failed to configure %s '%s', bus is invalid.", device.upper(), name)
        return None

    if clazz:
        if address is None:
            log.warn(
                "%s '%s' has an invalid address '%s'",
                device.upper(),
                name,
                device_config[CONF_KEY_ADDRESS],
            )
            return None

        log.debug(
            "Configuring %s '%s' at address 0x%02x on bus '%s'",
            device.upper(),
            name,
            address,
            bus,
        )
        return clazz(
            id=device_id,
            name=name,
            device=device,
            address=address,
            bus=buses[bus],
            bus_path=bus,
            device_config=device_config,
        )
    else:
        log.warn("%s '%s' is not a supported device", device.upper(), name)
        return None


def load(config_raw: t.Dict[str, t.Any] = {}) -> bool:
    """
    Initializes the module
    """
    try:
        from smbus2 import SMBus

        del SMBus
    except ModuleNotFoundError:
        log.error(
            "MQTTany's I2C module requires 'smbus2' to be installed, "
            "please see the wiki for instructions on how to install requirements"
        )
        return False

    conf_options = updateConfOptions(CONF_OPTIONS)
    conf_options.move_to_end("regex:.+")

    config_data = parse_config(config_raw, conf_options, log)
    del config_raw
    if config_data:
        log.debug("Config loaded")
        CONFIG.update(config_data)
        del config_data

        for device_id in [key for key in CONFIG if isinstance(CONFIG[key], dict)]:
            device_config = CONFIG.pop(device_id)
            device_object = build_device(device_id, device_config)
            if device_object:
                devices[device_id] = device_object
                nodes[device_id] = device_object.get_node()

        return True
    else:
        log.error("Error loading config")
        return False


def start() -> None:
    """
    Actions to be done in the subprocess before the loop starts
    """
    from smbus2 import SMBus

    # Open I2C buses
    log.debug("Opening I2C bus streams")
    for bus in buses:
        try:
            t.cast(SMBus, buses[bus]).open(bus)
        except IOError as err:
            log.error("Failed to open I2C bus '%s': %s", bus, err)

    # TODO Scan bus for devices
    # if CONFIG[CONF_KEY_BUS_SCAN]:
    #    for bus in buses:
    #        log.info("Scanning I2C bus '{bus}' for devices")

    # Setup devices
    for id in devices:
        if devices[id].setup():
            log.debug(
                "Successfully setup %s '%s'", devices[id].device, devices[id].name
            )
        else:
            log.warn("Failed to setup %s '%s'", devices[id].device, devices[id].name)
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

    log.debug("Disconnecting from bus streams")
    for bus in buses:
        if buses[bus]:
            buses[bus].close()


def device_message(message: SubscribeMessage) -> None:
    """
    Callback for device messages
    """
    path = message.path.strip("/").split("/")  # strip '/'
    if message.path.strip("/") == "i2c/poll-all":
        poll_all()
    elif path[0] in devices:
        devices[path[0]].message_callback(message)
    else:
        log.debug("Received message on unregistered path: %s", message)


def poll_message(message: SubscribeMessage) -> None:
    """
    Callback for poll all
    """
    if message.path.strip("/") == "i2c/poll-all/set":
        poll_all()
    else:
        log.debug("Received message on unregistered path: %s", message)


def poll_all() -> None:
    """
    Polls all devices
    """
    log.debug("Polling all devices")
    for id in devices:
        devices[id].publish_state()


def poll_interval() -> None:
    """ Polls all devices and restarts the timer """
    log.debug("Polling timer fired")
    global polling_timer
    polling_timer = Timer(CONFIG[CONF_KEY_POLL_INT], poll_interval)
    polling_timer.start()
    poll_all()
