"""
***********
GPIO Shared
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
    from mprop import mproperty
except ImportError:
    raise ImportError("MQTTany's GPIO module requires 'mprop' to be installed, \
        please see the wiki for instructions on how to install requirements")

from collections import OrderedDict

import logger
from common import Mode, Direction

CONF_KEY_MODE = "mode"
CONF_KEY_TOPIC = "topic"
CONF_KEY_TOPIC_SETTER = "topic set"
CONF_KEY_TOPIC_GETTER = "topic get"
CONF_KEY_PAYLOAD_ON = "payload on"
CONF_KEY_PAYLOAD_OFF = "payload off"
CONF_KEY_POLL_INT = "polling interval"
CONF_KEY_PIN = "pin"
CONF_KEY_FIRST_INDEX = "first index"
CONF_KEY_DIRECTION = "direction"
CONF_KEY_INVERT = "invert"

CONF_OPTIONS = OrderedDict([ # MUST USE ORDEREDDICT WHEN REGEX KEY MAY MATCH OTHER KEYS
    (CONF_KEY_MODE, {"default": Mode.SOC, "selection": {
        "BOARD": Mode.BOARD, "board": Mode.BOARD,
        "SOC": Mode.SOC, "soc": Mode.SOC, "BCM": Mode.SOC, "bcm": Mode.SOC,
        "WIRINGPI": Mode.WIRINGPI, "wiringpi": Mode.WIRINGPI, "WiringPi": Mode.WIRINGPI}}),
    (CONF_KEY_TOPIC, {"default": "{module_name}"}),
    (CONF_KEY_TOPIC_SETTER, {"default": "set"}),
    (CONF_KEY_TOPIC_GETTER, {"default": "poll"}),
    (CONF_KEY_PAYLOAD_ON, {"default": "ON"}),
    (CONF_KEY_PAYLOAD_OFF, {"default": "OFF"}),
    (CONF_KEY_POLL_INT, {"type": float, "default": 0.0}),
    ("regex:.+", {
        "type": "section",
        "required": False,
        CONF_KEY_PIN: {"type": (int, list)},
        CONF_KEY_TOPIC: {"type": (str, list), "default": "{pin}"},
        CONF_KEY_FIRST_INDEX: {"type": int, "default": 0},
        CONF_KEY_DIRECTION: {"default": Direction.INPUT, "selection": {}},
        CONF_KEY_INVERT: {"type": bool, "default": False},
    })
])

TEXT_PACKAGE_NAME = __name__.split(".")[-2] # gives gpio

log = logger.get_module_logger(module=TEXT_PACKAGE_NAME)
_config = {}

__all__ = [
    "CONF_KEY_MODE", "CONF_KEY_TOPIC", "CONF_KEY_TOPIC_SETTER",
    "CONF_KEY_TOPIC_GETTER", "CONF_KEY_PAYLOAD_ON", "CONF_KEY_PAYLOAD_OFF",
    "CONF_KEY_POLL_INT", "CONF_KEY_PIN", "CONF_KEY_FIRST_INDEX",
    "CONF_KEY_DIRECTION", "CONF_KEY_INVERT",

    "CONF_OPTIONS",

    "TEXT_PACKAGE_NAME",

    "log"
]

@mproperty
def config(module):
    return _config
