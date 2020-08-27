"""
**************
OneWire Device
**************

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

from modules.onewire.device.base import OneWireDevice
from modules.onewire.device import ds18x20

__all__ = [
    "getDevice",
    "getConfDeviceOptions",
    "getConfDeviceTypes",
    "getDeviceTypeByFamily",
]


def getDevice(address):
    """
    Returns a class for the device based on device family code or ``None`` if
    one is not available.
    """
    family = int(address[:2], base=16)

    if family in ds18x20.FAMILY_CODES:
        return ds18x20.DS18x20
    else:
        return None


def getConfDeviceOptions():
    """
    Returns all of the device options to add to CONF_OPTIONS
    """
    options = {}
    options.update(ds18x20.CONF_OPTIONS)
    return options


def getDeviceTypeByFamily(family):
    """
    Returns the device type based on the family code (can pass full address) or
    ``None`` if unsupported.
    """
    if isinstance(family, str):
        family = int(family[:2], base=16)

    if family in ds18x20.FAMILY_CODES:
        return ds18x20.FAMILY_CODES[family]
    else:
        return None
