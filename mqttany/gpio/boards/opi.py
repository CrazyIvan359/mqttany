"""
**************************
Core GPIO Orange Pi Boards
**************************

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

__all__ = ["SUPPORTED_BOARDS"]

import typing as t

from adafruit_platformdetect.constants.boards import ORANGE_PI_ZERO

from ..common import Mode, PinAlternate, PinBias, PinMode
from .base import Board

DIGITAL = PinMode.DIGITAL
P_UP = PinBias.PULL_UP


class OPiZero(Board):
    def __init__(self) -> None:
        super().__init__()
        self._id = ORANGE_PI_ZERO

        # chip, line, soc, board, wpi, modes, biases, alts
        self._add_pin(0, 0, 0, 13, 7, DIGITAL, P_UP)
        self._add_pin(0, 1, 1, 11, 5, DIGITAL, P_UP)
        self._add_pin(0, 2, 2, 22, 13, DIGITAL, P_UP)
        self._add_pin(0, 3, 3, 15, 8, DIGITAL, P_UP)
        self._add_pin(0, 6, 6, 7, 2, DIGITAL, P_UP)
        self._add_pin(0, 7, 7, 12, 6, DIGITAL, P_UP)
        self._add_pin(0, 10, 10, 26, 16, DIGITAL, P_UP)
        self._add_pin(0, 11, 11, 5, 1, DIGITAL, P_UP, PinAlternate.I2C0_SCL)
        self._add_pin(0, 12, 12, 3, 0, DIGITAL, P_UP, PinAlternate.I2C0_SDA)
        self._add_pin(0, 13, 13, 24, 15, DIGITAL, P_UP)
        self._add_pin(0, 14, 14, 23, 14, DIGITAL, P_UP)
        self._add_pin(0, 15, 15, 19, 11, DIGITAL, P_UP)
        self._add_pin(0, 16, 16, 21, 12, DIGITAL, P_UP)
        self._add_pin(0, 18, 18, 18, 10, DIGITAL, P_UP, PinAlternate.I2C1_SCL)
        self._add_pin(0, 19, 19, 16, 9, DIGITAL, P_UP, PinAlternate.I2C1_SDA)
        self._add_pin(0, 198, 198, 8, 3, DIGITAL, P_UP)
        self._add_pin(0, 199, 199, 10, 4, DIGITAL, P_UP)

        # detect wire1 pin (there must be a better way?)
        # defined in /boot/armbianEnv.txt as
        # param_w1_pin=PAxx
        try:
            with open("/boot/armbianEnv.txt") as fd:
                lines = fd.readlines()
        except IOError:
            pass
        else:
            for line in lines:
                if "param_w1_pin" in line:
                    pin = int(line.strip().split("=")[-1][2:])
                    self._pin_lookup[Mode.SOC][pin].lock(None, module="system.1wire")


SUPPORTED_BOARDS: t.Dict[str, t.Type[Board]] = {ORANGE_PI_ZERO: OPiZero}
