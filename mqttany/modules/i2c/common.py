"""
**********
I2C Common
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

__all__ = [
    "log",
    "CONFIG",
    "publish_queue",
    "nodes",
    "CONF_KEY_POLL_INT",
    "CONF_KEY_BUS_SCAN",
    "CONF_KEY_NAME",
    "CONF_KEY_DEVICE",
    "CONF_KEY_BUS",
    "CONF_KEY_ADDRESS",
    "CONF_OPTIONS",
    "validateAddress",
    "validateBus",
]

import multiprocessing as mproc
import os
import typing as t
from collections import OrderedDict

import logger
from config import resolve_type

from common import BusMessage, BusNode, BusProperty, DataType

CONF_KEY_POLL_INT = "polling interval"
CONF_KEY_BUS_SCAN = "bus scan"  # TODO not implemented yet
CONF_KEY_NAME = "name"
CONF_KEY_DEVICE = "device"
CONF_KEY_BUS = "bus"
CONF_KEY_ADDRESS = "address"

CONF_OPTIONS: t.MutableMapping[str, t.Dict[str, t.Any]] = OrderedDict(
    [
        (CONF_KEY_POLL_INT, {"type": int, "default": 60}),
        (CONF_KEY_BUS_SCAN, {"type": bool, "default": False}),
        (
            "regex:.+",
            {  # Device definition
                "type": "section",
                "required": False,
                CONF_KEY_NAME: {"type": str, "default": "{device_id}"},
                CONF_KEY_DEVICE: {"selection": []},
                CONF_KEY_BUS: {"type": (int, str), "default": 1},
                CONF_KEY_ADDRESS: {"type": int},
            },
        ),
    ]
)

log = logger.get_logger("i2c")
CONFIG: t.Dict[str, t.Any] = {}

publish_queue: "mproc.Queue[BusMessage]" = None  # type: ignore
nodes: t.Dict[str, BusNode] = {
    "i2c": BusNode(
        name="I2C",
        type="Module",
        properties={
            "poll-all": BusProperty(
                name="Poll All", settable=True, callback="poll_message"
            ),
            "polling-interval": BusProperty(
                name="Polling Interval", datatype=DataType.INT, unit="s"
            ),
        },
    )
}


def validateAddress(address: t.Any) -> t.Union[int, None]:
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


def validateBus(bus: t.Any) -> t.Union[str, None]:
    """
    Validates I2C bus ID or full path.
    Returns ``None`` if bus is invalid.
    """
    path = None
    if isinstance(bus, int):
        if os.access(f"/dev/i2c-{bus}", os.F_OK, effective_ids=True):
            path = f"/dev/i2c-{bus}"
        elif os.access(f"/dev/i2c{bus}", os.F_OK, effective_ids=True):
            path = f"/dev/i2c{bus}"
        else:
            log.error("Unknown I2C bus specifier '%s'", bus)
    elif isinstance(bus, str):
        if os.access(bus, os.F_OK, effective_ids=True):
            path = bus
        else:
            log.error("I2C bus path '%s' does not exist", bus)

    return path
