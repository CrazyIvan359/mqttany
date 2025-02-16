"""
**********
LED Module
**********

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

__all__ = ["load", "start", "stop", "anim_message"]

import threading
import typing as t

from config import parse_config

from common import SubscribeMessage, validate_id

from .anim import load_animations
from .array import getArray, updateConfOptions
from .array.base import baseArray
from .common import (
    ANIM_KEY_NAME,
    ANIM_KEY_PRIORITY,
    CONF_KEY_ANIM_STARTUP,
    CONF_OPTIONS,
    CONFIG,
    log,
    nodes,
)

arrays: t.Dict[str, baseArray] = {}


def load(config_raw: t.Dict[str, t.Any] = {}) -> bool:
    """
    Initializes the module
    """
    conf_options = updateConfOptions(CONF_OPTIONS)
    conf_options.move_to_end("regex:.+")

    config_data = parse_config(config_raw, conf_options, log)
    del config_raw
    if config_data:
        log.debug("Config loaded")
        CONFIG.update(config_data)
        del config_data

        for id in [key for key in CONFIG if isinstance(CONFIG[key], dict)]:
            array_config = CONFIG.pop(id)
            if not validate_id(id):
                log.warn("'%s' is not a valid ID and will be ignored", id)
            else:
                array_object = getArray(id, array_config, log)
                if array_object:
                    arrays[id] = array_object
                    nodes[id] = array_object.get_node()
                else:
                    log.error("Failed to configure LED array '%s'", id)

        return True
    else:
        log.error("Error loading config")
        return False


def start() -> None:
    """
    Actions to be done in the subprocess before the loop starts
    """
    anims: t.Dict[str, t.Callable[[baseArray, threading.Event], None]] = {}
    anims.update(load_animations())

    log.info("Setting up hardware")
    for id in arrays:
        if arrays[id].begin():
            arrays[id].anims = anims
            arrays[id].run_animation({ANIM_KEY_NAME: CONFIG[CONF_KEY_ANIM_STARTUP]})


def stop() -> None:
    """
    Actions to be done in the subprocess after the loop is exited
    """
    log.debug("Setting all arrays to 'off'")
    for id in arrays:
        arrays[id].run_animation({ANIM_KEY_NAME: "off", ANIM_KEY_PRIORITY: 2})
        arrays[id].cleanup()


def anim_message(message: SubscribeMessage) -> None:
    """
    Animation message callback
    """
    path = message.path.strip("/").split("/")
    if path[0] in arrays:
        arrays[path[0]].message_callback(message)
    else:
        log.debug("Received message on unregistered path: %s", message)
