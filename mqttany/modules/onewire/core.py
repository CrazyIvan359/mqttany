"""
*******************
Dallas OneWire Core
*******************

:Author: Michael Murton
"""
# Copyright (c) 2019 MQTTany contributors
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

from collections import OrderedDict
from threading import Timer

from config import parse_config

from modules.mqtt import resolve_topic, topic_matches_sub, publish, subscribe

from modules.onewire import bus
from modules.onewire import device
from modules.onewire.common import config
from modules.onewire.common import *

all = [  ]

CONF_OPTIONS = OrderedDict([ # MUST USE ORDEREDDICT WHEN REGEX KEY MAY MATCH OTHER KEYS
    (CONF_KEY_BUS, {"default": "w1", "selection": []}),
    (CONF_KEY_TOPIC, {"default": "{module_name}"}),
    (CONF_KEY_TOPIC_GETTER, {"default": "poll"}),
    (CONF_KEY_POLL_INT, {"type": float, "default": 0.0}),
    (CONF_KEY_BUS_SCAN, {"type": bool, "default": False}),
    ("regex:.+", {
        "type": "section",
        "required": False,
        CONF_KEY_ADDRESS: {"type": (str, list)},
        CONF_KEY_TOPIC: {"type": (str, list), "default": "{device_name}"},
        CONF_KEY_FIRST_INDEX: {"type": int, "default": 0},
    })
])

TEXT_NAME = TEXT_PACKAGE_NAME

ow_bus = None
devices = []
queue = None
polling_timer = None


def build_device(device_name, ow_bus, device_config={}, topic=None, address=None, index=None):
    valid_address = ow_bus.validateAddress(address or device_config.get(CONF_KEY_ADDRESS, None))
    device_type = device.getDeviceTypeByFamily(address)
    if not valid_address:
        log.warn("Device '{name}' has an invalid address '{address}'".format(
            name=device_name, address=address or device_config.get(CONF_KEY_ADDRESS, "")))
        return False
    clazz = device.getDevice(valid_address)
    if clazz:
        log.debug("Configuring {type} '{name}' with options: {options}".format(
                type=device_type,
                name=device_name, options=device_config))
        return clazz(
            device_name,
            valid_address,
            device_type,
            ow_bus,
            topic or device_config.get(CONF_KEY_TOPIC, None) or CONF_OPTIONS["regex:.+"][CONF_KEY_TOPIC]["default"],
            device_config,
            index=index
        )
    else:
        log.warn("{type} '{name}' is not a supported device".format(
                type=device_type or "Device", name=device_name))
        return None


def init(config_data={}):
    """
    Initializes the module
    """
    # add device options from device modules
    CONF_OPTIONS["regex:.+"].update(device.getConfDeviceOptions())
    # add bus types from bus modules
    CONF_OPTIONS[CONF_KEY_BUS]["selection"].extend(bus.getConfBusTypes())
    # add bus options from bus modules
    CONF_OPTIONS.update(bus.getConfBusOptions())
    # make sure wildcard regex match is at the end
    CONF_OPTIONS.move_to_end("regex:.+")

    raw_config = parse_config(config_data, CONF_OPTIONS, log)
    if raw_config:
        log.debug("Config loaded")
        config.update(raw_config)

        global ow_bus
        ow_bus = bus.getBus(config[CONF_KEY_BUS])
        if not ow_bus.valid:
            log.error("OneWire bus is not available")
            return False

        for device_name in [key for key in config if isinstance(config[key], dict)]:
            device_config = config.pop(device_name)

            if isinstance(device_config[CONF_KEY_ADDRESS], list):
                for index in range(len(device_config[CONF_KEY_ADDRESS])):
                    if isinstance(device_config[CONF_KEY_TOPIC], list):
                        topic = device_config[CONF_KEY_TOPIC][index]
                    else:
                        topic = device_config[CONF_KEY_TOPIC]
                    device_object = build_device(
                        device_name,
                        ow_bus,
                        device_config,
                        topic=topic,
                        address=device_config[CONF_KEY_ADDRESS][index],
                        index=index + device_config[CONF_KEY_FIRST_INDEX]
                    )
                    if device_object:
                        devices.append(device_object)
            else:
                device_object = build_device(
                    device_name,
                    ow_bus,
                    device_config
                )
                if device_object:
                    devices.append(device_object)

        return True
    else:
        log.error("Error loading config")
        return False


def pre_loop():
    """
    Actions to be done in the subprocess before the loop starts
    """
    if config[CONF_KEY_BUS_SCAN]:
        log.info("Scanning OneWire bus for devices")
        scan_results = ow_bus.scan()
        for address in scan_results:
            log.debug("Found device with address '{address}'".format(address=address))
            address = ow_bus.validateAddress(address)
            if not [dev for dev in devices if dev.address == address]:
                device_object = build_device(
                    address,
                    ow_bus,
                    address=address
                )
                if device_object:
                    devices.append(device_object)
        if not scan_results:
            log.debug("Scan found no unconfigured devices")

    log.info("Setting up devices")
    for index, dev in enumerate(devices):
        if dev.setup():
            log.debug("Successfully setup {type} '{name}'".format(
                    type=dev.type, name=dev.name))

            subscribe(
                    "{}/+/#".format(dev.topic),
                    callback=callback_device_message,
                )
        else:
            log.warn("Failed to setup '{name}', it will be ignored".format(name=dev.name))
            del devices[index]

    log.debug("Adding MQTT subscription to poll all devices topic")
    subscribe(
            config[CONF_KEY_TOPIC_GETTER],
            callback=callback_poll_all,
            subtopics=["{module_topic}"],
            substitutions={
                "module_topic": config[CONF_KEY_TOPIC],
                "module_name": TEXT_NAME,
            }
        )

    if config[CONF_KEY_POLL_INT] > 0:
        log.debug("Starting polling timer with interval of {interval}s".format(
                interval=config[CONF_KEY_POLL_INT]))
        global polling_timer
        polling_timer = Timer(config[CONF_KEY_POLL_INT], poll_interval)
        polling_timer.start()

    poll_all()


def post_loop():
    """
    Actions to be done in the subprocess after the loop is exited
    """
    if polling_timer is not None:
        log.debug("Stopping polling timer")
        polling_timer.cancel()


def callback_device_message(client, userdata, message):
    """
    Callback for message on device topic
    """
    queue.put_nowait({
        "func": "_device_message",
        "args": [message.topic, message.payload]
    })


def _device_message(topic, payload):
    for dev in devices:
        if topic_matches_sub("{}/+/#".format(dev.topic), topic):
            dev.handle_message(topic, payload)


def callback_poll_all(client, userdata, message):
    """
    Callback for poll all
    """
    queue.put_nowait({
        "func": "poll_all"
    })


def poll_all():
    """
    Polls all devices
    """
    log.debug("Polling all devices")
    for dev in devices:
        dev.publish_state()


def poll_interval():
    """ Polls all devices and restarts the timer """
    log.debug("Polling timer fired")
    global polling_timer
    polling_timer = Timer(config[CONF_KEY_POLL_INT], poll_interval)
    polling_timer.start()
    poll_all()
