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

import json
from threading import Timer

import logger
from logger import log_traceback
from config import resolve_type
from common import release_gpio_lock, TEXT_PIN_PREFIX, TEXT_LOGIC_STATE
from common import Direction, Resistor, Interrupt

from modules.mqtt import publish, topic_matches_sub

from modules.gpio.pin.base import Pin
from modules.gpio.common import config
from modules.gpio.common import *

CONF_KEY_TOPIC_PULSE = "topic pulse"
CONF_KEY_DEBOUNCE = "debounce"
CONF_KEY_INTERRUPT = "interrupt"
CONF_KEY_RESISTOR = "resistor"
CONF_KEY_INITIAL = "initial state"

CONF_OPTIONS = {
    CONF_KEY_TOPIC_PULSE: {"type": str, "default": "pulse"},
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

__all__ = [ "DigitalPin" ]


class DigitalPin(Pin):
    """
    GPIO Digital Pin class
    """

    def __init__(self, name, pin, topic, pin_config, index=None):
        super().__init__(name, pin, topic, index)
        self._pulse_timer = None
        self._state_map = { # map payload on/off to bool
            config[CONF_KEY_PAYLOAD_OFF]: 0,
            config[CONF_KEY_PAYLOAD_ON]: 1,
            0: config[CONF_KEY_PAYLOAD_OFF],
            1: config[CONF_KEY_PAYLOAD_ON]
        }
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
                self.set(self._state_map[self._initial] ^ self._invert)
            else:
                log.warn("Unrecognized initial state '{initial_state}' for '{name}' on {pin_prefix}{pin:02d}, setting pin to '{state}'".format(
                        name=self._name, initial_state=self._initial, pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]],
                        pin=self._pin, state=config[CONF_KEY_PAYLOAD_OFF]))
                self.set(False ^ self._invert)

        return True

    def publish_state(self):
        """
        Read the state from the pin and publish
        """
        if not self._setup: return

        state = self.get()
        if state is not None:
            log.debug("Read state '{state}' logic {logic} from '{name}' on {pin_prefix}{pin:02d}".format(
                name=self._name, pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]],
                state=self._state_map[int(state ^ self._invert)],
                logic=TEXT_LOGIC_STATE[int(state)], pin=self._pin))
            publish(
                    self._topic,
                    payload=self._state_map[int(state ^ self._invert)]
                )

    def handle_message(self, topic, payload):
        """
        Handles messages on ``{pin_topic}/#``.
        """
        if not self._setup: return

        super().handle_message(topic, payload)

        if topic_matches_sub("{}/{}".format(self._topic, config[CONF_KEY_TOPIC_SETTER]), topic):
            self.handle_set(payload.decode("utf-8"))
        elif topic_matches_sub("{}/{}".format(self._topic, config[CONF_KEY_TOPIC_PULSE]), topic):
            self.handle_pulse(payload.decode("utf-8"))

    def get(self):
        """
        Reads the pin state, return ``None`` if read fails
        """
        if not self._setup: return None

        try:
            return bool(self._gpio.input(self._pin))
        except:
            log.error("An exception occurred while reading '{name}' on {pin_prefix}{pin:02d}".format(
                    name=self._name, pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]], pin=self._pin))
            log_traceback(log)
            return None

    def set(self, state):
        """
        Set the state of the pin
        """
        if not self._setup: return False

        try:
            self._gpio.output(self._pin, state)
            return True
        except:
            log.error("An exception occurred while setting '{name}' on {pin_prefix}{pin:02d}".format(
                    name=self._name, pin=self._pin,
                    pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]]))
            log_traceback(log)
            return False

    def pulse(self, time, state):
        """
        Sets the pin to ``state`` for ``time`` ms then to ``not state``.
        Any calls to ``pulse`` while the timer is running will cancel the previous pulse.
        Any changes to the pin state will cancel the timer.
        """
        if not self.setup: return

        if self._pulse_timer is not None:
            self._pulse_timer.cancel()
            self._pulse_timer = None
            log.debug("Cancelled PULSE timer for '{name}' on {pin_prefix}{pin:02d}".format(
                name=self._name, pin=self._pin, pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]]))

        if self.set(state):
            self._pulse_timer = Timer(
                float(time) / 1000,
                self._pulse_end,
                args=[not state]
            )
            self._pulse_timer.start()
            self.publish_state()

    def _pulse_end(self, state):
        """
        End of a pulse cycle, set pin to state and log
        """
        self._pulse_timer = None
        if not self.setup: return

        if self.set(state):
            log.debug("PULSE ended for '{name}' on {pin_prefix}{pin:02d} set pin to '{state}' logic {logic}".format(
                name=self._name, pin=self._pin,
                pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]],
                logic=TEXT_LOGIC_STATE[int(state)],
                state=self._state_map[int(state ^ self._invert)]))
            self.publish_state()

    def handle_set(self, payload):
        """
        Handle a SET message
        """
        if not self._setup: return

        if not self._direction == Direction.OUTPUT:
            log.warn("Received SET command for '{name}' on {pin_prefix}{pin:02d} but it is configured as an output".format(
                name=self._name, pin=self._pin, pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]]))
            return
        elif payload == config[CONF_KEY_PAYLOAD_ON]:
            state = True ^ self._invert
        elif payload == config[CONF_KEY_PAYLOAD_OFF]:
            state = False ^ self._invert
        else:
            log.warn("Received unrecognized SET payload '{payload}' for '{name}' on {pin_prefix}{pin:02d}".format(
                    name=self._name, payload=payload, pin=self._pin,
                    pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]]))
            return

        if self._pulse_timer is not None:
            self._pulse_timer.cancel()
            self._pulse_timer = None
            log.debug("Cancelled PULSE timer for '{name}' on {pin_prefix}{pin:02d}".format(
                name=self._name, pin=self._pin, pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]]))

        if self.set(state):
            log.debug("Set '{name}' on {pin_prefix}{pin:02d} to '{state}' logic {logic}".format(
                name=self._name, pin=self._pin, state=payload, logic=TEXT_LOGIC_STATE[int(state)],
                pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]], ))
            self.publish_state()

    def handle_pulse(self, payload):
        """
        Handle a PULSE message
        """
        if not self._setup: return

        if not self._direction == Direction.OUTPUT:
            log.warn("Received PULSE command for '{name}' on {pin_prefix}{pin:02d} but it is configured as an output".format(
                name=self._name, pin=self._pin, pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]]))
            return

        # JSON payload
        if "{" in payload:
            try:
                payload = json.loads(payload)
            except ValueError:
                log.error("Received malformed JSON '{payload}' for PULSE for '{name}' on {pin_prefix}{pin:02d}".format(
                    payload=payload, name=self._name, pin=self._pin,
                    pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]]))
                return
            else:
                if not "time" in payload:
                    log.error("Received JSON PULSE command missing 'time' argument for '{name}' on {pin_prefix}{pin:02d}".format(
                        name=self._name, pin=self._pin, pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]]))
                    return
                if not "state" in payload:
                    payload["state"] = self.get()
                    if payload["state"] is not None:
                        payload["state"] = not payload["state"]
                        #log.warn("Received JSON PULSE command missing 'state' argument for '{name}' on {pin_prefix}{pin:02d}, using pin state".format(
                        #    name=self._name, pin=self._pin, state=payload["state"],
                        #    pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]]))
                    else:
                        log.error("PULSE failed, unable to read pin state for '{name}' on {pin_prefix}{pin:02d}".format(
                            name=self._name, pin=self._pin, pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]]))
                        return

        # List payload "time, state"
        elif len(payload.split(",")) > 1:
            if len(payload.split(",")) != 2:
                log.error("Received unrecognized PULSE command '{payload}' for '{name}' on {pin_prefix}{pin:02d}".format(
                    name=self._name, pin=self._pin, pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]]))
                return
            payload = {
                "time": resolve_type(payload.split(",")[0].strip()),
                "state": payload.split(",")[1].strip()
            }
            if not isinstance(payload["time"], int):
                log.error("Received invalid time '{time}' for PULSE command for '{name}' on {pin_prefix}{pin:02d}".format(
                    time=payload["time"], name=self._name, pin=self._pin,
                    pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]]))
                return

        # Time only payload
        else:
            payload = {"time": resolve_type(payload)}
            if not isinstance(payload["time"], int):
                log.error("Received invalid time '{time}' for PULSE command for '{name}' on {pin_prefix}{pin:02d}".format(
                    time=payload["time"], name=self._name, pin=self._pin,
                    pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]]))
                return
            payload["state"] = self.get()
            if payload["state"] is not None:
                payload["state"] = not payload["state"]
            else:
                log.error("PULSE failed, unable to read pin state for '{name}' on {pin_prefix}{pin:02d}".format(
                    name=self._name, pin=self._pin, pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]]))
                return

        if isinstance(payload["state"], str):
            if payload["state"] == config[CONF_KEY_PAYLOAD_ON]:
                payload["state"] = True ^ self._invert
            elif payload["state"] == config[CONF_KEY_PAYLOAD_OFF]:
                payload["state"] = False ^ self._invert
            else:
                log.error("Received unrecognized state '{state}' for PULSE command for '{name}' on {pin_prefix}{pin:02d}".format(
                    state=payload["state"], name=self._name, pin=self._pin,
                    pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]]))
                return

        log.debug("Pulsing '{name}' on {pin_prefix}{pin:02d} to '{state}' logic {logic} for {time}ms".format(
            name=self._name, pin=self._pin, time=payload["time"],
            pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]],
            logic=TEXT_LOGIC_STATE[int(payload["state"])],
            state=self._state_map[int(payload["state"] ^ self._invert)]))
        self.pulse(**payload)

    def handle_interrupt(self, pin):
        """
        Handles pin change interrupts
        """
        log.debug("Interrupt fired for '{name}' on {pin_prefix}{pin:02d}".format(
            name=self._name, pin=self._pin, pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]]))
        self.publish_state()
