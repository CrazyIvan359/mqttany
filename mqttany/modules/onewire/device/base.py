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

__all__ = ["OneWireDevice"]

import typing as t

from common import BusNode, BusProperty, PublishMessage, SubscribeMessage
from logger import mqttanyLogger

from .. import common
from ..bus import OneWireBus


class OneWireDevice:
    """
    OneWire Device base class
    """

    def __init__(
        self,
        id: str,
        name: str,
        device: str,
        address: str,
        bus: OneWireBus,
        **kwargs: t.Any,
    ) -> None:
        self._setup = False
        self._id = id
        self._name = name
        self._device = device.upper()
        self._address = address
        self._bus = bus
        self._log: mqttanyLogger = None  # type: ignore - must be set by subclass

    def get_node(self) -> BusNode:
        """
        Subclasses MUST override and ``super()`` this method.
        Returns a ``BusNode`` representing the device and all its properties.
        """
        return BusNode(
            name=self.name,
            type=self.device,
            properties={"address": BusProperty(name="Address")},
        )

    def setup(self) -> bool:
        """
        Sets up the device and makes sure it is available on the bus.
        Returns ``True`` if device is available, ``False`` otherwise.
        Subclasses may override this method but should ``super()`` it.
        """
        if self.address in self._bus.scan():
            common.publish_queue.put_nowait(
                PublishMessage(
                    path=f"{self.id}/address", content=self.address, mqtt_retained=True
                )
            )
            return True
        else:
            self._log.error(
                "Device %s '%s' was not found on the bus", self.device, self.name
            )
        return False

    def cleanup(self) -> None:
        """
        Perform cleanup on module shutdown.
        Subclasses may override this method.
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
    def address(self) -> str:
        return self._address
