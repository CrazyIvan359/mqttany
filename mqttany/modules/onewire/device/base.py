"""
*******************
OneWire Device Base
*******************

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

from modules.onewire.bus import getBus, OneWireBus
from modules.onewire.common import config
from modules.onewire.common import *

__all__ = [ "OneWireDevice" ]


class OneWireDevice():
    """
    OneWire Device base class
    """

    def __init__(self, name, address, dev_type, bus, topic, log, index=None):
        self.log = log
        self._name = name
        self._setup = False
        self._type = dev_type
        self._bus = bus if isinstance(bus, OneWireBus) else getBus(bus)
        self._address = self._bus.validateAddress(address) if self._bus else None
        self._topic = resolve_topic(
            topic,
            subtopics=["{module_topic}"],
            substitutions={
                "module_topic": config[CONF_KEY_TOPIC],
                "module_name": TEXT_PACKAGE_NAME,
                "device_name": name,
                "device_type": dev_type,
                "address": address,
                "index": index if index is not None else ""
            }
        )

    def setup(self, *args, **kwargs):
        """
        Sets up the device and makes sure it is available on the bus.
        Returns ``True`` if device is available, ``False`` otherwise.
        """
        if not self._bus:
            self.log.error("Bus not available for '{name}'".format(
                name=self._name))
            return False

        if not self._address:
            self.log.error("Address for '{name}' is invalid".format(
                name=self._name))
            return False

        return True

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
        Subclass may override this method.
        """
        if topic_matches_sub("{}/{}".format(self._topic, config[CONF_KEY_TOPIC_GETTER]), topic):
            self.publish_state()

    @property
    def name(self): return self._name

    @property
    def address(self): return self._address

    @property
    def type(self): return self._type

    @property
    def topic(self): return self._topic
