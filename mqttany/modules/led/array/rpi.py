"""
********************
LED RPi Array Module
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

try:
    import rpi_ws281x
except ImportError:
    raise ImportError("MQTTany's LED module requires 'rpi-ws281x' to be installed, \
        please see the wiki for instructions on how to install requirements")

import os

import logger
from logger import log_traceback

from common import acquire_gpio_lock, release_gpio_lock, TEXT_PIN_PREFIX
from modules.gpio.common import Mode
from modules.led.common import config, TEXT_PACKAGE_NAME
from modules.led.array.common import baseArray

LED_TYPES = {"WS2811":0x0, "WS2812":0x0, "WS2812B":0x0, "SK6812":0x0, "SK6812W":0x18000000}
LED_COLOR_ORDERS = {"RGB":0x100800, "RBG":0x100008, "GRB":0x081000, "GBR":0x080010, "BRG":0x001008,
                    "BGR":0x000810, "RGBW":0x100800, "RBGW":0x100008, "GRBW":0x081000, "GBRW":0x080010,
                    "BRGW":0x001008, "BGRW":0x000810}
DMA_CHANNEL = { # DMA channel map
    10: 10, # SPI does not use DMA
    12: 10, # PWM0 DMA10
    13: 11, # PWM1 DMA11
    18: 10, # PWM0 DMA10
    21: 13  # PCM  DMA13
}
PWM_CHANNEL = { # PWM channel map
    10: 0,
    12: 0, # PWM0
    13: 1, # PWM1
    18: 0, # PWM0
    21: 0
}

TEXT_NAME = ".".join([__name__.split(".")[-3], __name__.split(".")[-1]]) # gives led.rpi

log = logger.get_module_logger(module=TEXT_NAME)

__all__ = [ "rpiArray" ]


class rpiArray(baseArray):

    def __init__(self, name, topic, pin, led_type, count, leds_per_pixel, brightness, color_order, frequency, invert):
        """
        Returns an LED object wrapping ``rpi_ws281x.PixelStrip``
        """
        super().__init__(name, topic, led_type, count, leds_per_pixel, brightness, color_order, frequency, invert)
        self._pin = pin
        log.debug("Configured '{name}' on GPIO{pin:02d} with {count} {type} LEDs {leds_per_pixel}".format(
            name=self._name, pin=self._pin, count=self._count, type=self._type,
            leds_per_pixel="{}".format("with {num} LEDs per pixel".format(num=self._per_pixel) if self._per_pixel > 1 else "")))

    def begin(self):
        """Setup the LED array"""
        log.info("Setting up '{name}' on GPIO{pin:02d} with {count} {type} LEDS {leds_per_pixel}".format(
            name=self._name, pin=self._pin, count=self._count, type=self._type,
            leds_per_pixel="{}".format("with {num} LEDs per pixel".format(num=self._per_pixel) if self._per_pixel > 1 else "")))

        if not acquire_gpio_lock(self._pin, self._pin, TEXT_PACKAGE_NAME, timeout=2000):
            log.error("Failed to acquire a lock for '{name}' on {pin_prefix}{pin:02d}".format(
                name=self._name, pin=self._pin, pin_prefix=TEXT_PIN_PREFIX[Mode.SOC]))
            return False

        if self._pin != 10:
            if not os.access("/dev/mem", os.R_OK | os.W_OK):
                log.error("No read/write access to '/dev/mem', try running with root privileges")
                return False

        try:
            self._array = rpi_ws281x.PixelStrip(
                num=self._count * self._per_pixel,
                pin=self._pin,
                freq_hz=self._frequency * 1000,
                dma=DMA_CHANNEL[self._pin],
                invert=self._invert,
                brightness=255 if self._init_brightness > 255 else 0 if self._init_brightness < 0 else self._init_brightness,
                channel=PWM_CHANNEL[self._pin],
                strip_type=LED_COLOR_ORDERS[self._order] + LED_TYPES[self._type],
            )
            self._array.begin()
        except:
            log.error("An error occured while setting up '{name}'".format(name=self._name))
            log_traceback(log)
            return False
        else:
            super().begin()
            del self._init_brightness
            del self._order
            del self._frequency
            del self._invert
            self._setup = True
            return True

    def cleanup(self):
        """Cleanup actions when stopping"""
        super().cleanup()
        release_gpio_lock(self._pin, self._pin, TEXT_PACKAGE_NAME)

    def show(self):
        """Update the LED strip"""
        if not self._setup: return
        self._array.show()

    def setPixelColor(self, pixel, color):
        """Set LED to 24/32-bit color value"""
        if not self._setup: return
        index = int(pixel) * self._per_pixel # account for multiple chips per "pixel"
        for p in range(0, self._per_pixel):
            self._array.setPixelColor(index + p, int(color))

    def setPixelColorRGB(self, pixel, red, green, blue, white=0):
        """Set LED to RGB(W) values provided"""
        if not self._setup: return
        index = int(pixel) * self._per_pixel # account for multiple chips per "pixel"
        for p in range(0, self._per_pixel):
            self._array.setPixelColorRGB(index + p, int(red), int(green), int(blue), int(white))

    def getPixelColor(self, pixel):
        """Return the 24/32-bit LED color"""
        if not self._setup: return None
        index = int(pixel) * self._per_pixel # account for multiple chips per "pixel"
        return self._array.getPixelColor(index)

    def getPixelColorRGB(self, pixel):
        """Return an object with RGB(W) attributes"""
        if not self._setup: return None
        index = int(pixel) * self._per_pixel # account for multiple chips per "pixel"
        led_color = self._array.getPixelColor(index)
        c = lambda: None
        setattr(c, "white", led_color >> 24 & 0xff)
        setattr(c, "red",   led_color >> 16 & 0xff)
        setattr(c, "green", led_color >> 8  & 0xff)
        setattr(c, "blue",  led_color       & 0xff)
        return c

    def getBrightness(self):
        """Get LED strip brightness"""
        return self._array.getBrightness()

    def setBrightness(self, value):
        """Set LED strip brightness"""
        if not self._setup: return
        value = int(value)
        self._array.setBrightness(255 if value > 255 else 0 if value < 0 else value)
