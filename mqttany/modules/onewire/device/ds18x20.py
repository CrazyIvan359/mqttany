"""
**********************
OneWire DS18x20 Device
**********************

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

__all__ = ["CONF_OPTIONS", "FAMILY_CODES", "SUPPORTED_DEVICES"]

import typing as t

import logger
from common import BusNode, BusProperty, DataType, PublishMessage, SubscribeMessage

from .. import common
from ..bus.base import OneWireBus
from .base import OneWireDevice

CONF_KEY_DS18X20 = "ds18x20"
CONF_KEY_UNIT = "unit"

# will be added to device section of core CONF_OPTIONS
CONF_OPTIONS: t.Dict[str, t.Any] = {
    CONF_KEY_DS18X20: {
        "type": "section",
        CONF_KEY_UNIT: {
            "default": "C",
            "selection": ["C", "c", "F", "f"],
        },
    }
}

FAMILY_CODES: t.Dict[int, str] = {
    0x10: "DS18S20",
    0x22: "DS1822",
    0x28: "DS18B20",
    0x3B: "DS1825",
    0x42: "DS28EA00",
}


class DS18x20(OneWireDevice):
    """
    DS18x20 Temperature Sensor

    Supports DS18S20, DS1822, DS18B20, DS1825, and DS28EA00 devices.
    """

    def __init__(
        self,
        id: str,
        name: str,
        device: str,
        address: str,
        bus: OneWireBus,
        device_config: t.Dict[str, t.Any],
    ) -> None:
        super().__init__(id, name, device, address, bus)
        self._log = logger.get_logger("onewire.ds18x20")
        self._unit: str = (
            device_config.get(CONF_KEY_DS18X20, {}).get(CONF_KEY_UNIT, "C").upper()
        )
        self._log.debug(
            "Configured %s '%s' at address '%s' with options: %s",
            self.device,
            self.name,
            self.address,
            {CONF_KEY_UNIT: self._unit},
        )

    def get_node(self) -> BusNode:
        node = super().get_node()
        node.add_property(
            "temperature",
            BusProperty(
                name="Temperature", datatype=DataType.FLOAT, unit=f"°{self._unit}"
            ),
        )
        node.add_property("unit", BusProperty(name="Unit"))
        return node

    def setup(self) -> bool:
        """
        Sets up the device and makes sure it is available on the bus.
        Returns ``True`` if device is available, ``False`` otherwise.
        """
        self._setup = super().setup()
        return self._setup

    def publish_state(self) -> None:
        """
        Publishes the current device state
        """
        if self._setup:
            data = self._bus.read(self._address, 8)
            if data is None:
                self._log.error(
                    "%s: Failed to publish state, data read error", self.name
                )
            else:
                self._log.trace(
                    "%s: Read raw data 0x%s from device", self.name, data.hex()
                )

                itemp = int.from_bytes(data[:2], byteorder="little", signed=False)
                itemp >>= 4
                itemp = int.from_bytes(bytes([itemp]), "big", signed=True)
                ftemp = float(itemp)
                data = int.from_bytes(data, byteorder="little", signed=False)
                ftemp += 0.5000 * float(data & (1 << 3) > 0)
                ftemp += 0.2500 * float(data & (1 << 2) > 0)
                ftemp += 0.1250 * float(data & (1 << 1) > 0)
                ftemp += 0.0625 * float(data & (1 << 0) > 0)

                if self._unit == "F":
                    ftemp = ftemp * 9 / 5 + 32

                self._log.debug(
                    "%s: Read temperature %0.3f %s", self.name, ftemp, self._unit
                )
                common.publish_queue.put_nowait(
                    PublishMessage(path=f"{self.id}/temperature", content=ftemp)
                )
                common.publish_queue.put_nowait(
                    PublishMessage(path=f"{self.id}/unit", content=self._unit)
                )
        else:
            self._log.error(
                "%s: Failed to publish state, device is not setup", self.name
            )

    def message_callback(self, message: SubscribeMessage) -> None:
        if self._setup:
            self._log.debug(
                "%s: Received message on unregistered path: %s", self.name, message
            )


SUPPORTED_DEVICES: t.Dict[int, t.Type[OneWireDevice]] = {
    code: DS18x20 for code in FAMILY_CODES
}
