"""
*************
GPIO Pin Base
*************

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

__all__ = ["Pin"]

from common import BusProperty, lock_gpio

from modules.gpio.lib import getGPIO
from modules.gpio.common import (
    CONFIG,
    CONF_KEY_MODE,
    CONF_KEY_DIRECTION,
    TEXT_GPIO_MODE,
)


class Pin(object):
    """
    GPIO Pin base class
    """

    def __init__(self, pin: int, id: str, name: str, pin_config: dict = {}):
        self._setup = False
        self._log = None  # assigned by subclass
        self._pin = pin
        self._id = id
        self._name = name
        self._path = f"gpio/{id}"
        self._direction = pin_config[CONF_KEY_DIRECTION]
        self._gpio = getGPIO()

    def get_property(self) -> BusProperty:
        """
        Subclasses MUST override this method.
        It should return a ``BusProperty`` object descibing the pin.
        """
        raise NotImplementedError

    def setup(self):
        """
        Subclasses MUST override AND ``super()`` this method. This method will try to
        get the pin lock and return the result, which you MUST use to determine if the
        pin can be used. After getting the lock, pin setup can be done.
        """
        locked = lock_gpio(
            self._gpio.getPinFromMode(self._pin, CONFIG[CONF_KEY_MODE]), "gpio.pin"
        )
        if not locked:
            self._log.error(
                "Failed to acquire a lock for '%s' on %s",
                self._name,
                TEXT_GPIO_MODE[CONFIG[CONF_KEY_MODE]].format(pin=self._pin),
            )
        return locked

    def cleanup(self):
        """
        Cleanup actions when stopping
        """
        self._setup = False
        if self._gpio:
            self._gpio.cleanup(self._pin)

    def publish_state(self):
        """
        Subclasses MUST override this method.
        Reads and publishes the current pin state.
        """
        raise NotImplementedError

    def message_callback(self, path: str, content: str):
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
