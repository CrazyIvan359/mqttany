"""
*********************
LED sACN Array Module
*********************

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

import logger

from common import BusMessage, BusNode, BusProperty
from modules.led import common
from modules.led.common import (
    CONFIG,
    CONF_KEY_OUTPUT,
    CONF_KEY_BRIGHTNESS,
    CONF_KEY_ANIM_FPS,
)
from modules.led.array.base import baseArray

log = logger.get_module_logger("led.sacn")

CONF_KEY_SACN = "sacn"
CONF_KEY_UNIVERSE = "universe"
CONF_KEY_ADDRESS = "address"
CONF_KEY_SYNC = "sync universe"

CONF_OPTIONS = {
    "regex:.+": {
        CONF_KEY_OUTPUT: {"selection": {"sacn": "sacn", "sACN": "sacn"}},
        CONF_KEY_SACN: {
            "type": "section",
            "required": False,
            CONF_KEY_UNIVERSE: {"type": int, "default": 1},
            CONF_KEY_ADDRESS: {"type": str, "default": None},
            CONF_KEY_SYNC: {"type": int, "default": None},
        },
    }
}

sender = None
sender_started = False


class sacnArray(baseArray):
    def __init__(
        self,
        id: str,
        name: str,
        count: int,
        leds_per_pixel: int,
        color_order: str,
        fps: int,
        array_config: dict,
    ):
        """
        Returns an LED object that outputs via sACN
        """
        super().__init__(id, name, count, leds_per_pixel, color_order, fps)
        self._log = logger.get_module_logger(f"led.sacn.{self.id}")
        self._brightness = (
            255
            if array_config[CONF_KEY_BRIGHTNESS] > 255
            else 0
            if array_config[CONF_KEY_BRIGHTNESS] < 0
            else array_config[CONF_KEY_BRIGHTNESS]
        )
        self._order = self._order.format(default="RGB")
        self._address = array_config[CONF_KEY_SACN][CONF_KEY_ADDRESS]
        self._sync = array_config[CONF_KEY_SACN][CONF_KEY_SYNC]
        self._universes = []
        for universe in range(
            0, round((count * leds_per_pixel * self.colors) / 512.0 + 0.5)
        ):
            self._universes.append(
                universe + array_config[CONF_KEY_SACN][CONF_KEY_UNIVERSE]
            )
        self._dmx_data = [0] * (512 * len(self._universes))
        self._order_map = {}
        self._order_map["r"] = self._order.find("R")
        self._order_map["g"] = self._order.find("G")
        self._order_map["b"] = self._order.find("B")
        self._order_map["w"] = self._order.find("W")

        self._log.debug(
            "Configued '%s' on sACN %s with %d LEDs%s on universe%s%s",
            self._name,
            "multicast" if self._address is None else f"unicast to '{self._address}'",
            self._count,
            f" with {self._per_pixel} LEDs per pixel" if self._per_pixel > 1 else "",
            f" {self._universes[0]}"
            if len(self._universes) == 1
            else f"s {self._universes[0]}-{self._universes[-1]}",
            f" with sync on universe {self._sync}" if self._sync is not None else "",
        )

    def get_node(self) -> BusNode:
        """
        Returns a ``BusNode`` representing this array.
        """
        node = super().get_node()
        node.add_property("universe", BusProperty(name="Universe"))
        node.add_property("mode", BusProperty(name="Operating Mode"))
        if self._address is not None:
            node.add_property("address", BusProperty(name="Client Address"))
        if self._sync is not None:
            node.add_property("sync", BusProperty(name="Sync Universe"))
        return node

    def begin(self) -> bool:
        """
        Setup the LED array and hardware
        """
        self._log.info(
            "Setting up '%s' on sACN %s with %d LEDs%s on universe%s%s",
            self._name,
            "multicast" if self._address is None else f"unicast to '{self._address}'",
            self._count,
            f" with {self._per_pixel} LEDs per pixel" if self._per_pixel > 1 else "",
            f" {self._universes[0]}"
            if len(self._universes) == 1
            else f"s {self._universes[0]}-{self._universes[-1]}",
            f" with sync on universe {self._sync}" if self._sync is not None else "",
        )

        super().begin()

        global sender
        if not sender:
            try:
                import sacn as libsacn
            except ImportError:
                raise ImportError(
                    "MQTTany's LED module requires 'sacn' to be installed, "
                    "please see the wiki for instructions on how to install requirements"
                )
            else:
                sender = libsacn.sACNsender(
                    source_name="MQTTany",
                    fps=CONFIG[CONF_KEY_ANIM_FPS],
                    sync_universe=self._sync if self._sync is not None else 63999,
                )
                self._log.trace("Loaded sACNsender")

        global sender_started
        if not sender_started:
            sender_started = True
            sender.start()
            self._log.trace("Started sACNsender")

        for universe in self._universes:
            self._log.trace("Activating universe %d for '%s'", universe, self.name)
            sender.activate_output(universe)
            if self._address is None:
                sender[universe].multicast = True
            else:
                sender[universe].destination = self._address

        common.publish_queue.put_nowait(
            BusMessage(
                path=f"{self.id}/universe",
                content=f"{self._universes[0]}{f'-{self._universes[-1]}' if len(self._universes)>1 else ''}",
                mqtt_retained=True,
            )
        )
        common.publish_queue.put_nowait(
            BusMessage(
                path=f"{self.id}/mode",
                content="Unicast" if self._address else "Multicast",
                mqtt_retained=True,
            )
        )
        if self._address is not None:
            common.publish_queue.put_nowait(
                BusMessage(
                    path=f"{self.id}/address", content=self._address, mqtt_retained=True
                )
            )
        if self._sync is not None:
            common.publish_queue.put_nowait(
                BusMessage(
                    path=f"{self.id}/sync", content=self._sync, mqtt_retained=True
                )
            )

        self._setup = True
        return True

    def cleanup(self) -> None:
        """
        Cleanup actions when stopping
        """
        super().cleanup()
        for universe in self._universes:
            sender.deactivate_output(universe)
        if not sender.get_active_outputs():
            sender.stop()
            global sender_started
            sender_started = False

    def show(self) -> None:
        """
        Update the LEDs
        """
        if not self._setup:
            return

        if self._sync is not None:
            sender.manual_flush = True

        bright_factor = self._brightness / 255.0
        for universe in self._universes:
            data = self._dmx_data[
                (universe - self._universes[0])
                * 512 : (universe - self._universes[0])
                * 512
                + 512
            ]
            data = [round(pix * bright_factor) for pix in data]
            sender[universe].dmx_data = data

        if self._sync is not None:
            sender.flush(self._universes)
            sender.manual_flush = False

    def setPixelColor(self, pixel: [int, str, list], color: int) -> None:
        """Set LED to 24/32-bit color value"""
        if not self._setup:
            return
        color = int(color)
        self.setPixelColorRGB(
            pixel,
            # fmt: off
            color >> 16 & 0xFF,
            color >> 8  & 0xFF,
            color       & 0xFF,
            color >> 24 & 0xFF,
            # fmt: on
        )

    def setPixelColorRGB(
        self, pixel: [int, str, list], red: int, green: int, blue: int, white: int = 0
    ) -> None:
        """Set LED to RGB(W) values provided"""
        if not self._setup:
            return
        index = int(pixel) * self._per_pixel  # account for multiple chips per "pixel"
        for p in range(0, self._per_pixel):
            self._dmx_data[(index + p) * self.colors + self._order_map["r"]] = int(red)
            self._dmx_data[(index + p) * self.colors + self._order_map["g"]] = int(
                green
            )
            self._dmx_data[(index + p) * self.colors + self._order_map["b"]] = int(blue)
            if self.colors == 4:
                self._dmx_data[(index + p) * self.colors + self._order_map["w"]] = int(
                    white
                )

    def getPixelColor(self, pixel: int) -> int:
        """Return the 24/32-bit LED color"""
        if not self._setup:
            return None
        index = int(pixel) * self._per_pixel * self.colors
        color = 0x00
        color += self._dmx_data[index + self._order_map["r"]] << 16
        color += self._dmx_data[index + self._order_map["g"]] << 8
        color += self._dmx_data[index + self._order_map["b"]]
        if self.colors == 4:
            color += self._dmx_data[index + self._order_map["w"]] << 24
        return color

    def getPixelColorRGB(self, pixel: int):
        """Return an object with RGB(W) attributes"""
        if not self._setup:
            return None
        index = int(pixel) * self._per_pixel * self.colors
        c = lambda: None
        setattr(c, "red", self._dmx_data[index * self.colors + self._order_map["r"]])
        setattr(c, "green", self._dmx_data[index * self.colors + self._order_map["g"]])
        setattr(c, "blue", self._dmx_data[index * self.colors + self._order_map["b"]])
        setattr(c, "white", 0)
        if self.colors == 4:
            setattr(
                c, "white", self._dmx_data[index * self.colors + self._order_map["w"]]
            )
        return c

    def getBrightness(self) -> int:
        """Get LED strip brightness"""
        return self._brightness

    def setBrightness(self, brightness: int) -> None:
        """Set LED strip brightness"""
        if self._setup:
            self._brightness = (
                255 if brightness > 255 else 0 if brightness < 0 else brightness
            )


SUPPORTED_TYPES = {"sacn": sacnArray}
