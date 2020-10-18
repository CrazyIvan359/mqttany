"""
********************
LED RPi Array Module
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

__all__ = ["SUPPORTED_TYPES", "CONF_OPTIONS"]

import os

import logger
import gpio
from common import DataType, BusMessage, BusNode, BusProperty
from modules.led import common
from modules.led.common import CONF_KEY_OUTPUT, CONF_KEY_BRIGHTNESS
from modules.led.array.base import baseArray

CONF_KEY_RPI = "rpi"
CONF_KEY_GPIO = "gpio"
CONF_KEY_CHIP = "chip"
CONF_KEY_FREQUENCY = "frequency"
CONF_KEY_INVERT = "invert"

CONF_OPTIONS = {
    "regex:.+": {
        CONF_KEY_OUTPUT: {"selection": {"rpi": "rpi", "RPi": "rpi"}},
        CONF_KEY_RPI: {
            "type": "section",
            "required": True,
            "conditions": [(CONF_KEY_OUTPUT, "rpi")],
            CONF_KEY_GPIO: {"type": int},
            CONF_KEY_CHIP: {
                "default": "WS2812B",
                "selection": ["WS2811", "WS2812", "WS2812B", "SK6812", "SK6812W"],
            },
            CONF_KEY_FREQUENCY: {  # in kHz
                "default": 800,
                "selection": range(400, 801),
            },
            CONF_KEY_INVERT: {"type": bool, "default": False},
        },
    }
}

LED_TYPES = {
    "WS2811": 0x0,
    "WS2812": 0x0,
    "WS2812B": 0x0,
    "SK6812": 0x0,
    "SK6812W": 0x18000000,
}
LED_COLOR_ORDERS = {
    "RGB": 0x100800,
    "RBG": 0x100008,
    "GRB": 0x081000,
    "GBR": 0x080010,
    "BRG": 0x001008,
    "BGR": 0x000810,
    "RGBW": 0x100800,
    "RBGW": 0x100008,
    "GRBW": 0x081000,
    "GBRW": 0x080010,
    "BRGW": 0x001008,
    "BGRW": 0x000810,
}
DEFAULT_COLOR_ORDER = {
    "WS2811": "RGB",
    "WS2812": "GRB",
    "WS2812B": "GRB",
    "SK6812": "GRB",
    "SK6812B": "GRBW",
}
DMA_CHANNEL = {  # DMA channel map
    10: 10,  # SPI does not use DMA
    12: 10,  # PWM0 DMA10
    13: 11,  # PWM1 DMA11
    18: 10,  # PWM0 DMA10
    21: 13,  # PCM  DMA13
}
PWM_CHANNEL = {  # PWM channel map
    10: 0,
    12: 0,  # PWM0
    13: 1,  # PWM1
    18: 0,  # PWM0
    21: 0,
}


class rpiArray(baseArray):
    def __init__(
        self,
        id: str,
        name: str,
        count: int,
        leds_per_pixel: int,
        color_order: str,
        fps: int,
        init_brightness: int,
        array_config: dict,
    ):
        """
        Returns an LED object wrapping ``rpi_ws281x.PixelStrip``
        """
        super().__init__(id, name, count, leds_per_pixel, color_order, fps)
        self._log = logger.get_logger(f"led.rpi.{self.id}")
        self._init_brightness = (
            255
            if array_config[CONF_KEY_BRIGHTNESS] > 255
            else 0
            if array_config[CONF_KEY_BRIGHTNESS] < 0
            else array_config[CONF_KEY_BRIGHTNESS]
        )
        self._pin = array_config[CONF_KEY_RPI][CONF_KEY_GPIO]
        self._chip = array_config[CONF_KEY_RPI][CONF_KEY_CHIP]
        self._frequency = array_config[CONF_KEY_RPI][CONF_KEY_FREQUENCY]
        self._invert = array_config[CONF_KEY_RPI][CONF_KEY_INVERT]
        self._order = self._order.format(default=DEFAULT_COLOR_ORDER[self._chip])
        self._log.debug(
            "Configured '%s' on GPIO%02d with %d %s LEDs %s",
            self._name,
            self._pin,
            self._count,
            self._chip,
            f"with {self._per_pixel} LEDs per pixel" if self._per_pixel > 1 else "",
        )

    def get_node(self) -> BusNode:
        """
        Returns a ``BusNode`` representing this array.
        """
        node = super().get_node()
        node.add_property("gpio", BusProperty(name="GPIO Pin", datatype=DataType.INT))
        node.add_property("chip", BusProperty(name="LED Chip"))
        node.add_property(
            "frequency",
            BusProperty(name="Frequency", datatype=DataType.INT, unit="kHz"),
        )
        node.add_property(
            "invert", BusProperty(name="Signal Invert", datatype=DataType.BOOL)
        )
        return node

    def begin(self) -> bool:
        """Setup the LED array"""
        self._log.info(
            "Setting up '%s' on GPIO%02d with %d %s LEDS %s",
            self._name,
            self._pin,
            self._count,
            self._chip,
            f"with {self._per_pixel} LEDs per pixel" if self._per_pixel > 1 else "",
        )

        try:
            import rpi_ws281x
        except ImportError:
            raise ImportError(
                "MQTTany's LED module requires 'rpi-ws281x' to be installed, "
                "please see the wiki for instructions on how to install requirements"
            )

        if self._pin != 10:
            if not os.access("/dev/mem", os.R_OK | os.W_OK, effective_ids=True):
                self._log.error(
                    "No read/write access to '/dev/mem', try running with root privileges"
                )
                return False

        if gpio.board.lock(self._pin, gpio.common.Mode.SOC):
            try:
                self._array = rpi_ws281x.PixelStrip(
                    num=self._count * self._per_pixel,
                    pin=self._pin,
                    freq_hz=self._frequency * 1000,
                    dma=DMA_CHANNEL[self._pin],
                    invert=self._invert,
                    brightness=self._init_brightness,
                    channel=PWM_CHANNEL[self._pin],
                    strip_type=LED_COLOR_ORDERS[self._order] + LED_TYPES[self._chip],
                )
                self._array.begin()
            except:
                self._log.error("An error occured while setting up '%s'", self._name)
                self._log.traceback(self._log)
                return False
            else:
                super().begin()
                common.publish_queue.put_nowait(
                    BusMessage(
                        path=f"{self.id}/gpio", content=self._pin, mqtt_retained=True
                    )
                )
                common.publish_queue.put_nowait(
                    BusMessage(
                        path=f"{self.id}/chip", content=self._chip, mqtt_retained=True
                    )
                )
                common.publish_queue.put_nowait(
                    BusMessage(
                        path=f"{self.id}/frequency",
                        content=self._frequency,
                        mqtt_retained=True,
                    )
                )
                common.publish_queue.put_nowait(
                    BusMessage(
                        path=f"{self.id}/invert",
                        content=self._invert,
                        mqtt_retained=True,
                    )
                )
                del self._init_brightness
                del self._chip
                del self._frequency
                del self._invert
                self._setup = True

        return self._setup

    def show(self) -> None:
        """Update the LED strip"""
        if not self._setup:
            return
        self._array.show()

    def setPixelColor(self, pixel: [int, str, list], color: int) -> None:
        """Set LED to 24/32-bit color value"""
        if not self._setup:
            return
        index = int(pixel) * self._per_pixel  # account for multiple chips per "pixel"
        for p in range(0, self._per_pixel):
            self._array.setPixelColor(index + p, int(color))

    def setPixelColorRGB(
        self, pixel: [int, str, list], red: int, green: int, blue: int, white: int = 0
    ) -> None:
        """Set LED to RGB(W) values provided"""
        if not self._setup:
            return
        index = int(pixel) * self._per_pixel  # account for multiple chips per "pixel"
        for p in range(0, self._per_pixel):
            self._array.setPixelColorRGB(
                index + p, int(red), int(green), int(blue), int(white)
            )

    def getPixelColor(self, pixel: int) -> int:
        """Return the 24/32-bit LED color"""
        if not self._setup:
            return None
        index = int(pixel) * self._per_pixel  # account for multiple chips per "pixel"
        return self._array.getPixelColor(index)

    def getPixelColorRGB(self, pixel: int):
        """Return an object with RGB(W) attributes"""
        if not self._setup:
            return None
        index = int(pixel) * self._per_pixel  # account for multiple chips per "pixel"
        led_color = self._array.getPixelColor(index)
        c = lambda: None
        # fmt: off
        setattr(c, "white", led_color >> 24 & 0xFF)
        setattr(c, "red",   led_color >> 16 & 0xFF)
        setattr(c, "green", led_color >> 8  & 0xFF)
        setattr(c, "blue",  led_color       & 0xFF)
        # fmt: on
        return c

    def getBrightness(self) -> int:
        """Get LED strip brightness"""
        return self._array.getBrightness()

    def setBrightness(self, brightness: int) -> None:
        """Set LED strip brightness"""
        if self._setup:
            brightness = (
                255 if brightness > 255 else 0 if brightness < 0 else brightness
            )
            if self.brightness != brightness:
                self._array.setBrightness(brightness)


def validateGPIO(
    id: str,
    name: str,
    count: int,
    leds_per_pixel: int,
    color_order: str,
    fps: int,
    init_brightness: int,
    array_config: dict,
):
    """
    Validate GPIO pin and return array instance if valid.
    """
    try:
        import adafruit_platformdetect
        import adafruit_platformdetect.constants.boards as boards
    except ImportError:
        raise ImportError(
            "MQTTany's LED module requires 'Adafruit-PlatformDetect' to be installed, "
            "please see the wiki for instructions on how to install requirements"
        )

    detector = adafruit_platformdetect.Detector()
    board_id = detector.board.id

    if detector.board.any_raspberry_pi:
        pin_ok = False

        if array_config[CONF_KEY_RPI][CONF_KEY_GPIO] in [12, 18] and board_id in [
            boards.RASPBERRY_PI_B_PLUS,
            boards.RASPBERRY_PI_2B,
            boards.RASPBERRY_PI_3B,
            boards.RASPBERRY_PI_3B_PLUS,
        ]:
            pin_ok = True  # PWM0

        elif array_config[CONF_KEY_RPI][CONF_KEY_GPIO] in [13] and board_id in [
            boards.RASPBERRY_PI_B_PLUS,
            boards.RASPBERRY_PI_2B,
            boards.RASPBERRY_PI_3B,
            boards.RASPBERRY_PI_3B_PLUS,
            boards.RASPBERRY_PI_ZERO,
            boards.RASPBERRY_PI_ZERO_W,
        ]:
            pin_ok = True  # PWM1

        elif array_config[CONF_KEY_RPI][CONF_KEY_GPIO] in [21] and board_id in [
            boards.RASPBERRY_PI_B_PLUS,
            boards.RASPBERRY_PI_2B,
            boards.RASPBERRY_PI_3B,
            boards.RASPBERRY_PI_3B_PLUS,
            boards.RASPBERRY_PI_ZERO,
            boards.RASPBERRY_PI_ZERO_W,
        ]:
            pin_ok = True  # PCM_DOUT

        elif array_config[CONF_KEY_RPI][CONF_KEY_GPIO] in [10]:
            pin_ok = True  # SPI0-MOSI

        if not pin_ok:
            logger.get_logger("led.rpi").error(
                "GPIO%02d cannot be used for LED control on %s",
                array_config[CONF_KEY_RPI][CONF_KEY_GPIO],
                board_id,
            )
            return None
        else:
            return rpiArray(
                id,
                name,
                count,
                leds_per_pixel,
                color_order,
                fps,
                init_brightness,
                array_config,
            )

    else:
        logger.get_logger("led.rpi").error(
            "This module only supports GPIO output on certain Raspberry Pi boards"
        )
        logger.get_logger("led.rpi").error(
            "Please see the documentation for supported boards"
        )


SUPPORTED_TYPES = {"rpi": validateGPIO}
