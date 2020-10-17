"""
*****************************
Core GPIO Raspberry Pi Boards
*****************************

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

from adafruit_platformdetect.constants.boards import (
    RASPBERRY_PI_A,
    RASPBERRY_PI_A_PLUS,
    RASPBERRY_PI_B_REV1,
    RASPBERRY_PI_B_REV2,
    RASPBERRY_PI_B_PLUS,
    RASPBERRY_PI_ZERO,
    RASPBERRY_PI_ZERO_W,
    RASPBERRY_PI_2B,
    RASPBERRY_PI_3B,
    RASPBERRY_PI_3B_PLUS,
    RASPBERRY_PI_3A_PLUS,
)

from gpio.common import Mode, PinMode, PinBias, PinAlternate
from gpio.boards.base import Board

DIGITAL = PinMode.DIGITAL
P_UP = PinBias.PULL_UP


class RPIbase(Board):
    """Raspberry Pi base"""

    def _check_w1(self):
        # detect wire1 pin (there must be a better way?)
        # defined in /boot/config.txt as
        # dtoverlay=w1-gpio >> default gpio 4
        # dtoverlay=w1-gpio,gpiopin=x
        try:
            with open("/boot/config.txt") as fd:
                lines = fd.readlines()
        except IOError:
            pass
        else:
            for line in lines:
                if "w1-gpio" in line:
                    if "gpiopin" in line:
                        pin = int(line.strip().split("gpiopin=")[1].strip())
                    else:
                        pin = 4
                    self._pin_lookup[Mode.SOC][pin].lock(None, module="system.1wire")


class RPI40p(RPIbase):
    """Raspberry Pi 40 pin base"""

    def __init_subclass__(self):
        # chip, line, soc, board, wpi, modes, biases, alts
        self._add_pin(self, 0, 0, 0, 27, 30, DIGITAL, P_UP, PinAlternate.I2C0_SDA)
        self._add_pin(self, 0, 1, 1, 28, 31, DIGITAL, P_UP, PinAlternate.I2C0_SCL)
        self._add_pin(self, 0, 2, 2, 3, 8, DIGITAL, P_UP, PinAlternate.I2C1_SDA)
        self._add_pin(self, 0, 3, 3, 5, 9, DIGITAL, P_UP, PinAlternate.I2C1_SCL)
        self._add_pin(self, 0, 4, 4, 7, 7, DIGITAL, P_UP)
        self._add_pin(self, 0, 5, 5, 29, 21, DIGITAL, P_UP)
        self._add_pin(self, 0, 6, 6, 31, 22, DIGITAL, P_UP)
        self._add_pin(self, 0, 7, 7, 26, 11, DIGITAL, P_UP)
        self._add_pin(self, 0, 8, 8, 24, 10, DIGITAL, P_UP)
        self._add_pin(self, 0, 9, 9, 21, 13, DIGITAL, P_UP)
        self._add_pin(self, 0, 10, 10, 19, 12, DIGITAL, P_UP)
        self._add_pin(self, 0, 11, 11, 23, 14, DIGITAL, P_UP)
        self._add_pin(self, 0, 12, 12, 32, 26, DIGITAL, P_UP)
        self._add_pin(self, 0, 13, 13, 33, 23, DIGITAL, P_UP)
        self._add_pin(self, 0, 14, 14, 8, 15, DIGITAL, P_UP)
        self._add_pin(self, 0, 15, 15, 10, 16, DIGITAL, P_UP)
        self._add_pin(self, 0, 16, 16, 36, 27, DIGITAL, P_UP)
        self._add_pin(self, 0, 17, 17, 11, 0, DIGITAL, P_UP)
        self._add_pin(self, 0, 18, 18, 12, 1, DIGITAL, P_UP)
        self._add_pin(self, 0, 19, 19, 35, 24, DIGITAL, P_UP)
        self._add_pin(self, 0, 20, 20, 38, 28, DIGITAL, P_UP)
        self._add_pin(self, 0, 21, 21, 40, 29, DIGITAL, P_UP)
        self._add_pin(self, 0, 22, 22, 15, 3, DIGITAL, P_UP)
        self._add_pin(self, 0, 23, 23, 16, 4, DIGITAL, P_UP)
        self._add_pin(self, 0, 24, 24, 18, 5, DIGITAL, P_UP)
        self._add_pin(self, 0, 25, 25, 22, 6, DIGITAL, P_UP)
        self._add_pin(self, 0, 26, 26, 37, 25, DIGITAL, P_UP)
        self._add_pin(self, 0, 27, 27, 13, 2, DIGITAL, P_UP)
        self._check_w1(self)


class RPI26p(RPIbase):
    """Raspberry Pi 26 pin base"""

    def __init_subclass__(self):
        # chip, line, soc, board, wpi, modes, biases, alts
        self._add_pin(self, 0, 2, 2, 3, 8, DIGITAL, P_UP, PinAlternate.I2C1_SDA)
        self._add_pin(self, 0, 3, 3, 5, 9, DIGITAL, P_UP, PinAlternate.I2C1_SCL)
        self._add_pin(self, 0, 4, 4, 7, 7, DIGITAL, P_UP)
        self._add_pin(self, 0, 7, 7, 26, 11, DIGITAL, P_UP)
        self._add_pin(self, 0, 8, 8, 24, 10, DIGITAL, P_UP)
        self._add_pin(self, 0, 9, 9, 21, 13, DIGITAL, P_UP)
        self._add_pin(self, 0, 10, 10, 19, 12, DIGITAL, P_UP)
        self._add_pin(self, 0, 11, 11, 23, 14, DIGITAL, P_UP)
        self._add_pin(self, 0, 14, 14, 8, 15, DIGITAL, P_UP)
        self._add_pin(self, 0, 15, 15, 10, 16, DIGITAL, P_UP)
        self._add_pin(self, 0, 17, 17, 11, 0, DIGITAL, P_UP)
        self._add_pin(self, 0, 18, 18, 12, 1, DIGITAL, P_UP)
        self._add_pin(self, 0, 22, 22, 15, 3, DIGITAL, P_UP)
        self._add_pin(self, 0, 23, 23, 16, 4, DIGITAL, P_UP)
        self._add_pin(self, 0, 24, 24, 18, 5, DIGITAL, P_UP)
        self._add_pin(self, 0, 25, 25, 22, 6, DIGITAL, P_UP)
        self._add_pin(self, 0, 27, 27, 13, 2, DIGITAL, P_UP)
        self._check_w1(self)


class RPIA(RPI26p):
    def __init__(self):
        self._id = RASPBERRY_PI_A


class RPIBr1(RPIbase):
    """Raspberry Pi 26 pin - Model B rev 1"""

    def __init__(self):
        self._id = RASPBERRY_PI_B_REV2

        # chip, line, soc, board, wpi, modes, biases, alts
        self._add_pin(0, 0, 0, 3, 8, DIGITAL, P_UP, PinAlternate.I2C0_SDA)
        self._add_pin(0, 1, 1, 5, 9, DIGITAL, P_UP, PinAlternate.I2C0_SCL)
        self._add_pin(0, 4, 4, 7, 7, DIGITAL, P_UP)
        self._add_pin(0, 7, 7, 26, 11, DIGITAL, P_UP)
        self._add_pin(0, 8, 8, 24, 10, DIGITAL, P_UP)
        self._add_pin(0, 9, 9, 21, 13, DIGITAL, P_UP)
        self._add_pin(0, 10, 10, 19, 12, DIGITAL, P_UP)
        self._add_pin(0, 11, 11, 23, 14, DIGITAL, P_UP)
        self._add_pin(0, 14, 14, 8, 15, DIGITAL, P_UP)
        self._add_pin(0, 15, 15, 10, 16, DIGITAL, P_UP)
        self._add_pin(0, 17, 17, 11, 0, DIGITAL, P_UP)
        self._add_pin(0, 18, 18, 12, 1, DIGITAL, P_UP)
        self._add_pin(0, 21, 21, 13, 2, DIGITAL, P_UP)
        self._add_pin(0, 22, 22, 15, 3, DIGITAL, P_UP)
        self._add_pin(0, 23, 23, 16, 4, DIGITAL, P_UP)
        self._add_pin(0, 24, 24, 18, 5, DIGITAL, P_UP)
        self._add_pin(0, 25, 25, 22, 6, DIGITAL, P_UP)
        self._check_w1()


class RPIBr2(RPI26p):
    def __init__(self):
        self._id = RASPBERRY_PI_B_REV2


class RPIAp(RPI40p):
    def __init__(self):
        self._id = RASPBERRY_PI_A_PLUS


class RPIBp(RPI40p):
    def __init__(self):
        self._id = RASPBERRY_PI_B_PLUS


class RPI0(RPI40p):
    def __init__(self):
        self._id = RASPBERRY_PI_ZERO


class RPI0W(RPI40p):
    def __init__(self):
        self._id = RASPBERRY_PI_ZERO_W


class RPI2B(RPI40p):
    def __init__(self):
        self._id = RASPBERRY_PI_2B


class RPI3B(RPI40p):
    def __init__(self):
        self._id = RASPBERRY_PI_3B


class RPI3Bp(RPI40p):
    def __init__(self):
        self._id = RASPBERRY_PI_3B_PLUS


class RPI3Ap(RPI40p):
    def __init__(self):
        self._id = RASPBERRY_PI_3A_PLUS


SUPPORTED_BOARDS = {
    RASPBERRY_PI_A: RPIA,
    RASPBERRY_PI_B_REV1: RPIBr1,
    RASPBERRY_PI_B_REV2: RPIBr2,
    RASPBERRY_PI_A_PLUS: RPIAp,
    RASPBERRY_PI_B_PLUS: RPIBp,
    RASPBERRY_PI_ZERO: RPI0,
    RASPBERRY_PI_ZERO_W: RPI0W,
    RASPBERRY_PI_2B: RPI2B,
    RASPBERRY_PI_3B: RPI3B,
    RASPBERRY_PI_3B_PLUS: RPI3Bp,
    RASPBERRY_PI_3A_PLUS: RPI3Ap,
}
