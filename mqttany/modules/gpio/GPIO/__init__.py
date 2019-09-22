"""
********************
GPIO Library Wrapper
********************

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

from adafruit_blinka.agnostic import detector

from logger import log_traceback

from modules.gpio.common import log

all = [ "getGPIO" ]


def getGPIO(**kwargs):
    """
    Returns a class to interface with the hardware GPIO or ``None`` if one is
    not available.
    """
    if detector.board.any_raspberry_pi:
        try:
            from modules.gpio.GPIO.rpi import RPiGPIO
        except RuntimeError:
            log.error("A RuntimeError while trying to import RPi.GPIO. This is likely because you do not have the correct permissions.")
        except:
            log.error("An error occurred while trying to import RPi.GPIO")
            log_traceback(log)
        else:
            return RPiGPIO(**kwargs)

    return None
