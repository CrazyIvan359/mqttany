"""
********
I2C Core
********
:Author: Michael Murton
"""
# Copyright (c) 2019-2020 MQTTany contributors
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

try:
    from smbus2 import SMBus
except ImportError:
    raise ImportError(
        "MQTTany's I2C module requires 'smbus2' to be installed, "
        "please see the wiki for instructions on how to install requirements"
    )

from collections import OrderedDict
from threading import Timer

from config import parse_config

from common import update_dict
from modules.mqtt import resolve_topic, topic_matches_sub, publish, subscribe

from modules.i2c.device import getDeviceClass, getConfOptions, getDeviceOptions
from modules.i2c.common import config
from modules.i2c.common import *

__all__ = []

TEXT_NAME = TEXT_PACKAGE_NAME

buses = {}
devices = []
queue = None
polling_timer = None


def build_device(device_name, device_config):
    address = validateAddress(device_config[CONF_KEY_ADDRESS])
    bus = validateBus(device_config[CONF_KEY_BUS])
    device = device_config[CONF_KEY_DEVICE]
    clazz = getDeviceClass(device)

    if bus is not None:
        if bus not in buses:
            buses[bus] = SMBus()
    else:
        log.error(
            "Failed to configure {device} '{name}', bus is invalid.".format(
                device=device, name=device_name
            )
        )
        return None

    if clazz:
        if address is None:
            log.warn(
                "{device} '{name}' has an invalid address '{address}'".format(
                    device=device,
                    name=device_name,
                    address=device_config[CONF_KEY_ADDRESS],
                )
            )
            return False

        log.debug(
            "Configuring {device} '{name}' at address 0x{address:02x} on bus '{bus}'".format(
                device=device, name=device_name, address=address, bus=bus
            )
        )
        return clazz(
            device_name,
            address,
            device,
            bus,
            buses[bus],
            device_config[CONF_KEY_TOPIC],
            device_config,
        )
    else:
        log.warn(
            "{device} '{name}' is not a supported device".format(
                device=device, name=device_name
            )
        )
        return None


def init(config_data={}):
    """
    Initializes the module
    """
    # Add device specific options
    CONF_OPTIONS["regex:.+"].update(getDeviceOptions())
    # Add device options to root
    update_dict(CONF_OPTIONS, getConfOptions())
    CONF_OPTIONS.move_to_end("regex:.+")

    raw_config = parse_config(config_data, CONF_OPTIONS, log)
    del config_data
    if raw_config:
        log.debug("Config loaded")
        config.update(raw_config)
        del raw_config

        for device_name in [key for key in config if isinstance(config[key], dict)]:
            device_config = config.pop(device_name)
            device_object = build_device(device_name, device_config)
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
    # Open I2C buses
    log.debug("Opening I2C bus streams")
    for bus in buses:
        try:
            buses[bus].open(bus)
        except IOError as err:
            log.error("Failed to open I2C bus '{bus}': {err}".format(bus=bus, err=err))

    # Scan bus for devices
    # for bus in buses:
    #    log.info("Scanning I2C bus '{bus}' for devices")
    # TODO

    # Setup devices
    for index, device in enumerate(devices):
        if device.setup():
            log.debug(
                "Successfully setup {device} '{name}'".format(
                    device=device.device, name=device.name
                )
            )
            for topic in device.get_subscriptions():
                subscribe(topic, callback=callback_device_message)
        else:
            log.warn(
                "Failed to setup {device} '{name}', it will be ignored".format(
                    device=device.device, name=device.name
                )
            )
            del devices[index]

    log.debug("Adding MQTT subscription to poll all devices topic")
    subscribe(
        config[CONF_KEY_TOPIC_GETTER],
        callback=callback_poll_all,
        subtopics=["{module_topic}"],
        substitutions={
            "module_topic": config[CONF_KEY_TOPIC],
            "module_name": TEXT_NAME,
        },
    )

    if config[CONF_KEY_POLL_INT] > 0:
        log.debug(
            "Starting polling timer with interval of {interval}s".format(
                interval=config[CONF_KEY_POLL_INT]
            )
        )
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

    log.debug("Clearing device outputs")
    for device in devices:
        device.cleanup()

    log.debug("Disconnecting from bus streams")
    for bus in buses:
        buses[bus].close()


def callback_device_message(client, userdata, message):
    """
    Callback for message on device topic
    """
    queue.put_nowait(
        {"func": "_device_message", "args": [message.topic, message.payload]}
    )


def _device_message(topic, payload):
    for device in devices:
        device.handle_message(topic, payload)


def callback_poll_all(client, userdata, message):
    """
    Callback for poll all
    """
    queue.put_nowait({"func": "poll_all"})


def poll_all():
    """
    Polls all devices
    """
    log.debug("Polling all devices")
    for device in devices:
        device.publish_state()


def poll_interval():
    """ Polls all devices and restarts the timer """
    log.debug("Polling timer fired")
    global polling_timer
    polling_timer = Timer(config[CONF_KEY_POLL_INT], poll_interval)
    polling_timer.start()
    poll_all()
