"""
*************************
GPIO Library Wrapper Base
*************************

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


class GPIO():
    """
    GPIO Library Wrapper base class
    """

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
