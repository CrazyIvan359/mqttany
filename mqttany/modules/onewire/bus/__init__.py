"""
***********
OneWire Bus
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

__all__ = ["getBus", "updateConfOptions", "getConfBusTypes"]

import typing as t
from collections import OrderedDict

from common import update_dict

from . import wire1
from .base import OneWireBus


def getBus(bus_type: str) -> t.Union[t.Type[OneWireBus], None]:
    """
    Returns a class for the bus based on bus type setting or ``None`` if
    one is not available.
    """
    buses: t.Dict[str, t.Type[OneWireBus]] = {}
    buses.update(wire1.SUPPORTED_BUS_TYPES)
    return buses.get(bus_type, None)


def updateConfOptions(
    conf_options: t.MutableMapping[str, t.Dict[t.Any, t.Any]]
) -> "OrderedDict[str, t.Dict[t.Any, t.Any]]":
    """
    Return Conf Options from all bus types
    """
    conf_options = update_dict(conf_options, wire1.CONF_OPTIONS)
    return t.cast("OrderedDict[str, t.Dict[t.Any, t.Any]]", conf_options)


def getConfBusTypes() -> t.List[str]:
    """
    Returns all of the bus types to add to device selection
    """
    devices: t.List[str] = []
    devices.extend(wire1.CONF_BUS_SELECTION)
    return devices


def validateAddress(address: t.Any) -> t.Union[str, None]:
    """
    Validates a OneWire device address.
    Will remove any invalid characters and compute CRC if needed.
    Returns ``None`` if address is invalid.
    """
    return OneWireBus.validateAddress(address)
