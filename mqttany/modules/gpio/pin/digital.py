"""
****************
GPIO Digital Pin
****************

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
from logger import log_traceback
from common import release_gpio_lock, TEXT_PIN_PREFIX, TEXT_LOGIC_STATE

from modules.mqtt import publish, topic_matches_sub

from modules.gpio.pin.base import Pin
from modules.gpio.common import config
from modules.gpio.common import *
from modules.gpio.GPIO.common import Direction, Resistor, Interrupt

CONF_KEY_DEBOUNCE = "debounce"
CONF_KEY_INTERRUPT = "interrupt"
CONF_KEY_RESISTOR = "resistor"
CONF_KEY_INITIAL = "initial state"

CONF_OPTIONS = {
    CONF_KEY_DEBOUNCE: {"type": int, "default": 50},
    "regex:.+": {
        CONF_KEY_DIRECTION: {"selection": {"input": Direction.INPUT, "in": Direction.INPUT, "output": Direction.OUTPUT, "out": Direction.OUTPUT}},
        CONF_KEY_INTERRUPT: {"default": Interrupt.NONE, "selection": {"rising": Interrupt.RISING, "falling": Interrupt.FALLING, "both": Interrupt.BOTH, "none": Interrupt.NONE}},
        CONF_KEY_RESISTOR: {"default": Resistor.OFF, "selection": {"pullup": Resistor.PULL_UP, "up": Resistor.PULL_UP, "pulldown": Resistor.PULL_DOWN, "down": Resistor.PULL_DOWN, "off": Resistor.OFF, "none": Resistor.OFF}},
        CONF_KEY_INITIAL: {"default": "{payload_off}"},
    }
}
SUPPORTED_DIRECTIONS = [Direction.INPUT, Direction.OUTPUT]

TEXT_NAME = ".".join([__name__.split(".")[-3], __name__.split(".")[-1]]) # gives gpio.digital

log = logger.get_module_logger(module=TEXT_NAME)


class DigitalPin(Pin):
    """
    GPIO Digital Pin class
    """

    def __init__(self, name, pin, topic, pin_config, index=None):
        super().__init__(name, pin, topic, index)
        self._direction = pin_config[CONF_KEY_DIRECTION]
        self._interrupt = pin_config[CONF_KEY_INTERRUPT]
        self._resistor = pin_config[CONF_KEY_RESISTOR]
        self._invert = pin_config[CONF_KEY_INVERT]
        self._initial = pin_config[CONF_KEY_INITIAL].format(
            payload_on=config[CONF_KEY_PAYLOAD_ON],
            payload_off=config[CONF_KEY_PAYLOAD_OFF]
        )
        log.debug("Configured '{name}' on {pin_prefix}{pin:02d} with options: {options}".format(
            name=name, pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]], pin=pin,
            options={
                CONF_KEY_TOPIC: self._topic,
                CONF_KEY_DIRECTION: self._direction.name,
                CONF_KEY_INTERRUPT: self._interrupt.name,
                CONF_KEY_RESISTOR: self._resistor.name,
                CONF_KEY_INVERT: self._invert,
                CONF_KEY_INITIAL: self._initial,
            }))

    def setup(self):
        """
        Configures the pin in hardware, returns ``True`` on success
        """
        log.info("Setting up '{name}' on {pin_prefix}{pin:02d} as {direction}".format(
            name=self._name, pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]],
            pin=self._pin, direction=self._direction.name))

        if not super().setup(): return False

        try:
            self._gpio.setup(self._pin, self._direction, self._resistor)
        except:
            log.error("An exception occurred while setting up '{name}' on {pin_prefix}{pin:02d}".format(
                name=self._name, pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]], pin=self._pin))
            log_traceback(log)
            release_gpio_lock(self._pin, self._gpio.getPinFromMode(self._pin, config[CONF_KEY_MODE]), TEXT_PACKAGE_NAME, mode=config[CONF_KEY_MODE])
            return False

        if self._direction == Direction.INPUT and self._interrupt != Interrupt.NONE:
            log.trace("Adding interrupt event for '{name}' on {pin_prefix}{pin:02d} with edge trigger '{edge}'".format(
                    name=self._name, pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]],
                    pin=self._pin, edge=self._interrupt.name))
            self._gpio.add_event_detect(
                    self._pin,
                    self._interrupt,
                    callback=self.handle_interrupt,
                    bouncetime=config[CONF_KEY_DEBOUNCE]
                )

        self._setup = True

        if self._direction == Direction.OUTPUT:
            if self._initial in [config[CONF_KEY_PAYLOAD_ON], config[CONF_KEY_PAYLOAD_OFF]]:
                log.trace("Setting '{name}' on {pin_prefix}{pin:02d} to initial state '{state}'".format(
                        name=self._name, pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]],
                        pin=self._pin, state=self._initial))
                self._set(self._initial)
            else:
                log.warn("Invalid initial state '{initial_state}' for '{name}' on {pin_prefix}{pin:02d}, setting pin to '{state}'".format(
                        name=self._name, initial_state=self._initial, pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]],
                        pin=self._pin, state=config[CONF_KEY_PAYLOAD_OFF]))
                self._set(config[CONF_KEY_PAYLOAD_OFF])
        else:
            self.publish_state()

        return True

    def publish_state(self):
        """
        Read the state from the pin and publish
        """
        if not self._setup: return

        try:
            state = bool(self._gpio.input(self._pin)) ^ self._invert # apply the invert flag
        except:
            log.error("An exception occurred while reading '{name}' on {pin_prefix}{pin:02d}".format(
                    name=self._name, pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]], pin=self._pin))
            log_traceback(log)
        else:
            log.debug("Read state '{state}' logic {logic} from '{name}' on {pin_prefix}{pin:02d}".format(
                name=self._name, pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]],
                state=config[CONF_KEY_PAYLOAD_ON] if state else config[CONF_KEY_PAYLOAD_OFF],
                logic=TEXT_LOGIC_STATE[int(state ^ self._invert)], pin=self._pin))
            publish(
                    self._topic,
                    payload=config[CONF_KEY_PAYLOAD_ON] if state else config[CONF_KEY_PAYLOAD_OFF]
                )

    def handle_message(self, topic, payload):
        """
        Handles messages on ``{pin_topic}/#``.
        """
        if not self._setup: return

        super().handle_message(topic, payload)

        if topic_matches_sub("{}/{}".format(self._topic, config[CONF_KEY_TOPIC_SETTER]), topic):
            self._set(payload.decode("utf-8"))

    def handle_interrupt(self, pin):
        """
        Handles pin change interrupts
        """
        log.debug("Interrupt fired for '{name}' on {pin_prefix}{pin:02d}".format(
            name=self._name, pin=self._pin, pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]]))
        self.publish_state()

    def _set(self, payload):
        """
        Set the state of the pin and publish
        ``payload`` expects ``payload on`` or ``payload off``
        """
        if not self._setup: return

        if payload == config[CONF_KEY_PAYLOAD_ON]:
            state = True
        elif payload == config[CONF_KEY_PAYLOAD_OFF]:
            state = False
        else:
            log.warn("Received unrecognized SET payload '{payload}' for '{name}' on {pin_prefix}{pin:02d}".format(
                    name=self._name, payload=payload, pin=self._pin,
                    pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]]))
            return

        try:
            self._gpio.output(self._pin, state ^ self._invert)
        except:
            log.error("An exception occurred while setting '{name}' on {pin_prefix}{pin:02d}".format(
                    name=self._name, pin=self._pin,
                    pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]]))
            log_traceback(log)
        else:
            log.debug("Set '{name}' on {pin_prefix}{pin:02d} to '{state}' logic {logic}".format(
                name=self._name, pin=self._pin, state=payload, logic=TEXT_LOGIC_STATE[int(state ^ self._invert)],
                pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]], ))
            self.publish_state()
