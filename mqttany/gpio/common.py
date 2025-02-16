"""
****************
Core GPIO Common
****************

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
    "cdev",
    "sysfs",
    "Mode",
    "PinMode",
    "PinBias",
    "PinEdge",
    "PinAlternate",
]

import enum

import logger

log = logger.get_logger("core.gpio")
cdev = False
cdev_bias = False
sysfs = False


class Mode(enum.Enum):
    """Pin Numbering mode"""

    SOC = enum.auto()
    BOARD = enum.auto()
    WIRINGPI = enum.auto()


class PinMode(enum.Flag):
    """Pin operating mode"""

    INPUT = enum.auto()
    OUTPUT = enum.auto()
    DIGITAL = INPUT | OUTPUT


class PinBias(enum.Flag):
    """Pin bias resistor setting"""

    NONE = 0
    PULL_UP = enum.auto()
    PULL_DOWN = enum.auto()


class PinEdge(enum.Flag):
    """Pin change trigger edge"""

    NONE = 0
    RISING = enum.auto()
    FALLING = enum.auto()
    BOTH = RISING | FALLING


class PinAlternate(enum.Flag):
    """Pin alternate functions"""

    NONE = 0
    I2C0_SDA = enum.auto()
    I2C0_SCL = enum.auto()
    I2C1_SDA = enum.auto()
    I2C1_SCL = enum.auto()
    I2C2_SDA = enum.auto()
    I2C2_SCL = enum.auto()
    I2C3_SDA = enum.auto()
    I2C3_SCL = enum.auto()
    I2C4_SDA = enum.auto()
    I2C4_SCL = enum.auto()
    I2C5_SDA = enum.auto()
    I2C5_SCL = enum.auto()
    ANY_I2C = (
        I2C0_SDA
        | I2C0_SCL
        | I2C1_SDA
        | I2C1_SCL
        | I2C2_SDA
        | I2C2_SCL
        | I2C3_SDA
        | I2C3_SCL
        | I2C4_SDA
        | I2C4_SCL
        | I2C5_SDA
        | I2C5_SCL
    )
