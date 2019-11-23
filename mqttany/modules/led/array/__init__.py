"""
****************
LED Array Module
****************

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

try:
    import adafruit_platformdetect
    import adafruit_platformdetect.board as board
    detector = adafruit_platformdetect.Detector()
    board_id = detector.board.id
except ImportError:
    raise ImportError("MQTTany's LED module requires 'Adafruit-PlatformDetect' to be installed, \
        please see the wiki for instructions on how to install requirements")

from logger import log_traceback

from modules.led.common import config
from modules.led.common import *

__all__ = [ "getArray" ]


def getArray(array_config):
    """
    Returns an LED Object or ``None`` if one is not available for the specified hardware.
    """
    led_obj = None

    if array_config[CONF_KEY_GPIO] is not None:

        if detector.board.any_raspberry_pi:
            pin_ok = False

            if array_config[CONF_KEY_GPIO] in [12, 18] and board_id in [
                                board.RASPBERRY_PI_B_PLUS,
                                board.RASPBERRY_PI_2B,
                                board.RASPBERRY_PI_3B,
                                board.RASPBERRY_PI_3B_PLUS,
                            ]:
                pin_ok = True # PWM0

            if array_config[CONF_KEY_GPIO] in [13] and board_id in [
                                board.RASPBERRY_PI_B_PLUS,
                                board.RASPBERRY_PI_2B,
                                board.RASPBERRY_PI_3B,
                                board.RASPBERRY_PI_3B_PLUS,
                                board.RASPBERRY_PI_ZERO,
                                board.RASPBERRY_PI_ZERO_W,
                            ]:
                pin_ok = True # PWM1

            if array_config[CONF_KEY_GPIO] in [21] and board_id in [
                                board.RASPBERRY_PI_B_PLUS,
                                board.RASPBERRY_PI_2B,
                                board.RASPBERRY_PI_3B,
                                board.RASPBERRY_PI_3B_PLUS,
                                board.RASPBERRY_PI_ZERO,
                                board.RASPBERRY_PI_ZERO_W,
                            ]:
                pin_ok = True # PCM_DOUT

            if array_config[CONF_KEY_GPIO] in [10]:
                pin_ok = True # SPI0-MOSI

            if not pin_ok:
                log.error("GPIO{pin:02d} cannot be used for LED control on {board}".format(
                    pin=array_config[CONF_KEY_GPIO], board=board_id))
            else:
                try:
                    from modules.led.array.rpi import rpiArray
                except:
                    log.error("An error occurred while trying to import the Raspberry Pi WS281x library")
                    log_traceback(log)
                else:
                    led_obj = rpiArray(
                        name=array_config["name"],
                        topic=array_config[CONF_KEY_TOPIC],
                        pin=array_config[CONF_KEY_GPIO],
                        led_type=array_config[CONF_KEY_TYPE],
                        count=array_config[CONF_KEY_COUNT],
                        leds_per_pixel=array_config[CONF_KEY_PER_PIXEL],
                        brightness=array_config[CONF_KEY_BRIGHTNESS],
                        color_order=array_config[CONF_KEY_COLOR_ORDER],
                        frequency=array_config[CONF_KEY_FREQUENCY],
                        invert=array_config[CONF_KEY_INVERT],
                    )

    else:
        log.error("No library is available for '{name}' configuration".format(name=array_config["name"]))

    return led_obj
