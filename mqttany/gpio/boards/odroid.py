"""
***********************
Core GPIO Odroid Boards
***********************

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

__all__ = ["SUPPORTED_BOARDS"]

import subprocess
import typing as t

from adafruit_platformdetect.constants.boards import (
    ODROID_C1,
    ODROID_C1_PLUS,
    ODROID_C2,
    ODROID_N2,
    ODROID_XU4,
)

from ..common import PinAlternate, PinBias, PinMode
from .base import Board

DIGITAL = PinMode.DIGITAL
P_UP = PinBias.PULL_UP
P_DN = PinBias.PULL_DOWN


class OdroidC1(Board):
    def __init__(self) -> None:
        super().__init__()
        self._id = ODROID_C1

        # chip, line, soc, board, wpi, modes, biases, alts
        self._add_pin(0, 74, 74, 3, 8, DIGITAL, P_UP, PinAlternate.I2C1_SDA)
        self._add_pin(0, 75, 75, 5, 9, DIGITAL, P_UP, PinAlternate.I2C1_SCL)
        self._add_pin(0, 76, 76, 27, 30, DIGITAL, P_UP, PinAlternate.I2C2_SDA)
        self._add_pin(0, 77, 77, 28, 31, DIGITAL, P_UP, PinAlternate.I2C2_SCL)
        self._add_pin(0, 83, 83, 7, 7, DIGITAL, P_UP)
        self._add_pin(0, 87, 87, 12, 1, DIGITAL, P_UP)
        self._add_pin(0, 88, 88, 11, 0, DIGITAL, P_UP)
        self._add_pin(0, 97, 97, 35, 24, DIGITAL, P_UP)
        self._add_pin(0, 98, 98, 36, 27, DIGITAL, P_UP)
        self._add_pin(0, 99, 99, 32, 26, DIGITAL, P_UP)
        self._add_pin(0, 100, 100, 31, 22, DIGITAL, P_UP)
        self._add_pin(0, 101, 101, 29, 21, DIGITAL, P_UP)
        self._add_pin(0, 102, 102, 18, 5, DIGITAL, P_UP)
        self._add_pin(0, 103, 103, 22, 6, DIGITAL, P_UP)
        self._add_pin(0, 104, 104, 16, 4, DIGITAL, P_UP)
        self._add_pin(0, 105, 105, 23, 14, DIGITAL, P_UP)
        self._add_pin(0, 106, 106, 21, 13, DIGITAL, P_UP)
        self._add_pin(0, 107, 107, 19, 12, DIGITAL, P_UP)
        self._add_pin(0, 108, 108, 33, 23, DIGITAL, P_DN)
        self._add_pin(0, 113, 113, 8, 15, DIGITAL, P_UP)
        self._add_pin(0, 114, 114, 10, 16, DIGITAL, P_UP)
        self._add_pin(0, 115, 115, 15, 3, DIGITAL, P_DN)
        self._add_pin(0, 116, 116, 13, 2, DIGITAL, P_UP)
        self._add_pin(0, 117, 117, 24, 10, DIGITAL, P_DN)


class OdroidC1p(OdroidC1):
    def __init__(self) -> None:
        super().__init__()
        self._id = ODROID_C1_PLUS

        # chip, line, soc, board, wpi, modes, biases, alts
        self._add_pin(0, 6, 6, -1, -1, DIGITAL, PinBias.NONE)
        self._add_pin(0, 8, 8, -1, -1, DIGITAL, P_UP)
        self._add_pin(0, 9, 9, -1, -1, DIGITAL, P_UP)
        self._add_pin(0, 10, 10, -1, -1, DIGITAL, P_UP)
        self._add_pin(0, 11, 11, -1, -1, DIGITAL, P_UP)


class OdroidC2(Board):
    def __init__(self) -> None:
        super().__init__()
        self._id = ODROID_C2

        # chip, line, soc, board, wpi, modes, biases, alts
        self._add_pin(0, 205, 205, 3, 8, DIGITAL, P_UP, PinAlternate.I2C1_SDA)
        self._add_pin(0, 206, 206, 5, 9, DIGITAL, P_UP, PinAlternate.I2C1_SCL)
        self._add_pin(0, 207, 207, 27, 30, DIGITAL, P_UP, PinAlternate.I2C2_SDA)
        self._add_pin(0, 208, 208, 28, 31, DIGITAL, P_UP, PinAlternate.I2C2_SCL)
        self._add_pin(0, 214, 214, 35, 24, DIGITAL, P_UP)
        self._add_pin(0, 218, 218, 36, 27, DIGITAL, P_UP)
        self._add_pin(0, 219, 219, 31, 22, DIGITAL, P_UP)
        self._add_pin(0, 224, 224, 32, 26, DIGITAL, P_UP)
        self._add_pin(0, 225, 225, 26, 11, DIGITAL, P_DN)
        self._add_pin(0, 228, 228, 29, 21, DIGITAL, P_UP)
        self._add_pin(0, 229, 229, 24, 10, DIGITAL, P_UP)
        self._add_pin(0, 230, 230, 23, 14, DIGITAL, P_UP)
        self._add_pin(0, 231, 231, 22, 6, DIGITAL, P_UP)
        self._add_pin(0, 232, 232, 21, 13, DIGITAL, P_UP)
        self._add_pin(0, 233, 233, 18, 5, DIGITAL, P_UP)
        self._add_pin(0, 234, 234, 33, 23, DIGITAL, P_DN)
        self._add_pin(0, 235, 235, 19, 12, DIGITAL, P_UP)
        self._add_pin(0, 236, 236, 16, 4, DIGITAL, P_UP)
        self._add_pin(0, 237, 237, 15, 3, DIGITAL, P_UP)
        self._add_pin(0, 238, 238, 12, 1, DIGITAL, P_DN)
        self._add_pin(0, 239, 239, 13, 2, DIGITAL, P_UP)
        self._add_pin(0, 240, 240, 8, 15, DIGITAL, P_UP)
        self._add_pin(0, 241, 241, 10, 16, DIGITAL, P_UP)
        self._add_pin(0, 247, 247, 11, 0, DIGITAL, P_UP)
        self._add_pin(0, 249, 249, 7, 7, DIGITAL, P_UP)

        self._add_pin(0, 128, 128, -1, -1, DIGITAL, P_UP)
        self._add_pin(0, 130, 130, -1, -1, DIGITAL, P_UP)
        self._add_pin(0, 131, 131, -1, -1, DIGITAL, P_UP)
        self._add_pin(0, 132, 132, -1, -1, DIGITAL, P_UP)
        self._add_pin(0, 133, 133, -1, -1, DIGITAL, P_UP)


class OdroidN2(Board):
    def __init__(self) -> None:
        super().__init__()
        self._id = ODROID_N2

        # chip, line, soc, board, wpi, modes, biases, alts
        self._add_pin(0, 464, 464, 26, 11, DIGITAL, P_UP)
        self._add_pin(0, 472, 472, 32, 26, DIGITAL, P_UP)
        self._add_pin(0, 473, 473, 7, 7, DIGITAL, P_UP)
        self._add_pin(0, 474, 474, 27, 30, DIGITAL, P_UP, PinAlternate.I2C1_SDA)
        self._add_pin(0, 475, 475, 28, 31, DIGITAL, P_UP, PinAlternate.I2C1_SCL)
        self._add_pin(0, 476, 476, 16, 4, DIGITAL, P_UP)
        self._add_pin(0, 477, 477, 18, 5, DIGITAL, P_UP)
        self._add_pin(0, 478, 478, 22, 6, DIGITAL, P_UP)
        self._add_pin(0, 479, 479, 11, 0, DIGITAL, P_UP)
        self._add_pin(0, 480, 480, 13, 2, DIGITAL, P_UP)
        self._add_pin(0, 481, 481, 33, 23, DIGITAL, P_UP)
        self._add_pin(0, 482, 482, 35, 24, DIGITAL, P_UP)
        self._add_pin(0, 483, 483, 15, 3, DIGITAL, P_UP)
        self._add_pin(0, 484, 484, 19, 12, DIGITAL, P_UP)
        self._add_pin(0, 485, 485, 21, 13, DIGITAL, P_UP)
        self._add_pin(0, 486, 486, 24, 10, DIGITAL, P_UP)
        self._add_pin(0, 487, 487, 23, 14, DIGITAL, P_UP)
        self._add_pin(0, 488, 488, 8, 15, DIGITAL, P_UP)
        self._add_pin(0, 489, 489, 10, 16, DIGITAL, P_UP)
        self._add_pin(0, 490, 490, 29, 21, DIGITAL, P_UP)
        self._add_pin(0, 491, 491, 31, 22, DIGITAL, P_UP)
        self._add_pin(0, 492, 492, 12, 1, DIGITAL, P_UP)
        self._add_pin(0, 493, 493, 3, 8, DIGITAL, P_UP, PinAlternate.I2C0_SDA)
        self._add_pin(0, 494, 494, 5, 9, DIGITAL, P_UP, PinAlternate.I2C0_SCL)
        self._add_pin(0, 495, 495, 36, 27, DIGITAL, P_UP)


class OdroidXU(Board):
    def __init__(self) -> None:
        super().__init__()
        self._id = ODROID_XU4

        # Untested attempt to check kernel version as /dev/i2c-? assignments
        # changed in kernel 4.14.37-135
        try:
            kernel = [
                int(s)
                for s in (
                    subprocess.run(["uname", "-r"], stdout=subprocess.PIPE)
                    .stdout.strip(bytes(0))
                    .decode()
                    .split("-", 1)[0]
                    .split(".")
                )
            ]
            if kernel >= [4, 14, 37]:
                I2C1_sda = PinAlternate.I2C1_SDA
                I2C1_scl = PinAlternate.I2C1_SCL
                I2C5_sda = PinAlternate.I2C5_SDA
                I2C5_scl = PinAlternate.I2C5_SCL
            else:
                I2C1_sda = PinAlternate.I2C4_SDA
                I2C1_scl = PinAlternate.I2C4_SCL
                I2C5_sda = PinAlternate.I2C1_SDA
                I2C5_scl = PinAlternate.I2C1_SCL
        except:
            I2C1_sda = PinAlternate.I2C1_SDA
            I2C1_scl = PinAlternate.I2C1_SCL
            I2C5_sda = PinAlternate.I2C5_SDA
            I2C5_scl = PinAlternate.I2C5_SCL

        # chip, line, soc, board, wpi, modes, biases, alts
        self._add_pin(0, 18, 18, 7, 7, DIGITAL, P_UP | P_DN)
        self._add_pin(0, 19, 19, 16, 4, DIGITAL, P_UP | P_DN)
        self._add_pin(0, 21, 21, 13, 2, DIGITAL, P_UP | P_DN)
        self._add_pin(0, 22, 22, 15, 3, DIGITAL, P_UP | P_DN)
        self._add_pin(0, 23, 23, 18, 5, DIGITAL, P_UP | P_DN)
        self._add_pin(0, 24, 24, 22, 6, DIGITAL, P_UP | P_DN)
        self._add_pin(0, 25, 25, 26, 11, DIGITAL, P_UP | P_DN)
        self._add_pin(0, 28, 28, 29, 21, DIGITAL, P_UP | P_DN)
        self._add_pin(0, 29, 29, 32, 26, DIGITAL, P_UP | P_DN)
        self._add_pin(0, 30, 30, 31, 22, DIGITAL, P_UP | P_DN)
        self._add_pin(0, 31, 31, 33, 23, DIGITAL, P_UP | P_DN)
        self._add_pin(0, 33, 33, 36, 27, DIGITAL, P_UP | P_DN)
        self._add_pin(0, 34, 34, -1, -1, DIGITAL, P_UP | P_DN)
        self._add_pin(0, 171, 171, 10, 16, DIGITAL, P_UP | P_DN)
        self._add_pin(0, 172, 172, 8, 15, DIGITAL, P_UP | P_DN)
        self._add_pin(0, 173, 173, 12, 1, DIGITAL, P_UP | P_DN)
        self._add_pin(0, 174, 174, 11, 0, DIGITAL, P_UP | P_DN)
        self._add_pin(0, 189, 189, 23, 14, DIGITAL, P_UP | P_DN)
        self._add_pin(0, 190, 190, 24, 10, DIGITAL, P_UP | P_DN)
        self._add_pin(0, 191, 191, 21, 13, DIGITAL, P_UP | P_DN)
        self._add_pin(0, 192, 192, 19, 12, DIGITAL, P_UP | P_DN)
        self._add_pin(0, 209, 209, 3, 8, DIGITAL, P_UP | P_DN, I2C1_sda)
        self._add_pin(0, 210, 210, 5, 9, DIGITAL, P_UP | P_DN, I2C1_scl)

        self._add_pin(0, 187, 187, 27, 30, DIGITAL, P_UP | P_DN, I2C5_sda)
        self._add_pin(0, 188, 188, 29, 31, DIGITAL, P_UP | P_DN, I2C5_scl)
        self._add_pin(0, 225, 225, -1, -1, DIGITAL, P_UP | P_DN)
        self._add_pin(0, 226, 226, -1, -1, DIGITAL, P_UP | P_DN)
        self._add_pin(0, 227, 227, -1, -1, DIGITAL, P_UP | P_DN)
        self._add_pin(0, 228, 228, -1, -1, DIGITAL, P_UP | P_DN)
        self._add_pin(0, 229, 229, -1, -1, DIGITAL, P_UP | P_DN)


SUPPORTED_BOARDS: t.Dict[str, t.Type[Board]] = {
    ODROID_C1: OdroidC1,
    ODROID_C1_PLUS: OdroidC1p,
    ODROID_C2: OdroidC2,
    ODROID_N2: OdroidN2,
    ODROID_XU4: OdroidXU,
}
