"""
*****************
I2C Device Common
*****************
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

__all__ = ["I2CDevice"]

import typing as t

from common import BusNode, BusProperty, PublishMessage, SubscribeMessage
from logger import mqttanyLogger

from .. import common


class I2CDevice:
    """
    I2C Device base class
    """

    def __init__(
        self,
        id: str,
        name: str,
        device: str,
        address: int,
        bus: object,
        bus_path: str,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> None:
        from smbus2.smbus2 import SMBus

        self._setup = False
        self._id = id
        self._name = name
        self._device = device.upper()
        self._address = address
        self._bus: SMBus = t.cast(SMBus, bus)
        self._bus_path = bus_path
        self._log: mqttanyLogger = None  # type: ignore - must be set by subclass

    def get_node(self) -> BusNode:
        """
        Subclasses MUST override and ``super()`` this method.
        Returns a ``BusNode`` representing the device and all its properties.
        """
        return BusNode(
            name=self._name,
            type=self._device,
            properties={"address": BusProperty(name="Address")},
        )

    def setup(self) -> bool:
        """
        Sets up the device and makes sure it is available on the bus.
        Returns ``True`` if device is available, ``False`` otherwise.
        Subclasses may override this method but should ``super()`` it.
        """
        if self._bus.fd is None:
            self._log.error(
                "Bus '%s' not initialized for %s '%s'",
                self._bus_path,
                self._device,
                self._name,
            )
        else:
            # check device is on the line
            try:
                self._bus.write_quick(self.address)
                common.publish_queue.put_nowait(
                    PublishMessage(
                        path=f"{self._id}/address",
                        content=f"0x{self._address:02x}",
                        mqtt_retained=True,
                    )
                )
                return True
            except IOError:
                self._log.error(
                    "No ack from %s '%s' at address 0x%02x on I2C bus '%s'",
                    self._device,
                    self._name,
                    self._address,
                    self._bus_path,
                )
        return False

    def cleanup(self) -> None:
        """
        Perform cleanup on module shutdown.
        Subclasses may override this method
        """

    def publish_state(self) -> None:
        """
        Subclasses MUST override this method.
        Publishes the current device state.
        """
        raise NotImplementedError

    def message_callback(self, message: SubscribeMessage) -> None:
        """
        Subclasses MUST override this method.
        Handles messages received for this device.
        """
        raise NotImplementedError

    def _read_byte(self, register: int, silent: bool = False) -> t.Union[int, None]:
        """
        Read byte from I2C device.
        Returns ``int`` or ``None`` if read fails.
        """
        if self._setup:
            try:
                data = self._bus.read_byte_data(self._address, register)
            except IOError as err:
                self._log.error("I2C error on bus '%s': %s", self._bus_path, err)
                self._log.warn(
                    "Failed to read from %s '%s' at address 0x%02x on I2C bus '%s'",
                    self._device,
                    self._name,
                    self._address,
                    self._bus_path,
                )
            else:
                if not silent:
                    self._log.trace(
                        "Read byte 0x%02x from register 0x%02x on %s '%s' at address "
                        "0x%02x on I2C bus '%s'",
                        data,
                        register,
                        self._device,
                        self._name,
                        self._address,
                        self._bus_path,
                    )
                return data
        return None

    def _write_byte(self, register: int, data: int, silent: bool = False) -> bool:
        """
        Write byte to I2C device.
        Returns ``True`` if success, ``False`` otherwise.
        """
        if self._setup:
            try:
                self._bus.write_byte_data(self._address, register, data)
            except IOError as err:
                self._log.error("I2C error on bus '%s': %s", self._bus_path, err)
                self._log.warn(
                    "Failed to write to %s '%s' at address 0x%02x on I2C bus '%s'",
                    self._device,
                    self._name,
                    self._address,
                    self._bus_path,
                )
            else:
                if not silent:
                    self._log.trace(
                        "Wrote byte 0x%02x to register 0x%02x on %s '%s' at address "
                        "0x%02x on I2C bus '%s'",
                        data,
                        register,
                        self._device,
                        self._name,
                        self._address,
                        self._bus_path,
                    )
                return True
        return False

    def _read_word(self, register: int, silent: bool = False) -> t.Union[int, None]:
        """
        Read 16-bit word from I2C device.
        Returns ``int`` or ``None`` if read fails.
        """
        if self._setup:
            try:
                data = self._bus.read_word_data(self._address, register)
            except IOError as err:
                self._log.error("I2C error on bus '%s': %s", self._bus_path, err)
                self._log.warn(
                    "Failed to read from %s '%s' at address 0x%02x on I2C bus '%s'",
                    self._device,
                    self._name,
                    self._address,
                    self._bus_path,
                )
            else:
                if not silent:
                    self._log.trace(
                        "Read word 0x%04x from register 0x%02x on %s '%s' at address "
                        "0x%02x on I2C bus '%s'",
                        data,
                        register,
                        self._device,
                        self._name,
                        self._address,
                        self._bus_path,
                    )
                return data
        return None

    def _write_word(self, register: int, data: int, silent: bool = False) -> bool:
        """
        Write 16-bit word to I2C device.
        Returns ``True`` if success, ``False`` otherwise.
        """
        if self._setup:
            try:
                self._bus.write_word_data(self._address, register, data)
            except IOError as err:
                self._log.error("I2C error on bus '%s': %s", self._bus_path, err)
                self._log.warn(
                    "Failed to write to %s '%s' at address 0x%02x on I2C bus '%s'",
                    self._device,
                    self._name,
                    self._address,
                    self._bus_path,
                )
            else:
                if not silent:
                    self._log.trace(
                        "Wrote word 0x%04x to register 0x%02x on %s '%s' at address "
                        "0x%02x on I2C bus '%s'",
                        data,
                        register,
                        self._device,
                        self._name,
                        self._address,
                        self._bus_path,
                    )
                return True
        return False

    def _read_block(
        self, register: int, length: int, silent: bool = False
    ) -> t.Union[t.Sequence[int], None]:
        """
        Read up to 32 bytes from I2C device.
        Returns list of ``bytes`` or ``None`` if read fails.
        """
        if self._setup:
            try:
                data = self._bus.read_i2c_block_data(self._address, register, length)
            except IOError as err:
                self._log.error("I2C error on bus '%s': %s", self._bus_path, err)
                self._log.warn(
                    "Failed to read from %s '%s' at address 0x%02x on I2C bus '%s'",
                    self._device,
                    self._name,
                    self._address,
                    self._bus_path,
                )
            else:
                if not silent:
                    self._log.trace(
                        "Read %d bytes %s from register 0x%02x on %s '%s' at address "
                        "0x%02x on I2C bus '%s'",
                        len(data),
                        data,
                        register,
                        self._device,
                        self._name,
                        self._address,
                        self._bus_path,
                    )
                return data
        return None

    def _write_block(
        self, register: int, data: t.Sequence[int], silent: bool = False
    ) -> bool:
        """
        Write list of up to 32 bytes to I2C device.
        Returns ``True`` if success, ``False`` otherwise.
        """
        if self._setup:
            try:
                self._bus.write_i2c_block_data(self._address, register, data)
            except IOError as err:
                self._log.error("I2C error on bus '%s': %s", self._bus_path, err)
                self._log.warn(
                    "Failed to write to %s '%s' at address 0x%02x on I2C bus '%s'",
                    self._device,
                    self._name,
                    self._address,
                    self._bus_path,
                )
            else:
                if not silent:
                    self._log.trace(
                        "Wrote %d bytes %s to register 0x%02x on %s '%s' at address 0x%02x "
                        "on I2C bus '%s'",
                        len(data),
                        data,
                        register,
                        self._device,
                        self._name,
                        self._address,
                        self._bus_path,
                    )
                return True
        return False

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def device(self) -> str:
        return self._device

    @property
    def address(self) -> int:
        return self._address
