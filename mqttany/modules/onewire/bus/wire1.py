"""
*****************
OneWire wire1 Bus
*****************

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

import os

import logger

from modules.onewire.bus.base import OneWireBus
from modules.onewire.common import *

all = [ "OneWireBus_wire1" ]

CONF_OPTIONS = {}
CONF_BUS_SELECTION = ["w1", "W1", "wire1", "WIRE1", "Wire1"]

BUS_PATH = "/sys/bus/w1/devices"
DEVICE_RAW = "rw"
DEVICE_SLAVE = "w1_slave"

TEXT_NAME = ".".join([__name__.split(".")[-3], __name__.split(".")[-1]]) # gives onewire.wire1

log = logger.get_module_logger(module=TEXT_NAME)

class wire1(OneWireBus):
    """
    OneWire Bus wrapping the Kernel wire1 driver
    """

    def __init__(self):
        super().__init__()

    def scan(self):
        """
        Scan bus and return list of addresses found
        """
        devices = []
        if os.path.exists(BUS_PATH):
            for device in os.listdir(BUS_PATH):
                if "w1" not in device:
                    device = device.replace("-", "")
                    device = "{}{}".format(device, self.crc8(bytes.fromhex(device)).hex())
                    devices.append(device.upper())
        return devices

    def read(self, address, length):
        """
        Read ``length`` bytes from device (not including crc8).
        """
        buffer = self.read_rw(address, length) or self.read_slave(address, length)
        if buffer is None:
            log.warn("Failed to read from device at {address}".format(address=address))
        return buffer

    def read_rw(self, address, length):
        """
        Read raw bytes from ``rw`` device file.
        Returns ``length`` bytes (not including crc8), will be ``None`` if read fails.
        """
        addr = "{}-{}".format(address[:2],address[2:])[:-2].lower()
        buffer = None

        log.trace("Attempting to read from 'rw' file '{path}'".format(
            path=os.path.join(BUS_PATH, addr, DEVICE_RAW)))

        if os.path.exists(os.path.join(BUS_PATH, addr, DEVICE_RAW)):
            pass # read raw
        else:
            log.trace("Unable to read from device at address {address}, no 'rw' file".format(
                address=address))
        return buffer

    def read_slave(self, address, length):
        """
        Read raw bytes from ``w1_slave`` file.
        Returns ``length`` bytes (not including crc8), will be ``None`` if read fails.
        """
        addr = "{}-{}".format(address[:2],address[2:])[:-2].lower()
        buffer = None

        log.trace("Attempting to read from 'w1_slave' file '{path}'".format(
            path=os.path.join(BUS_PATH, addr, DEVICE_SLAVE)))

        if os.path.exists(os.path.join(BUS_PATH, addr, DEVICE_SLAVE)):
            try:
                with open(os.path.join(BUS_PATH, addr, DEVICE_SLAVE)) as fh:
                    lines = fh.readlines()
                if lines:
                    try:
                        buffer = bytes.fromhex("".join(lines[0].split(" ")[:length+1]))
                    except:
                        log.error("Failed to read {length} bytes from {address} 'w1_slave' file line 1 '{line}'".format(
                            length=length, address=address, line=lines[0]))
                    else:
                        if buffer != bytes([*buffer[:length], *self.crc8(buffer[:length])]):
                            log.error("Read invalid data from device at address {address}".format(address=address))
                            buffer = None
                        else:
                            buffer = buffer[:length]
            except Exception as err:
                log.error("Failed to read from device at address {address}, an error occurred when reading 'w1_slave' file: {error}".format(
                    address=address, error=err))
        else:
            log.trace("Unable to read from device at address {address}, no 'w1_slave' file".format(
                address=address))
        return buffer

    def write_raw(self, address, buffer):
        """
        Write raw bytes to device
        """
        addr = "{}-{}".format(address[:2],address[2:])

    @property
    def valid(self):
        """
        Returns ``True`` if the bus is available
        """
        return os.path.exists(BUS_PATH)
