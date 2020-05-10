"""
**********************
OneWire DS18x20 Device
**********************

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

import logger

from modules.mqtt import publish

from modules.onewire.device.base import OneWireDevice
from modules.onewire.common import *

__all__ = [ "DS18x20" ]

CONF_KEY_UNIT = "ds18x20 unit"

CONF_OPTIONS = { # will be added to device section of core CONF_OPTIONS
    CONF_KEY_UNIT: {"default": "C", "selection": {"C": "C", "c": "C", "F": "F", "f": "F"}},
}

TEXT_NAME = ".".join([__name__.split(".")[-3], __name__.split(".")[-1]]) # gives onewire.ds18x20

FAMILY_CODES = {
    0x10: "DS18S20",
    0x22: "DS1822",
    0x28: "DS18B20",
    0x3B: "DS1825",
    0x42: "DS28EA00"
}

log = logger.get_module_logger(module=TEXT_NAME)


class DS18x20(OneWireDevice):
    """
    DS18x20 Temperature Sensor

    Supports DS18S20, DS1822, DS18B20, DS1825, and DS28EA00 devices.
    """

    def __init__(self, name, address, dev_type, bus, topic, device_config, index=None):
        super().__init__(name, address, dev_type, bus, topic, log, index)
        self._unit = device_config.get(CONF_KEY_UNIT, "C")
        self.log.debug("Configured {type} '{name}' at address '{address}' with options: {options}".format(
            type=dev_type,
            name=name,
            address=address,
            options={
                CONF_KEY_TOPIC: self._topic,
                CONF_KEY_UNIT: self._unit,
            }
        ))

    def setup(self):
        """
        Sets up the device and makes sure it is available on the bus.
        Returns ``True`` if device is available, ``False`` otherwise.
        """
        if not super().setup(): return False

        # validate family code
        family = int.from_bytes(bytes.fromhex(self._address[:2]), "big")
        if family not in FAMILY_CODES:
            self.log.error("Family code {family:02x} for '{name}' is not supported by this class".format(
                    family=family, name=self._name))
            return False

        self._setup = True
        return True

    def publish_state(self):
        """
        Publishes the current device state
        """
        if not self._setup:
            self.log.error("{name}: Failed to publish state, device is not setup".format(
                name=self._name))
            return

        data = self._bus.read(self._address, 8)
        if data is None:
            self.log.error("{name}: Failed to publish state, data read error".format(
                name=self._name))
        else:
            self.log.trace("{name}: Read raw data '{data}' from device".format(
                name=self._name, data=data.hex()))

            temp = int.from_bytes(data[:2], byteorder="little", signed=False)
            temp = int("0b"+"{:08b}".format(temp >> 4)[-8:], base=0)
            temp = int.from_bytes(bytes([temp]), "big", signed=True)
            temp = float(temp)
            data = int.from_bytes(data, byteorder="little", signed=False)
            temp += 0.5000 * (data & (1 << 3) > 0)
            temp += 0.2500 * (data & (1 << 2) > 0)
            temp += 0.1250 * (data & (1 << 1) > 0)
            temp += 0.0625 * (data & (1 << 0) > 0)

            if self._unit == "F":
                temp = temp * 9 / 5 + 32

            self.log.debug("{name}: Read temperature {temp} {unit}".format(
                name=self._name, temp=temp, unit=self._unit))

            publish(self._topic, temp)
            publish("{}/unit".format(self._topic), self._unit)
