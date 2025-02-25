"""
**********
LED Shared
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
    "CONF_KEY_ANIM_DIR",
    "CONF_KEY_ANIM_STARTUP",
    "CONF_KEY_NAME",
    "CONF_KEY_OUTPUT",
    "CONF_KEY_COUNT",
    "CONF_KEY_PER_PIXEL",
    "CONF_KEY_BRIGHTNESS",
    "CONF_KEY_COLOR_ORDER",
    "CONF_KEY_ANIM_FPS",
    "CONF_OPTIONS",
    "ANIM_KEY_NAME",
    "ANIM_KEY_REPEAT",
    "ANIM_KEY_PRIORITY",
    "Color",
]

import multiprocessing as mproc
import typing as t
from collections import OrderedDict

import logger

from common import BusMessage, BusNode

CONF_KEY_ANIM_DIR = "anim dir"
CONF_KEY_ANIM_STARTUP = "anim startup"
CONF_KEY_NAME = "name"
CONF_KEY_OUTPUT = "output"
CONF_KEY_COUNT = "count"
CONF_KEY_PER_PIXEL = "leds per pixel"
CONF_KEY_BRIGHTNESS = "brightness"
CONF_KEY_COLOR_ORDER = "color order"
CONF_KEY_ANIM_FPS = "anim fps"

CONF_OPTIONS: t.MutableMapping[str, t.Dict[str, t.Any]] = OrderedDict(
    [
        (CONF_KEY_ANIM_DIR, {"type": (str, list), "default": []}),
        (CONF_KEY_ANIM_STARTUP, {"type": str, "default": "test.array"}),
        (
            "regex:.+",
            {
                "type": "section",
                "required": False,
                CONF_KEY_NAME: {"type": str, "default": "{array_id}"},
                CONF_KEY_OUTPUT: {"selection": {}},
                CONF_KEY_COUNT: {"type": int},
                CONF_KEY_PER_PIXEL: {"type": int, "default": 1},
                CONF_KEY_BRIGHTNESS: {"type": int, "default": 255},
                CONF_KEY_COLOR_ORDER: {
                    "default": "{default}",
                    "selection": [
                        "RGB",
                        "RBG",
                        "GRB",
                        "GBR",
                        "BRG",
                        "BGR",
                        "RGBW",
                        "RBGW",
                        "GRBW",
                        "GBRW",
                        "BRGW",
                        "BGRW",
                    ],
                },
                CONF_KEY_ANIM_FPS: {"type": int, "default": 60},
            },
        ),
    ]
)

ANIM_KEY_NAME = "anim"
ANIM_KEY_REPEAT = "repeat"
ANIM_KEY_PRIORITY = "priority"

log = logger.get_logger("led")
CONFIG: t.Dict[str, t.Any] = {}

publish_queue: "mproc.Queue[BusMessage]" = None  # type: ignore
nodes: t.Dict[str, BusNode] = {}


class Color(t.NamedTuple):
    r: int
    g: int
    b: int
    w: int = 0

    def asInt(self) -> int:
        """
        Returns a 24/32-bit representation of this color (``RRGGBB`` or ``WWRRGGBB``)
        """
        color = self.b
        color += self.g << 8
        color += self.r << 16
        color += self.w << 24
        return color

    @classmethod
    def fromInt(cls, color: int):
        # rtype: Color
        """
        Creates a ``Color`` instance from a 24/32-bit color (``RRGGBB`` or ``WWRRGGBB``)
        """
        return cls.__new__(
            cls,
            color >> 16 & 0xFF,
            color >> 8 & 0xFF,
            color & 0xFF,
            color >> 24 & 0xFF,
        )

    @staticmethod
    def getIntFromRGB(r: int, g: int, b: int, w: int = 0) -> int:
        """
        Converts the RGB(W) components provided into a 24/32-bit ``int`` in the format
        ``RRGGBB`` or ``WWRRGGBB``.
        """
        color = b
        color += g << 8
        color += r << 16
        color += w << 24
        return color

    @staticmethod
    def getRGBFromInt(color: int) -> t.Tuple[int, int, int, int]:
        """
        Coverts a 24/32-bit ``int`` in the format ``RRGGBB`` or ``WWRRGGBB`` into a
        tuple of its R, G, B, and W components.
        """
        return (
            color >> 16 & 0xFF,
            color >> 8 & 0xFF,
            color & 0xFF,
            color >> 24 & 0xFF,
        )
