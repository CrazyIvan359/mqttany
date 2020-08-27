"""
*********************
Dallas OneWire Shared
*********************

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
    raise ImportError(
        "MQTTany's OneWire module requires 'mprop' to be installed, "
        "please see the wiki for instructions on how to install requirements"
    )

import logger

CONF_KEY_TOPIC = "topic"
CONF_KEY_TOPIC_GETTER = "topic get"
CONF_KEY_POLL_INT = "polling interval"
CONF_KEY_BUS = "bus interface"
CONF_KEY_BUS_SCAN = "bus scan"
CONF_KEY_ADDRESS = "address"
CONF_KEY_FIRST_INDEX = "first index"

TEXT_PACKAGE_NAME = __name__.split(".")[-2]  # gives onewire

log = logger.get_module_logger(module=TEXT_PACKAGE_NAME)
_config = {}

__all__ = [
    "CONF_KEY_TOPIC",
    "CONF_KEY_TOPIC_GETTER",
    "CONF_KEY_POLL_INT",
    "CONF_KEY_BUS",
    "CONF_KEY_BUS_SCAN",
    "CONF_KEY_ADDRESS",
    "CONF_KEY_FIRST_INDEX",
    "TEXT_PACKAGE_NAME",
    "log",
    "config",
]


@mproperty
def config(module):
    return _config
