"""
**************
OneWire Device
**************

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

__all__ = [
    "getDevice",
    "updateConfOptions",
    "getDeviceTypeByFamily",
]

import typing as t

from common import update_dict

from . import ds18x20
from .base import OneWireDevice


def getDevice(address: str) -> t.Union[t.Type[OneWireDevice], None]:
    """
    Returns a class for the device based on device family code or ``None`` if
    one is not available.
    """
    family = int(address[:2], base=16)
    dev_classes: t.Dict[int, t.Type[OneWireDevice]] = {}
    dev_classes.update(ds18x20.SUPPORTED_DEVICES)
    return dev_classes.get(family, None)


def updateConfOptions(conf_options: t.MutableMapping[str, t.Any]) -> t.Dict[str, t.Any]:
    """
    Return Conf Options from all device types
    """
    conf_options = update_dict(conf_options, ds18x20.CONF_OPTIONS)
    return t.cast(t.Dict[str, t.Any], conf_options)


def getDeviceTypeByFamily(family: t.Union[int, str]) -> str:
    """
    Returns the device type based on the family code (can pass full address) or
    ``'UNKNOWN`` if unsupported.
    """
    if isinstance(family, str):
        family = int(family[:2], base=16)

    family_codes: t.Dict[int, str] = {}
    family_codes.update(ds18x20.FAMILY_CODES)
    return family_codes.get(family, "UNKNOWN")
