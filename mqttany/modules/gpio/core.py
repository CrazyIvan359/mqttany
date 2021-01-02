"""
***********
GPIO Module
***********

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

__all__ = ["load", "start", "stop", "pin_message", "poll_message", "pulse_message"]

import json
import typing as t
from threading import Timer

from config import parse_config

from common import PublishMessage, SubscribeMessage, validate_id

from . import common
from .common import (
    CONF_KEY_FIRST_INDEX,
    CONF_KEY_MODE,
    CONF_KEY_NAME,
    CONF_KEY_PIN,
    CONF_KEY_PIN_MODE,
    CONF_KEY_POLL_INT,
    CONF_OPTIONS,
    CONFIG,
    log,
    nodes,
)
from .pin import getPin, updateConfOptions
from .pin.base import Pin
from .pin.digital import Digital

pins: t.Dict[int, Pin] = {}
pin_from_path: t.Dict[str, int] = {}
polling_timer = None


def load(config_raw: t.Dict[str, t.Any] = {}) -> bool:
    """
    Initializes the module
    """

    def build_pin(
        id: str, pin_config: t.Dict[str, t.Any], index: t.Optional[int] = None
    ) -> t.Union[Pin, None]:
        if not validate_id(id):
            log.warn("'%s' is not a valid ID and will be ignored", id)
            return None
        clazz = getPin(pin_config[CONF_KEY_PIN_MODE])
        if clazz:
            if index is None:
                pin = pin_config[CONF_KEY_PIN]
                name = pin_config[CONF_KEY_NAME].format(pin=pin, pin_id=id, index="")
            else:
                if isinstance(pin_config[CONF_KEY_NAME], list):
                    name = pin_config[CONF_KEY_NAME][index]
                elif "{index}" in pin_config[CONF_KEY_NAME]:
                    name = pin_config[CONF_KEY_NAME]
                else:
                    name = f"{pin_config[CONF_KEY_NAME]} {index + pin_config[CONF_KEY_FIRST_INDEX]}"
                pin = pin_config[CONF_KEY_PIN][index]
                name = name.format(
                    pin=pin, pin_id=id, index=index + pin_config[CONF_KEY_FIRST_INDEX]
                )
                id = f"{id}-{index + pin_config[CONF_KEY_FIRST_INDEX]}"

            clazz = clazz(pin, CONFIG[CONF_KEY_MODE], id, name, pin_config)
        else:
            log.error(
                "Pin mode %s in '%s' is not supported",
                pin_config[CONF_KEY_PIN_MODE].name,
                id,
            )
        return clazz

    conf_options = updateConfOptions(CONF_OPTIONS)
    conf_options.move_to_end("regex:.+")
    config_data = parse_config(config_raw, conf_options, log)
    del config_raw
    if config_data:
        log.debug("Config loaded")
        CONFIG.update(config_data)
        del config_data

        for id in [key for key in CONFIG if isinstance(CONFIG[key], dict)]:
            named_config = CONFIG.pop(id)
            pin_object = None

            if isinstance(named_config.get(CONF_KEY_PIN), int):
                pin = named_config[CONF_KEY_PIN]
                if pin in pins:
                    log.warn(
                        "Duplicate configuration for %s found in '%s' will be ignored, "
                        "pin already configured under '%s'",
                        pins[pin].pin_name,
                        id,
                        pins[pin].name,
                    )
                else:
                    pin_object = build_pin(id, named_config)

                if pin_object:
                    pins[pin] = pin_object
                    pin_object = None

            elif isinstance(named_config.get(CONF_KEY_PIN), list):
                for index in range(len(named_config[CONF_KEY_PIN])):
                    pin = named_config[CONF_KEY_PIN][index]
                    if pin in pins:
                        log.warn(
                            "Duplicate configuration for %s found in '%s' will be "
                            "ignored, pin already configured under '%s'",
                            pins[pin].pin_name,
                            id,
                            pins[pin].name,
                        )
                    else:
                        pin_object = build_pin(id, named_config, index)

                    if pin_object:
                        pins[pin] = pin_object
                        pin_object = None

        # build properties and lookup dict
        for pin in pins:
            nodes["gpio"].add_property(pins[pin].id, pins[pin].get_property())
            pin_from_path[pins[pin].id] = pin

        return True
    else:
        log.error("Error loading config")
        return False


def start() -> None:
    """
    Actions to be done in the subprocess before the loop starts
    """
    log.debug("Setting up hardware")

    for pin in [k for k in pins]:
        if not pins[pin].setup():
            del pins[pin]
            del pin_from_path[[k for k in pin_from_path if pin_from_path[k] == pin][0]]

    if CONFIG[CONF_KEY_POLL_INT] > 0:
        log.debug(
            "Starting polling timer with interval of %ds", CONFIG[CONF_KEY_POLL_INT]
        )
        global polling_timer
        polling_timer = Timer(CONFIG[CONF_KEY_POLL_INT], polling_timer_callback)
        polling_timer.start()

    common.publish_queue.put_nowait(
        PublishMessage(
            path="gpio/polling-interval",
            content=CONFIG[CONF_KEY_POLL_INT],
            mqtt_retained=True,
        )
    )
    poll_all()


def stop() -> None:
    """
    Actions to be done in the subprocess after the loop is exited
    """
    if polling_timer is not None:
        log.debug("Stopping polling timer")
        polling_timer.cancel()

    log.debug("Running pin cleanup")
    for pin in pins:
        pins[pin].cleanup()


def polling_timer_callback() -> None:
    """ Polls all pins and restarts the timer """
    log.debug("Polling timer fired")
    global polling_timer
    polling_timer = Timer(CONFIG[CONF_KEY_POLL_INT], polling_timer_callback)
    polling_timer.start()
    poll_all()


def poll_all() -> None:
    """
    Polls all pins
    """
    log.debug("Polling all pins")
    for pin in pins:
        pins[pin].publish_state()


def pin_message(message: SubscribeMessage) -> None:
    """
    Callback for message matching a pin path
    """
    path = message.path.strip("/").split("/")[1:]  # strip '/' and drop node 'gpio'
    if path[0] in pin_from_path:
        pins[pin_from_path[path[0]]].message_callback(
            "/".join(path[1:]), message.content
        )
    else:
        log.debug("Received message on unregistered path: %s", message)


def poll_message(message: SubscribeMessage) -> None:
    """
    Callback for message matching the poll all path
    """
    if message.path.strip("/") == "gpio/poll-all/set":
        poll_all()
    else:
        log.debug("Received message on unregistered path: %s", message)


# from pin.digital
def pulse_message(message: SubscribeMessage) -> None:
    """
    Callback for message matching pulse path
    """
    if message.path.strip("/") == "gpio/pulse/set":
        try:
            payload: t.Dict[str, t.Any] = json.loads(message.content)
        except ValueError:
            log.warn("Received unrecognized PULSE command: %s", message.content)
        else:
            if payload.get("pin") in pin_from_path:
                pin = pins[pin_from_path[payload["pin"]]]
                if getattr(pin, "pulse", None):
                    t.cast(Digital, pin).pulse(message.content)
                else:
                    log.warn(
                        "PULSE command not supported for pin %s (%s)",
                        pin.id,
                        pin.__class__.__name__,
                    )
            else:
                log.warn(
                    "Received PULSE command for unknown pin %s: %s",
                    payload.get("pin"),
                    message.content,
                )
    else:
        log.debug("Received message on unregistered path: %s", message)
