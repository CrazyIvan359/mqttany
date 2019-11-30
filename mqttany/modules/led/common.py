"""
**********
LED Shared
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

try:
    from mprop import mproperty
except ImportError:
    raise ImportError("MQTTany's LED module requires 'mprop' to be installed, \
        please see the wiki for instructions on how to install requirements")

from collections import OrderedDict

import logger

CONF_KEY_TOPIC = "topic"
CONF_KEY_ANIM_DIR = "anim dir"
CONF_KEY_ANIM_STARTUP = "anim startup"
CONF_KEY_ANIM_FPS = "anim fps"
CONF_KEY_OUTPUT = "output"
CONF_KEY_COUNT = "count"
CONF_KEY_PER_PIXEL = "leds per pixel"
CONF_KEY_BRIGHTNESS = "brightness"
CONF_KEY_COLOR_ORDER = "color order"

CONF_OPTIONS = OrderedDict([ # MUST USE ORDEREDDICT WHEN REGEX KEY MAY MATCH OTHER KEYS
    (CONF_KEY_TOPIC, {"default": "{module_name}"}),
    (CONF_KEY_ANIM_DIR, {"type": (str, list), "default": []}),
    (CONF_KEY_ANIM_STARTUP, {"type": str, "default": "test.array"}),
    (CONF_KEY_ANIM_FPS, {"type": int, "default": 60}),
    ("regex:.+", {
        "type": "section",
        "required": False,
        CONF_KEY_OUTPUT: {"selection": {}},
        CONF_KEY_TOPIC: {"type": str, "default": "{array_name}"},
        CONF_KEY_COUNT: {"type": int},
        CONF_KEY_PER_PIXEL: {"type": int, "default": 1},
        CONF_KEY_BRIGHTNESS: {"type": int, "default": 255},
        CONF_KEY_COLOR_ORDER: {"default": "{default}", "selection": ["RGB", "RBG", "GRB", "GBR", "BRG", "BGR", "RGBW", "RBGW", "GRBW", "GBRW", "BRGW", "BGRW"]},
    })
])

ANIM_KEY_ARRAY = "array"
ANIM_KEY_NAME = "anim"
ANIM_KEY_REPEAT = "repeat"
ANIM_KEY_PRIORITY = "priority"

TEXT_PACKAGE_NAME = __name__.split(".")[-2] # gives led

log = logger.get_module_logger(module=TEXT_PACKAGE_NAME)
_config = {}

__all__ = [
    "CONF_KEY_TOPIC", "CONF_KEY_ANIM_DIR", "CONF_KEY_ANIM_STARTUP",
    "CONF_KEY_ANIM_FPS", "CONF_KEY_OUTPUT", "CONF_KEY_COUNT",
    "CONF_KEY_PER_PIXEL", "CONF_KEY_BRIGHTNESS", "CONF_KEY_COLOR_ORDER",

    "CONF_OPTIONS",

    "ANIM_KEY_ARRAY", "ANIM_KEY_NAME", "ANIM_KEY_REPEAT", "ANIM_KEY_PRIORITY",

    "TEXT_PACKAGE_NAME",

    "log"
]

@mproperty
def config(module):
    return _config
