"""
********************
GPIO Library Wrapper
********************

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

try:
    import adafruit_platformdetect
    import adafruit_platformdetect.board as board
    detector = adafruit_platformdetect.Detector()
    board_id = detector.board.id
except ImportError:
    raise ImportError("MQTTany's GPIO module requires 'Adafruit-PlatformDetect' to be installed, \
        please see the wiki for instructions on how to install requirements")

from logger import log_traceback

from modules.gpio.common import log, config, CONF_KEY_MODE

__all__ = [ "getGPIO" ]

gpio_mod = None


def is_odroid_xu():
    """Return ``True`` if platform is Odroid XU"""
    return "ODROID-XU3" in detector.get_cpuinfo_field("Hardware")

def getGPIO(**kwargs):
    """
    Returns a class to interface with the hardware GPIO or ``None`` if one is
    not available.
    """
    global gpio_mod
    if not gpio_mod:
        if detector.board.any_raspberry_pi:
            try:
                from modules.gpio.GPIO.rpi import rpiGPIO
            except:
                log.error("An error occurred while trying to import the Raspberry Pi GPIO library")
                log_traceback(log)
            else:
                gpio_mod = rpiGPIO(mode=config[CONF_KEY_MODE])

        elif is_odroid_xu() or board_id in [
                            board.ODROID_C1, board.ODROID_C1_PLUS,
                            board.ODROID_C2,
                            board.ODROID_N2,
                        ]:
            if is_odroid_xu():
                log.warn("Detected board Odroid XU3 or XU4 but cannot identify which!")
                log.warn("Do not attempt to use pins from CON11 if you are using an XU3 board!")

            try:
                from modules.gpio.GPIO.odroid import odroidGPIO
            except:
                log.error("An error occurred while trying to import the Odroid GPIO library")
                log_traceback(log)
            else:
                gpio_mod = odroidGPIO(mode=config[CONF_KEY_MODE])

    return gpio_mod

def getPinFromMode(pin, mode):
    """
    Returns SOC GPIO number for ``pin`` in mode ``mode``
    """
    if not gpio_mod:
        getGPIO()

    return gpio_mod.getPinFromMode(pin, mode)
