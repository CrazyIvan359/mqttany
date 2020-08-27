"""
***********
GPIO Module
***********

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
    import adafruit_platformdetect
except ImportError:
    raise ImportError(
        "MQTTany's GPIO module requires 'Adafruit-PlatformDetect' to be installed, "
        "please see the wiki for instructions on how to install requirements"
    )

from threading import Timer

from config import parse_config

from common import TEXT_PIN_PREFIX
from modules.mqtt import subscribe, topic_matches_sub

from modules.gpio.GPIO import getGPIO
from modules.gpio.pin import getPin, updateConfOptions
from modules.gpio.common import config
from modules.gpio.common import *

__all__ = []

TEXT_NAME = TEXT_PACKAGE_NAME

pins = []
queue = None
polling_timer = None


def init(config_data={}):
    """
    Initializes the module
    """

    def build_pin(name, pin_config, index=None):
        clazz = getPin(pin_config[CONF_KEY_DIRECTION])
        if clazz:
            if isinstance(pin_config[CONF_KEY_TOPIC], list):
                topic = pin_config[CONF_KEY_TOPIC][index]
            else:
                topic = pin_config[CONF_KEY_TOPIC]

            if isinstance(pin_config[CONF_KEY_PIN], list):
                pin = pin_config[CONF_KEY_PIN][index]
                index = index + pin_config[CONF_KEY_FIRST_INDEX]
            else:
                pin = pin_config[CONF_KEY_PIN]

            return clazz(name, pin, topic, pin_config, index)
        else:
            log.warn(
                "Direction '{dir}'  for '{name}' on {pin_prefix}{pin:02d} is not supported".format(
                    dir=pin_config[CONF_KEY_DIRECTION],
                    name=name,
                    pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]],
                    pin=pin,
                )
            )
            return None

    conf_options = updateConfOptions(CONF_OPTIONS)
    conf_options.move_to_end("regex:.+")
    raw_config = parse_config(config_data, conf_options, log)
    del config_data
    if raw_config:
        log.debug("Config loaded")
        config.update(raw_config)
        del raw_config
        used_pins = {}

        detector = adafruit_platformdetect.Detector()
        if getGPIO() is None:
            log.error("Unsupported board {board}".format(board=detector.board.id))
            return False
        log.debug("Board is {board}".format(board=detector.board.id))

        pin_valid = getGPIO().pin_valid

        for name in [key for key in config if isinstance(config[key], dict)]:
            named_config = config.pop(name)
            pin_object = None

            if isinstance(named_config[CONF_KEY_PIN], int):
                pin = named_config[CONF_KEY_PIN]
                if not pin_valid(pin, named_config[CONF_KEY_DIRECTION]):
                    log.warn(
                        "{pin_prefix}{pin:02d} in '{name}' is not a valid pin for this board, it will be ignored".format(
                            pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]],
                            pin=pin,
                            name=name,
                        )
                    )
                elif pin in used_pins:
                    log.warn(
                        "Duplicate configuration for {pin_prefix}{pin:02d} found in '{name}' will be ignored, pin already configured under '{original}'".format(
                            pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]],
                            pin=pin,
                            name=name,
                            original=pins[used_pins[pin]].name,
                        )
                    )
                else:
                    pin_object = build_pin(name, named_config)

                if pin_object:
                    used_pins[pin] = len(pins)
                    pins.append(pin_object)
                    pin_object = None

            elif isinstance(named_config[CONF_KEY_PIN], list):
                for index in range(len(named_config[CONF_KEY_PIN])):
                    pin = named_config[CONF_KEY_PIN][index]
                    if not pin_valid(pin, named_config[CONF_KEY_DIRECTION]):
                        log.warn(
                            "{pin_prefix}{pin:02d} in '{name}' is not a valid pin for this board, it will be ignored".format(
                                pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]],
                                pin=pin,
                                name=name,
                            )
                        )
                    elif pin in used_pins:
                        log.warn(
                            "Duplicate configuration for {pin_prefix}{pin:02d} found in '{name}' will be ignored, pin already configured under '{original}'".format(
                                pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]],
                                pin=pin,
                                name=name,
                                original=pins[used_pins[pin]].name,
                            )
                        )
                    else:
                        pin_object = build_pin(name, named_config, index)

                    if pin_object:
                        used_pins[pin] = len(pins)
                        pins.append(pin_object)
                        pin_object = None

        return True
    else:
        log.error("Error loading config")
        return False


def pre_loop():
    """
    Actions to be done in the subprocess before the loop starts
    """
    log.debug("Setting up hardware")

    for index, pin in enumerate(pins):
        if pin.setup():
            subscribe("{}/+/#".format(pin.topic), callback=callback_pin_message)
        else:
            del pins[index]

    log.debug("Adding MQTT subscription to poll all topic")
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

    for pin in pins:
        pin.cleanup()


def callback_pin_message(client, userdata, message):
    """
    Callback for message on pin topic
    """
    queue.put_nowait({"func": "_pin_message", "args": [message.topic, message.payload]})


def _pin_message(topic, payload):
    for pin in pins:
        if topic_matches_sub("{}/+/#".format(pin.topic), topic):
            pin.handle_message(topic, payload)


def callback_poll_all(client, userdata, message):
    """
    Callback for poll all
    """
    queue.put_nowait({"func": "poll_all"})


def poll_all():
    """
    Polls all pins
    """
    log.debug("Polling all pins")
    for pin in pins:
        pin.publish_state()


def poll_interval():
    """ Polls all pins and restarts the timer """
    log.debug("Polling timer fired")
    global polling_timer
    polling_timer = Timer(config[CONF_KEY_POLL_INT], poll_interval)
    polling_timer.start()
    poll_all()
