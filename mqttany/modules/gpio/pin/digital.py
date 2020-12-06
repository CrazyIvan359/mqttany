"""
****************
GPIO Digital Pin
****************

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

__all__ = ["SUPPORTED_PIN_MODES", "CONF_OPTIONS"]

import json
from threading import Timer
from enum import Enum

import logger
from logger import log_traceback
from config import resolve_type
from common import BusMessage, BusProperty
from gpio import board, Mode, PinMode, PinBias, PinEdge

from modules.gpio import common
from modules.gpio.pin.base import Pin
from modules.gpio.common import CONFIG, CONF_KEY_PIN_MODE

CONF_KEY_DEBOUNCE = "debounce"
CONF_KEY_RESISTOR = "resistor"
CONF_KEY_DIGITAL = "digital"
CONF_KEY_INTERRUPT = "interrupt"
CONF_KEY_INVERT = "invert"
CONF_KEY_INITIAL = "initial state"

CONF_OPTIONS = {
    CONF_KEY_DEBOUNCE: {"type": int, "default": 50},
    "regex:.+": {
        CONF_KEY_PIN_MODE: {
            "default": PinMode.INPUT,
            "selection": {
                "input": PinMode.INPUT,
                "in": PinMode.INPUT,
                "output": PinMode.OUTPUT,
                "out": PinMode.OUTPUT,
            },
        },
        CONF_KEY_RESISTOR: {
            "default": PinBias.NONE,
            "selection": {
                "pullup": PinBias.PULL_UP,
                "up": PinBias.PULL_UP,
                "pulldown": PinBias.PULL_DOWN,
                "down": PinBias.PULL_DOWN,
                "off": PinBias.NONE,
                "none": PinBias.NONE,
            },
        },
        CONF_KEY_DIGITAL: {
            "type": "section",
            "conditions": [
                (CONF_KEY_PIN_MODE, PinMode.INPUT),
                (CONF_KEY_PIN_MODE, PinMode.OUTPUT),
            ],
            CONF_KEY_INTERRUPT: {
                "default": PinEdge.NONE,
                "selection": {
                    "rising": PinEdge.RISING,
                    "falling": PinEdge.FALLING,
                    "both": PinEdge.BOTH,
                    "none": PinEdge.NONE,
                },
            },
            CONF_KEY_INVERT: {"type": bool, "default": False},
            CONF_KEY_INITIAL: {
                "selection": {"ON": True, "on": True, "OFF": False, "off": False},
                "default": False,
            },
        },
    },
}

TEXT_STATE = {False: "OFF", "OFF": False, True: "ON", "ON": True}


class Logic(Enum):
    LOW = 0
    HIGH = 1


class Digital(Pin):
    """
    GPIO Digital Pin class
    """

    def __init__(
        self, pin: int, gpio_mode: Mode, id: str, name: str, pin_config: dict = {}
    ):
        super().__init__(pin, gpio_mode, id, name, pin_config)
        self._log = logger.get_logger("gpio.digital")
        self._pulse_timer = None
        self._bias = pin_config[CONF_KEY_RESISTOR]
        self._edge = pin_config[CONF_KEY_DIGITAL][CONF_KEY_INTERRUPT]
        self._invert = pin_config[CONF_KEY_DIGITAL][CONF_KEY_INVERT]
        self._initial = pin_config[CONF_KEY_DIGITAL][CONF_KEY_INITIAL]
        self._handle = board.get_pin(
            pin=pin,
            mode=gpio_mode,
            pin_mode=self._mode,
            bias=self._bias,
            edge=self._edge,
            interrupt_callback=self.interrupt,
            interrupt_debounce=CONFIG[CONF_KEY_DEBOUNCE],
        )
        if self._handle:
            self._log.debug(
                "Configured '%s' on %s with options: %s",
                self._name,
                self.pin_name,
                {
                    "ID": self.id,
                    CONF_KEY_PIN_MODE: self._mode.name,
                    CONF_KEY_INTERRUPT: self._edge.name,
                    CONF_KEY_RESISTOR: self._bias.name,
                    CONF_KEY_INVERT: self._invert,
                    CONF_KEY_INITIAL: TEXT_STATE[self._initial],
                },
            )

    def get_property(self) -> BusProperty:
        return BusProperty(
            name=self.name,
            settable=self._mode == PinMode.OUTPUT,
            callback="pin_message",
        )

    def setup(self):
        """
        Configures the pin in hardware, returns ``True`` on success
        """
        if self._handle:
            self._log.info(
                "Setting up '%s' on %s as %s",
                self.name,
                self.pin_name,
                self._mode.name,
            )
            if self._handle.setup():
                self._setup = True
                if self._mode == PinMode.OUTPUT:
                    self._log.trace(
                        "Setting '%s' on %s to initial state %s logic %s",
                        self.name,
                        self.pin_name,
                        TEXT_STATE[self._initial],
                        Logic(self._initial ^ self._invert).name,
                    )
                    self._set(self._initial ^ self._invert)
                    del self._initial
        else:
            self._log.warn(
                "Unable to setup '%s' as %s, no available pin class",
                self.name,
                self._mode.name,
            )

        return self._setup

    def cleanup(self):
        """
        Cleanup actions when stopping
        """
        if self._setup and self._mode == PinMode.OUTPUT:
            self._set(False)
        super().cleanup()

    def publish_state(self):
        """
        Read the state from the pin and publish
        """
        if self._setup:
            state = self.get()
            if state is not None:
                self._log.debug(
                    "Read state %s logic %s from '%s' on %s",
                    TEXT_STATE[state],
                    Logic(int(state ^ self._invert)).name,
                    self.name,
                    self.pin_name,
                )
                common.publish_queue.put_nowait(
                    BusMessage(path=self.path, content=TEXT_STATE[state])
                )

    def message_callback(self, path: str, content: str):
        """
        Handles messages on the pin's paths. Path will have the pin's path removed,
        ex. path may only be ``set``.
        """
        if self._setup:
            if path == "set":
                self.set(content)
            elif path == "pulse":
                self.pulse(content)
            else:
                self._log.trace(
                    "Received unrecognized message on '%s' for '%s' on %s: %s",
                    path,
                    self.name,
                    self.pin_name,
                    content,
                )

    def get(self) -> bool:
        """
        Reads the pin state, return ``None`` if read fails
        """
        if self._setup:
            try:
                return bool(self._handle.read() ^ self._invert)
            except:
                self._log.error(
                    "An exception occurred while reading '%s' on %s",
                    self.name,
                    self.pin_name,
                )
                log_traceback(self._log)
        return None

    def _set(self, state: bool):
        """
        Set the state of the pin
        """
        if self._setup:
            try:
                self._handle.write(state ^ self._invert)
                self._log.debug(
                    "Set '%s' on %s to %s logic %s",
                    self.name,
                    self.pin_name,
                    TEXT_STATE[state],
                    Logic(state ^ self._invert).name,
                )
                return True
            except:
                self._log.error(
                    "An exception occurred while setting '%s' on %s",
                    self.name,
                    self.pin_name,
                )
        return False

    def _pulse(self, time: int, state: bool):
        """
        Sets the pin to ``state`` for ``time`` ms then to ``not state``.
        Any calls to ``pulse`` while the timer is running will cancel the previous pulse.
        Any changes to the pin state will cancel the timer.
        """
        if self._setup:
            self._log.debug(
                "Pulsing '%s' on %s to %s logic %s for %dms",
                self.name,
                self.pin_name,
                TEXT_STATE[state],
                Logic(state ^ self._invert).name,
                time,
            )
            self._pulse_cancel()
            if self._set(state):
                self._pulse_timer = Timer(
                    float(time) / 1000, self._pulse_end, args=[not state]
                )
                self._pulse_timer.start()
                self.publish_state()

    def _pulse_end(self, state: bool):
        """
        End of a pulse cycle, set pin to state and log
        """
        if self._setup:
            self._pulse_timer = None
            if self._set(state):
                self._log.debug(
                    "PULSE ended for '%s' on %s set pin to %s logic %s",
                    self.name,
                    self.pin_name,
                    TEXT_STATE[state],
                    Logic(state ^ self._invert).name,
                )
                self.publish_state()

    def _pulse_cancel(self):
        """
        Cancel pulse timer if it is running.
        """
        if self._pulse_timer is not None:
            self._pulse_timer.cancel()
            self._pulse_timer = None
            self._log.debug(
                "Cancelled PULSE timer for '%s' on %s",
                self.name,
                self.pin_name,
            )

    def set(self, content: str):
        """
        Handle a SET message
        """
        if self._setup:
            if self._mode == PinMode.OUTPUT:
                state = str(resolve_type(content))
                if state in TEXT_STATE:
                    self._pulse_cancel()
                    if self._set(TEXT_STATE[state]):
                        self.publish_state()
                else:
                    self._log.warn(
                        "Received unrecognized SET message for '%s' on %s: %s",
                        self.name,
                        self.pin_name,
                        content,
                    )
            else:
                self._log.warn(
                    "Received SET command for '%s' on %s but it is not configured as an output",
                    self.name,
                    self.pin_name,
                )

    def pulse(self, content: str):
        """
        Handle a PULSE message
        """
        if self._setup:
            if self._mode == PinMode.OUTPUT:
                try:
                    content = json.loads(content)
                except ValueError:
                    self._log.error(
                        "Received malformed JSON in PULSE command for '%s' on %s: %s",
                        self.name,
                        self.pin_name,
                        content,
                    )
                else:
                    time = content.get("time")
                    state = content.get("state", TEXT_STATE.get(self.get()))
                    if not time:
                        self._log.error(
                            "Received PULSE command missing 'time' argument for '%s' on %s: %s",
                            self.name,
                            self.pin_name,
                            content,
                        )
                        return
                    if state is None:
                        self._log.error(
                            "PULSE failed, unable to read state for '%s' on %s",
                            self.name,
                            self.pin_name,
                        )
                        return

                    state = str(resolve_type(content))
                    if state in TEXT_STATE:
                        self._pulse(time, TEXT_STATE[state])
                    else:
                        self._log.warn(
                            "Received unrecognized PULSE state for '%s' on %s: %s",
                            self.name,
                            self.pin_name,
                            state,
                        )
            else:
                self._log.warn(
                    "Received PULSE command for '%s' on %s but it is not configured as an output",
                    self.name,
                    self.pin_name,
                )

    def interrupt(self, state: bool):
        """
        Handles pin change interrupts
        """
        state = state ^ self._invert
        self._log.trace(
            "%s edge trigger fired with state %s logic %s for '%s' on %s",
            "Rising" if state else "Falling",
            TEXT_STATE[state],
            Logic(int(state ^ self._invert)).name,
            self.name,
            self.pin_name,
        )
        common.publish_queue.put_nowait(
            BusMessage(path=self.path, content=TEXT_STATE[state])
        )


SUPPORTED_PIN_MODES = {PinMode.INPUT: Digital, PinMode.OUTPUT: Digital}
