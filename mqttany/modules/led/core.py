"""
**********
LED Module
**********

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

import json

from config import parse_config

from common import TEXT_PIN_PREFIX, update_dict
from modules.mqtt import subscribe, topic_matches_sub

from modules.led.array import getArray, getConfOptions
from modules.led.anim import load_animations
from modules.led.common import config
from modules.led.common import *

__all__ = [  ]

TEXT_NAME = TEXT_PACKAGE_NAME

queue = None
arrays = []
anims = {}


def init(config_data={}):
    """
    Initializes the module
    """
    CONF_OPTIONS.update(update_dict(CONF_OPTIONS, getConfOptions()))
    CONF_OPTIONS.move_to_end("regex:.+")

    raw_config = parse_config(config_data, CONF_OPTIONS, log)
    del config_data
    if raw_config:
        log.debug("Config loaded")
        config.update(raw_config)
        del raw_config

        for name in [key for key in config if isinstance(config[key], dict)]:
            array_config = config.pop(name)
            array_config["name"] = name
            array_object = getArray(array_config, log)
            if array_object:
                arrays.append(array_object)
            else:
                log.error("Failed to configure LED array '{name}'".format(name=name))

        return True
    else:
        log.error("Error loading config")
        return False


def pre_loop():
    """
    Actions to be done in the subprocess before the loop starts
    """
    global anims
    anims.update(load_animations())

    log.info("Setting up hardware")
    for array in [key for key in arrays]:
        if array.begin():
            array.anims = anims
            array.runAnimation(config[CONF_KEY_ANIM_STARTUP])
            subscribe(
                topic="{}/#".format(array.topic),
                callback=callback_anim_message
            )

    # subscribe to module topic
    subscribe(
        topic=config[CONF_KEY_TOPIC],
        callback=callback_anim_message,
        substitutions={
            "module_name": TEXT_NAME,
        }
    )


def post_loop():
    """
    Actions to be done in the subprocess after the loop is exited
    """
    log.debug("Setting all arrays to 'off'")
    for array in arrays:
        array.runAnimation("off", priority=2)
        array.cleanup()


def callback_anim_message(client, userdata, message):
    """
    Callback for animation message
    """
    queue.put_nowait({
        "func": "_anim_message",
        "args": [message.topic, message.payload.decode("utf-8")]
    })


def _anim_message(topic, payload):
    array, anim = None, None
    repeat, priority = 1, 1
    log.trace("Received message '{payload}' on topic '{topic}'".format(
        payload=payload, topic=topic))

    # message to module topic
    if not topic_matches_sub(config[CONF_KEY_TOPIC], topic):
        # check all arrays
        for array in arrays:
            # message to array topic
            if topic_matches_sub(array.topic, topic):
                break
            # message to array+anim topic
            elif topic_matches_sub(array.topic + "/+", topic):
                anim = topic.split("/")[-1]
                break
            array = None

    if array is not None or payload:
        if payload:
            try:
                payload = json.loads(payload)
            except ValueError:
                if array is None or anim is None:
                    log.error("Received malformed JSON '{payload}' on topic '{topic}'".format(
                        payload=payload, topic=topic))
                else:
                    payload = {}
            else:
                repeat = payload.pop(ANIM_KEY_REPEAT, repeat)
                priority = payload.pop(ANIM_KEY_PRIORITY, priority)
                if array is None:
                    array = payload.pop(ANIM_KEY_ARRAY, None)
                    array = [arr for arr in arrays if arr.name == array]
                    array = array[0] if array else None
                if anim is None:
                    anim = payload.pop(ANIM_KEY_NAME, None)

        if array and anim:
            if anim not in anims:
                log.warn("Unrecognized animation '{anim}' requested for array '{array}' on topic '{topic}'".format(
                    anim=anim, array=array.name, topic=topic))
            else:
                log.debug("Array '{array}' received command '{anim}' priority {priority} repeat {repeat} on topic '{topic}' with arguments {args}".format(
                    args=payload, anim=anim, array=array.name, topic=topic, priority=priority, repeat=repeat))
                array.runAnimation(
                    anim,
                    repeat=repeat,
                    priority=priority,
                    anim_args=payload or {}
                )
        elif array:
            log.warn("Unable to determine animation for array '{array}' from message '{payload}' on topic '{topic}'".format(
                array=array.name, payload=payload, topic=topic))
        elif anim:
            log.warn("Unable to determine array for animation '{anim}' from message '{payload}' on topic '{topic}'".format(
                anim=anim, payload=payload, topic=topic))
        else:
            log.warn("Unable to determine array or animation from message '{payload}' on topic '{topic}'".format(
                payload=payload, topic=topic))

    else:
        log.warn("Received unknown animation message '{payload}' on topic '{topic}'".format(
            payload=payload, topic=topic))
