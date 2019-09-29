"""
***************************
GPIO Library Wrapper Common
***************************

:Author: Michael Murton
"""
# Copyright (c) 2019 MQTTany contributors
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

from enum import Enum

all = [ "baseGPIO", "Mode", "Logic", "Direction", "Resistor", "Interrupt" ]

class Mode(Enum):
    BOARD = 50
    SOC = 51
    WIRINGPI = 52

class Logic():
    LOW = 0
    HIGH = 1

class Direction(Enum):
    INPUT = 10
    OUTPUT = 11

class Resistor(Enum):
    OFF = 20
    PULL_UP = 21
    PULL_DOWN = 22

class Interrupt(Enum):
    NONE = 0
    RISING = 30
    FALLING = 31
    BOTH = 32

class baseGPIO():
    """
    GPIO Library Wrapper base class
    """

    def pin_valid(self, pin, direction):
        """
        Return ``True`` if pin can be used for ``direction``
        """
        raise NotImplementedError

    def setup(self, pin, direction, resistor):
        """
        Set the pin direction (input or output).
        """
        raise NotImplementedError

    def output(self, pin, value):
        """
        Set the pin state (high or low).
        """
        raise NotImplementedError

    def input(self, pin):
        """
        Read the pin state (high or low).
        """
        raise NotImplementedError

    def add_event_detect(self, pin, edge, callback, bouncetime=0):
        """
        Add a pin change interrupt with callback.
        """
        raise NotImplementedError

    def remove_event_detect(self, pin):
        """
        Remove a pin change interurpt.
        """
        raise NotImplementedError

    def cleanup(self, pin=None):
        """
        Clean up interrupts for pin or all if pin is ``None``.
        """
        raise NotImplementedError
