"""
**********
I2C Common
**********
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
    raise ImportError("MQTTany's I2C module requires 'mprop' to be installed, \
        please see the wiki for instructions on how to install requirements")

import os
from collections import OrderedDict

import logger
from config import resolve_type

CONF_KEY_TOPIC = "topic"
CONF_KEY_TOPIC_GETTER = "topic get"
CONF_KEY_POLL_INT = "polling interval"
CONF_KEY_BUS_SCAN = "bus scan"
CONF_KEY_DEVICE = "device"
CONF_KEY_BUS = "bus"
CONF_KEY_ADDRESS = "address"

CONF_OPTIONS = OrderedDict([ # MUST USE ORDEREDDICT WHEN REGEX KEY MAY MATCH OTHER KEYS
    (CONF_KEY_TOPIC, {"default": "{module_name}"}),
    (CONF_KEY_TOPIC_GETTER, {"default": "poll"}),
    (CONF_KEY_POLL_INT, {"type": float, "default": 0.0}),
    (CONF_KEY_BUS_SCAN, {"type": bool, "default": False}),
    ("regex:.+", { # Device definition
        "type": "section",
        "required": False,
        CONF_KEY_DEVICE: {"type": str},
        CONF_KEY_BUS: {"type": (int, str), "default": 1},
        CONF_KEY_ADDRESS: {"type": (int, list)},
        CONF_KEY_TOPIC: {"type": (str, list), "default": "{device_name}"},
    })
])

TEXT_PACKAGE_NAME = __name__.split(".")[-2] # gives i2c

log = logger.get_module_logger(module=TEXT_PACKAGE_NAME)
_config = {}

__all__ = [
    "CONF_KEY_TOPIC", "CONF_KEY_TOPIC_GETTER", "CONF_KEY_POLL_INT",
    "CONF_KEY_BUS", "CONF_KEY_BUS_SCAN", "CONF_KEY_DEVICE", "CONF_KEY_BUS",
    "CONF_KEY_ADDRESS",

    "CONF_OPTIONS",

    "TEXT_PACKAGE_NAME",

    "log", "config", "validateAddress", "validateBus"
]

@mproperty
def config(module):
    return _config


def validateAddress(address):
    """
    Validates I2C address.
    Returns ``None`` if address is invalid.
    """
    if not isinstance(address, int):
        address = resolve_type(address)
    if isinstance(address, int):
        if 15 < address < 240:
            return address
    return None


def validateBus(bus):
    """
    Validates I2C bus ID or full path.
    Returns ``None`` if bus is invalid.
    """
    if isinstance(bus, int):
        filepath = "/dev/i2c-{bus}".format(bus=bus)
    elif isinstance(bus, str):
        filepath = bus
    else:
        log.error("Unknown I2C bus specifier '{bus}'".format(bus=bus))
        return None

    if not os.path.exists(filepath):
        log.error("I2C bus path '{filepath}' does not exist".format(
            filepath=filepath))
        return None

    return filepath
