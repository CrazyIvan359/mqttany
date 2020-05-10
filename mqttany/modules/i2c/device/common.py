"""
*****************
I2C Device Common
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

from modules.mqtt import resolve_topic, topic_matches_sub
from modules.i2c.common import config
from modules.i2c.common import *

__all__ = [ "I2CDevice" ]


class I2CDevice():
    """
    I2C Device base class
    """

    def __init__(self, name, address, device, bus_path, bus, topic, log):
        self.log = log
        self._name = name
        self._setup = False
        self._device = device
        self._bus_path = bus_path
        self._bus = bus
        self._address = validateAddress(address)
        self._topic = topic
        #self._topic = resolve_topic(
        #    topic,
        #    subtopics=["{module_topic}"],
        #    substitutions={
        #        "module_topic": config[CONF_KEY_TOPIC],
        #        "module_name": TEXT_PACKAGE_NAME,
        #        "device_name": name,
        #        "address": "0x{:02x}".format(address),
        #        "index": index if index is not None else ""
        #    }
        #)

    def setup(self, *args, **kwargs):
        """
        Sets up the device and makes sure it is available on the bus.
        Returns ``True`` if device is available, ``False`` otherwise.
        Subclasses may override this method but should ``super()`` it.
        """
        if self._bus.fd is None:
            self.log.error("Bus '{bus_path}' not initialized for '{name}'".format(
                bus_path=self._bus_path, name=self._name))
            return False

        if self._address is None:
            self.log.error("Address for {device} '{name}' is invalid".format(
                device=self._device, name=self._name))
            return False

        # TODO check device is on the line
        try:
            self._bus.write_quick(self.address)
        except IOError:
            log.error("No ack from {device} '{name}' at address 0x{address:02x} on I2C bus '{bus}'".format(
                device=self._device, name=self.name, address=self.address, bus=self._bus_path))
            return False

        return True

    def cleanup(self):
        """
        Perform cleanup on module shutdown.
        Subclasses may override this method
        """
        pass

    def publish_state(self):
        """
        Publishes the current device state.
        Subclasses must override this method.
        """
        raise NotImplementedError

    def handle_message(self, topic, payload):
        """
        Handles messages on ``{device_topic}/#``.
        Base class function will call ``self.publish_state`` if any message
        arrives on ``{device_topic}/{CONF_KEY_TOPIC_GETTER}``.
        Subclasses may override this method.
        """
        if topic_matches_sub("{}/{}".format(self._topic, config[CONF_KEY_TOPIC_GETTER]), topic):
            self.publish_state()

    def get_subscriptions(self):
        """
        Returns a list of fully resolved topics to subscribe to.
        Subclasses may override this method but must super() it.
        """
        return [resolve_topic(
            self._topic,
            subtopics=["{module_topic}"],
            substitutions={
                "module_topic": config[CONF_KEY_TOPIC],
                "module_name": TEXT_PACKAGE_NAME,
                "device_name": self._name,
                "address": "0x{:02x}".format(self._address),
            }
        ) + "/" + config[CONF_KEY_TOPIC_GETTER]]

    def _read_byte(self, register):
        """
        Read byte from I2C device.
        Returns ``int`` or ``None`` if read fails.
        """
        if not self._setup: return None
        try:
            data = self._bus.read_byte_data(self.address, register)
        except IOError as err:
            self.log.error("I2C error on bus '{bus}': {err}".format(
                bus=self._bus_path, err=err))
            self.log.warn("Failed to read from {device} '{device_name}' at address 0x{address:02x} on I2C bus '{bus}'".format(
                device=self.device, device_name=self.name, address=self.address, bus=self._bus_path))
            return None
        else:
            self.log.trace("Read byte 0x{data:02x} from register 0x{register:02x} on {device} '{device_name}' at address 0x{address:02x} on I2C bus '{bus}'".format(
                data=data, register=register, device=self.device, device_name=self.name,
                address=self.address, bus=self._bus_path))
            return data


    def _write_byte(self, register, data):
        """
        Write byte to I2C device.
        Returns ``True`` if success, ``False`` otherwise.
        """
        if not self._setup: return False
        try:
            self._bus.write_byte_data(self.address, register, data)
        except IOError as err:
            self.log.error("I2C error on bus '{bus}': {err}".format(
                bus=self._bus_path, err=err))
            self.log.warn("Failed to write to {device} '{device_name}' at address 0x{address:02x} on I2C bus '{bus}'".format(
                device=self.device, device_name=self.name, address=self.address, bus=self._bus_path))
            return False
        else:
            self.log.trace("Wrote byte 0x{data:02x} to register 0x{register:02x} on {device} '{device_name}' at address 0x{address:02x} on I2C bus '{bus}'".format(
                data=data, register=register, device=self.device, device_name=self.name,
                address=self.address, bus=self._bus_path))
            return True

    def _read_word(self, register):
        """
        Read 16-bit word from I2C device.
        Returns ``int`` or ``None`` if read fails.
        """
        if not self._setup: return None
        try:
            data = self._bus.read_word_data(self.address, register)
        except IOError as err:
            self.log.error("I2C error on bus '{bus}': {err}".format(
                bus=self._bus_path, err=err))
            self.log.warn("Failed to read from {device} '{device_name}' at address 0x{address:02x} on I2C bus '{bus}'".format(
                device=self.device, device_name=self.name, address=self.address, bus=self._bus_path))
            return None
        else:
            self.log.trace("Read word 0x{data:04x} from register 0x{register:02x} on {device} '{device_name}' at address 0x{address:02x} on I2C bus '{bus}'".format(
                data=data, register=register, device=self.device, device_name=self.name,
                address=self.address, bus=self._bus_path))
            return data

    def _write_word(self, register, data):
        """
        Write 16-bit word to I2C device.
        Returns ``True`` if success, ``False`` otherwise.
        """
        if not self._setup: return False
        try:
            self._bus.write_word_data(self.address, register, data)
        except IOError as err:
            self.log.error("I2C error on bus '{bus}': {err}".format(
                bus=self._bus_path, err=err))
            self.log.warn("Failed to write to {device} '{device_name}' at address 0x{address:02x} on I2C bus '{bus}'".format(
                device=self.device, device_name=self.name, address=self.address, bus=self._bus_path))
            return False
        else:
            self.log.trace("Wrote word 0x{data:04x} to register 0x{register:02x} on {device} '{device_name}' at address 0x{address:02x} on I2C bus '{bus}'".format(
                data=data, register=register, device=self.device, device_name=self.name,
                address=self.address, bus=self._bus_path))
            return True

    def _read_block(self, register, length):
        """
        Read up to 32 bytes from I2C device.
        Returns list of ``bytes`` or ``None`` if read fails.
        """
        if not self._setup: return None
        try:
            data = self._bus.read_i2c_block_data(self.address, register, length)
        except IOError as err:
            self.log.error("I2C error on bus '{bus}': {err}".format(
                bus=self._bus_path, err=err))
            self.log.warn("Failed to read from {device} '{device_name}' at address 0x{address:02x} on I2C bus '{bus}'".format(
                device=self.device, device_name=self.name, address=self.address, bus=self._bus_path))
            return None
        else:
            self.log.trace("Read {bytes} bytes {data} from register 0x{register:02x} on {device} '{device_name}' at address 0x{address:02x} on I2C bus '{bus}'".format(
                bytes=len(data), data=data, register=register,
                device=self.device, device_name=self.name,
                address=self.address, bus=self._bus_path))
            return data

    def _write_block(self, register, data):
        """
        Write list of up to 32 bytes to I2C device.
        Returns ``True`` if success, ``False`` otherwise.
        """
        if not self._setup: return False
        try:
            self._bus.write_i2c_block_data(self.address, register, data)
        except IOError as err:
            self.log.error("I2C error on bus '{bus}': {err}".format(
                bus=self._bus_path, err=err))
            self.log.warn("Failed to write to {device} '{device_name}' at address 0x{address:02x} on I2C bus '{bus}'".format(
                device=self.device, device_name=self.name, address=self.address, bus=self._bus_path))
            return False
        else:
            self.log.trace("Wrote {bytes} bytes {data} to register 0x{register:02x} on {device} '{device_name}' at address 0x{address:02x} on I2C bus '{bus}'".format(
                bytes=len(data), data=data, register=register,
                device=self.device, device_name=self.name,
                address=self.address, bus=self._bus_path))
            return True

    @property
    def name(self): return self._name

    @property
    def device(self): return self._device

    @property
    def address(self): return self._address

    @property
    def topic(self): return self._topic
