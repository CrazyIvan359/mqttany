"""
***********
GPIO Common
***********

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
    "nodes",
    "CONF_KEY_MODE",
    "CONF_KEY_POLL_INT",
    "CONF_KEY_PIN",
    "CONF_KEY_NAME",
    "CONF_KEY_FIRST_INDEX",
    "CONF_KEY_PIN_MODE",
    "CONF_OPTIONS",
]

import multiprocessing as mproc
import typing as t
from collections import OrderedDict

import logger

from common import BusMessage, BusNode, BusProperty, DataType
from gpio import Mode

CONF_KEY_MODE = "mode"
CONF_KEY_POLL_INT = "polling interval"
CONF_KEY_PIN = "pin"
CONF_KEY_NAME = "name"
CONF_KEY_FIRST_INDEX = "first index"
CONF_KEY_PIN_MODE = "pin mode"

CONF_OPTIONS: t.MutableMapping[str, t.Dict[str, t.Any]] = OrderedDict(
    [
        (
            CONF_KEY_MODE,
            {
                "default": Mode.SOC,
                "selection": {
                    "BOARD": Mode.BOARD,
                    "board": Mode.BOARD,
                    "SOC": Mode.SOC,
                    "soc": Mode.SOC,
                    "BCM": Mode.SOC,
                    "bcm": Mode.SOC,
                    "WIRINGPI": Mode.WIRINGPI,
                    "wiringpi": Mode.WIRINGPI,
                    "WiringPi": Mode.WIRINGPI,
                },
            },
        ),
        (CONF_KEY_POLL_INT, {"type": int, "default": 60}),
        (
            "regex:.+",
            {
                "type": "section",
                "required": False,
                CONF_KEY_PIN: {"type": (int, list)},
                CONF_KEY_NAME: {"type": (str, list), "default": "{pin_id}"},
                CONF_KEY_FIRST_INDEX: {"type": int, "default": 0},
                CONF_KEY_PIN_MODE: {"selection": {}},
            },
        ),
    ]
)

log = logger.get_logger("gpio")
CONFIG: t.Dict[str, t.Any] = {}

publish_queue: "mproc.Queue[BusMessage]" = None  # type: ignore
nodes: t.Dict[str, BusNode] = {
    "gpio": BusNode(
        name="GPIO",
        type="Module",
        properties={
            "poll-all": BusProperty(
                name="Poll All Pins", settable=True, callback="poll_message"
            ),
            "polling-interval": BusProperty(
                name="Polling Interval", datatype=DataType.FLOAT, unit="s"
            ),
            # from pin.digital
            "pulse": BusProperty(name="Pulse", settable=True, callback="pulse_message"),
        },
    )
}
