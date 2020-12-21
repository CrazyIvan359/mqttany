"""
*****************
OneWire wire1 Bus
*****************

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

__all__ = ["CONF_OPTIONS", "CONF_BUS_SELECTION", "SUPPORTED_BUS_TYPES"]

import os
from typing import List

import logger
from modules.onewire.bus.base import OneWireBus

log = logger.get_logger("onewire.wire1")

CONF_OPTIONS = {}
CONF_BUS_SELECTION = ["w1", "W1", "wire1", "WIRE1", "Wire1"]

BUS_PATH = "/sys/bus/w1/devices"
DEVICE_RAW = "rw"
DEVICE_SLAVE = "w1_slave"


class Wire1(OneWireBus):
    """
    OneWire Bus wrapping the Kernel wire1 driver
    """

    @staticmethod
    def valid() -> bool:
        """
        Returns ``True`` if the bus is available
        """
        return os.path.exists(BUS_PATH)

    def scan(self) -> List[str]:
        """
        Scan bus and return list of addresses found
        """
        devices = []
        if os.path.exists(BUS_PATH):
            for filename in os.listdir(BUS_PATH):
                if "w1" not in filename:
                    filename = self.validateAddress(filename)
                    if filename is not None:
                        devices.append(filename)
        return devices

    def read(self, address: str, length: int) -> bytes:
        """
        Read ``length`` bytes from device (not including crc8).
        """
        buffer = self.read_rw(address, length) or self.read_slave(address, length)
        if buffer is None:
            log.warn("Failed to read from device at '%s'", address)
        return buffer

    def write(self, address: str, buffer: bytes) -> bool:
        """
        Not implemented yet
        """
        # TODO
        raise NotImplementedError

    def read_rw(self, address: str, length: int) -> bytes:
        """
        Read raw bytes from ``rw`` device file.
        Returns ``length`` bytes (not including crc8), will be ``None`` if read fails.
        """
        buffer = None
        path = os.path.join(BUS_PATH, self.get_w1_address(address), DEVICE_RAW)
        log.trace("Attempting to read from 'rw' file '%s", path)

        if os.path.exists(path):
            pass  # TODO read raw
        else:
            log.trace(
                "Unable to read from device at address '%s', no 'rw' file", address
            )
        return buffer

    def read_slave(self, address: str, length: int) -> bytes:
        """
        Read raw bytes from ``w1_slave`` file.
        Returns ``length`` bytes (not including crc8), will be ``None`` if read fails.
        """
        buffer = None
        path = os.path.join(BUS_PATH, self.get_w1_address(address), DEVICE_SLAVE)
        log.trace("Attempting to read from 'w1_slave' file '%s'", path)

        if os.path.exists(path):
            try:
                with open(path) as fh:
                    lines = fh.readlines()
                if lines:
                    try:
                        buffer = bytes.fromhex(
                            "".join(lines[0].split(" ")[: length + 1])
                        )
                    except:
                        log.error(
                            "Failed to read %d bytes from '%s' 'w1_slave' file line 1 '%s'",
                            length,
                            address,
                            lines[0],
                        )
                    else:
                        if buffer != bytes(
                            [*buffer[:length], *self.crc8(buffer[:length])]
                        ):
                            log.error(
                                "Read invalid data from device at address '%s'", address
                            )
                            buffer = None
                        else:
                            buffer = buffer[:length]
            except Exception as err:  # pylint: disable=broad-except
                log.error(
                    "Failed to read from device at address '%s', an error occurred when "
                    "reading 'w1_slave' file: %s",
                    address,
                    err,
                )
        else:
            log.trace(
                "Unable to read from device at address '%s', no 'w1_slave' file",
                address,
            )
        return buffer

    def write_raw(self, address, buffer):
        """
        Write raw bytes to device
        """
        # TODO
        # path = os.path.join(BUS_PATH, self.get_w1_address(address), DEVICE_SLAVE)
        # log.trace("Attempting to read from 'w1_slave' file '%s'", path)


SUPPORTED_BUS_TYPES = {bus_type: Wire1 for bus_type in CONF_BUS_SELECTION}
