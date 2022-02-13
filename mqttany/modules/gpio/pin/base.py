"""
*************
GPIO Pin Base
*************

:Author: Michael Murton
"""
# Copyright (c) 2019-2022 MQTTany contributors
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

__all__ = ["Pin"]

import typing as t

from common import BusProperty
from gpio.common import Mode, PinMode
from gpio.pins.base import Pin as CorePin
from logger import mqttanyLogger
from ..common import CONF_KEY_PIN_MODE


class Pin(object):
    """
    GPIO Pin base class
    """

    def __init__(
        self,
        pin: int,
        gpio_mode: Mode,
        id: str,
        name: str,
        pin_config: t.Dict[str, t.Any] = {},
    ):
        self._setup = False
        self._log: mqttanyLogger = None  # type: ignore - assigned by subclass
        self._handle: t.Union[
            CorePin, None
        ] = None  # hardware access, assigned by subclass
        self._pin = pin
        self._gpio_mode = gpio_mode
        self._id = id
        self._name = name
        self._path = f"gpio/{id}"
        self._mode: PinMode = pin_config[CONF_KEY_PIN_MODE]

    def get_property(self) -> BusProperty:
        """
        Subclasses MUST override this method.
        It should return a ``BusProperty`` object descibing the pin.
        """
        raise NotImplementedError

    def setup(self) -> bool:
        """
        Subclasses MUST override this method.
        A pin handle should be acquired from ``gpio.board.get_pin``.
        """
        raise NotImplementedError

    def cleanup(self) -> None:
        """
        Cleanup actions when stopping
        """
        self._setup = False
        if self._handle:
            self._handle.cleanup()

    def publish_state(self) -> None:
        """
        Subclasses MUST override this method.
        Reads and publishes the current pin state.
        """
        raise NotImplementedError

    def message_callback(self, path: str, content: str) -> None:
        """
        Subclasses MUST override this method.
        Handles messages received for this pin.
        """
        raise NotImplementedError

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def path(self) -> str:
        return self._path

    @property
    def pin_name(self) -> str:
        return self._handle.get_name(self._gpio_mode)  # type: ignore
