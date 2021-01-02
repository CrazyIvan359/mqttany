"""
*********************
Dallas OneWire Common
*********************

:Author: Michael Murton
"""
# Copyright (c) 2019-2021 MQTTany contributors
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
    "CONF_KEY_BUS",
    "CONF_KEY_BUS_SCAN",
    "CONF_KEY_NAME",
    "CONF_KEY_ADDRESS",
    "CONF_KEY_FIRST_INDEX",
    "CONF_OPTIONS",
]

import multiprocessing as mproc
import typing as t
from collections import OrderedDict

import logger

from common import BusMessage, BusNode, BusProperty, DataType

log = logger.get_logger("onewire")
CONFIG: t.Dict[str, t.Any] = {}

publish_queue: "mproc.Queue[BusMessage]" = None  # type: ignore
nodes = {
    "onewire": BusNode(
        name="OneWire",
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

CONF_KEY_POLL_INT = "polling interval"
CONF_KEY_BUS = "bus interface"
CONF_KEY_BUS_SCAN = "bus scan"
CONF_KEY_NAME = "name"
CONF_KEY_ADDRESS = "address"
CONF_KEY_FIRST_INDEX = "first index"

CONF_OPTIONS: t.MutableMapping[str, t.Dict[str, t.Any]] = OrderedDict(
    [
        (CONF_KEY_BUS, {"default": "w1", "selection": []}),
        (CONF_KEY_POLL_INT, {"type": int, "default": 60}),
        (CONF_KEY_BUS_SCAN, {"type": bool, "default": False}),
        (
            "regex:.+",
            {
                "type": "section",
                "required": False,
                CONF_KEY_NAME: {"type": (str, list), "default": "{device_id}"},
                CONF_KEY_ADDRESS: {"type": (str, list)},
                CONF_KEY_FIRST_INDEX: {"type": int, "default": 0},
            },
        ),
    ]
)
