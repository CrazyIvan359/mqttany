"""
*************
GPIO Pin Base
*************

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

import logger
from common import acquire_gpio_lock, release_gpio_lock, TEXT_PIN_PREFIX

from modules.mqtt import resolve_topic, topic_matches_sub

from modules.gpio.GPIO import getGPIO
from modules.gpio.common import config
from modules.gpio.common import *

TEXT_NAME = ".".join(__name__.split(".")[-3:3]) # gives gpio.pin

log = logger.get_module_logger(module=TEXT_NAME)


class Pin(object):
    """
    GPIO Pin base class
    """

    def __init__(self, name, pin, topic, pin_config, index=None):
        self._setup = False
        self._name = name
        self._pin = pin
        self._gpio = getGPIO()
        self._topic = resolve_topic(
            topic,
            subtopics=["{module_topic}"],
            substitutions={
                "module_topic": config[CONF_KEY_TOPIC],
                "module_name": TEXT_PACKAGE_NAME,
                "pin": pin,
                "pin_name": name,
                "index": index if index is not None else ""
            }
        )

    def setup(self):
        """
        Makes sure we have a valid GPIO library and can get a lock on the pin.
        Returns ``True`` if it succeeds, ``False`` otherwise.
        Subclasses must override this method and ``super()`` it or acquire
        their own lock on the pin.
        """
        if not self._gpio:
            log.error("No GPIO library available for '{name}' on {pin_prefix}{pin:02d}".format(
                name=self._name, pin=self._pin, pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]]))
            return False

        if not acquire_gpio_lock(self._pin, self._gpio.getPinFromMode(self._pin, config[CONF_KEY_MODE]), TEXT_PACKAGE_NAME, timeout=2000, mode=config[CONF_KEY_MODE]):
            log.error("Failed to acquire a lock for '{name}' on {pin_prefix}{pin:02d}".format(
                name=self._name, pin=self._pin, pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]]))
            return False
        return True

    def cleanup(self):
        """
        Cleanup actions when stopping
        """
        self._setup = False
        if self._gpio: self._gpio.cleanup(self._pin)
        release_gpio_lock(self._pin, self._gpio.getPinFromMode(self._pin, config[CONF_KEY_MODE]), TEXT_PACKAGE_NAME, mode=config[CONF_KEY_MODE])

    def publish_state(self):
        """
        Publishes the current pin state.
        Subclasses must override this method.
        """
        raise NotImplementedError

    def handle_message(self, topic, payload):
        """
        Handles messages on ``{pin_topic}/#``.
        Base class function will call ``self.publish_state`` if any message
        arrives on ``{pin_topic}/{CONF_KEY_TOPIC_GETTER}``.
        Subclass may override this method.
        """
        if topic_matches_sub("{}/{}".format(self._topic, config[CONF_KEY_TOPIC_GETTER]), topic):
            self.publish_state()

    @property
    def name(self): return self._name

    @property
    def topic(self): return self._topic
