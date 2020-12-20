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

import typing as t

import logger
from common import BusNode, BusProperty, PublishMessage

from .. import common
from ..common import CONF_KEY_OUTPUT, Color
from .base import baseArray

CONF_KEY_SACN = "sacn"
CONF_KEY_UNIVERSE = "universe"
CONF_KEY_ADDRESS = "address"
CONF_KEY_SYNC = "sync universe"

CONF_OPTIONS: t.MutableMapping[str, t.Dict[str, t.Any]] = {
    "regex:.+": {
        CONF_KEY_OUTPUT: {"selection": {"sacn": "sacn", "sACN": "sacn"}},
        CONF_KEY_SACN: {
            "type": "section",
            "conditions": [(CONF_KEY_OUTPUT, "sacn")],
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
        init_brightness: int,
        array_config: t.Dict[str, t.Any],
    ) -> None:
        """
        Returns an LED object that outputs via sACN
        """
        super().__init__(id, name, count, leds_per_pixel, color_order, fps)
        self._log = logger.get_logger(f"led.sacn.{self.id}")
        self._brightness = (
            255
            if init_brightness > 255
            else 0
            if init_brightness < 0
            else init_brightness
        )
        self._order: str = self._order.format(default="RGB")
        self._address: str = array_config[CONF_KEY_SACN][CONF_KEY_ADDRESS]
        self._sync: int = array_config[CONF_KEY_SACN][CONF_KEY_SYNC]
        self._universes: t.List[int] = []
        for universe in range(
            0, round((count * leds_per_pixel * self.colors) / 512.0 + 0.5)
        ):
            self._universes.append(
                universe + array_config[CONF_KEY_SACN][CONF_KEY_UNIVERSE]
            )
        self._dmx_data = [0] * (512 * len(self._universes))
        self._order_map: t.Dict[str, int] = {}
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
            except ModuleNotFoundError:
                self._log.error(
                    "MQTTany's LED module requires 'sacn' to be installed, "
                    "please see the wiki for instructions on how to install requirements"
                )
                return False
            else:
                sender = libsacn.sACNsender(
                    source_name="MQTTany",
                    fps=self._fps,
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
            PublishMessage(
                path=f"{self.id}/universe",
                content=f"{self._universes[0]}{f'-{self._universes[-1]}' if len(self._universes)>1 else ''}",
                mqtt_retained=True,
            )
        )
        common.publish_queue.put_nowait(
            PublishMessage(
                path=f"{self.id}/mode",
                content="Unicast" if self._address else "Multicast",
                mqtt_retained=True,
            )
        )
        if self._address is not None:
            common.publish_queue.put_nowait(
                PublishMessage(
                    path=f"{self.id}/address", content=self._address, mqtt_retained=True
                )
            )
        if self._sync is not None:
            common.publish_queue.put_nowait(
                PublishMessage(
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
        if sender:
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
        if not self._setup or not sender:
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

    def _setPixel(self, pixel: int, color: int) -> None:
        """Set LED to 24/32-bit color value"""
        index = pixel * self.colors
        self._dmx_data[index + self._order_map["r"]] = color >> 16 & 0xFF
        self._dmx_data[index + self._order_map["g"]] = color >> 8 & 0xFF
        self._dmx_data[index + self._order_map["b"]] = color & 0xFF
        if self.colors == 4:
            self._dmx_data[index + self._order_map["w"]] = color >> 24 & 0xFF

    def _getPixel(self, pixel: int) -> int:
        """
        Return the 24/32-bit LED color (``RRGGBB`` or ``WWRRGGBB``)
        """
        index = pixel * self.colors
        return Color.getIntFromRGB(
            self._dmx_data[index + self._order_map["r"]],
            self._dmx_data[index + self._order_map["g"]],
            self._dmx_data[index + self._order_map["b"]],
            self._dmx_data[index + self._order_map["w"]] if self.colors == 4 else 0,
        )

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
