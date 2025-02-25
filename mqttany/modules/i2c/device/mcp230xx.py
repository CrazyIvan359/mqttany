"""
*******************
I2C Device MCP230xx
*******************
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

__all__ = ["CONF_OPTIONS", "SUPPORTED_DEVICES"]

import json
import typing as t
from collections import OrderedDict
from enum import Enum
from threading import Timer

import logger
from common import BusNode, BusProperty, PublishMessage, SubscribeMessage, validate_id
from config import resolve_type
from gpio import Mode, PinBias, PinEdge, PinMode, board
from gpio.pins.base import Pin as CorePin

from .. import common
from ..common import CONF_KEY_DEVICE, CONF_KEY_NAME
from .base import I2CDevice


class Logic(Enum):
    LOW = 0
    HIGH = 1


class Direction(Enum):
    INPUT = 10
    OUTPUT = 11


class Resistor(Enum):
    OFF = 20
    PULL_UP = 21


TEXT_STATE = {False: "OFF", "OFF": False, True: "ON", "ON": True}

CONF_KEY_MCP = "mcp230xx"
CONF_KEY_INT_PIN = "interrupt pin"
CONF_KEY_INT_RESISTOR = "interrupt pin resistor"
CONF_KEY_INT_POLLING = "interrupt polling interval"
CONF_KEY_PIN = "pin"
CONF_KEY_DIRECTION = "direction"
CONF_KEY_RESISTOR = "resistor"
CONF_KEY_INTERRUPT = "interrupt"
CONF_KEY_INVERT = "invert"
CONF_KEY_INITIAL = "initial state"
CONF_KEY_FIRST_INDEX = "first index"

CONF_OPTIONS: t.MutableMapping[str, t.Dict[str, t.Any]] = {
    "regex:.+": {
        CONF_KEY_DEVICE: {"selection": ["mcp23008", "mcp23017"]},
        CONF_KEY_MCP: OrderedDict(
            [
                ("type", "section"),
                (
                    "conditions",
                    [
                        (CONF_KEY_DEVICE, "mcp23008"),
                        (CONF_KEY_DEVICE, "mcp23017"),
                    ],
                ),
                (
                    CONF_KEY_INT_POLLING,
                    {
                        "default": 0,
                        "type": int,
                    },
                ),
                (
                    CONF_KEY_INT_PIN,
                    {
                        "default": -1,
                        "type": int,
                    },
                ),
                (
                    CONF_KEY_INT_RESISTOR,
                    {
                        "default": PinBias.PULL_UP,
                        "selection": {
                            "pullup": PinBias.PULL_UP,
                            "up": PinBias.PULL_UP,
                            "off": PinBias.NONE,
                            False: PinBias.NONE,
                            "none": PinBias.NONE,
                        },
                    },
                ),
                (
                    "regex:.+",
                    {
                        "type": "section",
                        "required": False,
                        CONF_KEY_PIN: {"type": (int, list)},  # type: ignore
                        CONF_KEY_NAME: {
                            "type": (str, list),
                            "default": "{pin_id}",
                        },
                        CONF_KEY_DIRECTION: {
                            "default": Direction.INPUT,
                            "selection": {
                                "input": Direction.INPUT,
                                "in": Direction.INPUT,
                                "output": Direction.OUTPUT,
                                "out": Direction.OUTPUT,
                            },
                        },
                        CONF_KEY_RESISTOR: {
                            "default": Resistor.OFF,
                            "selection": {
                                "pullup": Resistor.PULL_UP,
                                "up": Resistor.PULL_UP,
                                "off": Resistor.OFF,
                                False: Resistor.OFF,
                                "none": Resistor.OFF,
                            },
                        },
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
                            "selection": {
                                "ON": True,
                                "on": True,
                                True: True,
                                "OFF": False,
                                "off": False,
                                False: False,
                            },
                            "default": False,
                        },
                        CONF_KEY_FIRST_INDEX: {"type": int, "default": 0},
                    },
                ),
            ]
        ),
    },
}


# helpers to get/set bits
def _get_bit(val: int, bit: int) -> int:
    return val & (1 << bit) > 0


def _set_bit(val: int, bit: int, bit_val: int = 1) -> int:
    return (val & ~(1 << bit)) | bit_val << bit


def _clear_bit(val: int, bit: int) -> int:
    return val & ~(1 << bit)


class Pin(object):
    """
    MCP230xx Pin class
    """

    def __init__(
        self,
        pin: int,
        id: str,
        name: str,
        direction: Direction,
        resistor: Resistor,
        interrupt: PinEdge,
        invert: bool,
        initial: bool,
        device: I2CDevice,
    ) -> None:
        self._pin = pin
        self._id = id
        self._name = name
        self._direction = direction
        self._resistor = Resistor.OFF
        self._invert = invert
        self._device = t.cast(MCP230xx, device)
        self._path = f"{self._device.id}/{self.id}"
        self._pulse_timer = None
        self._last_state = None

        if direction == Direction.INPUT:
            self._resistor = resistor
            if resistor == Resistor.PULL_UP:
                self._device.gppu = _set_bit(self._device.gppu, pin)
            if interrupt != PinEdge.NONE:
                self._device.gpinten = _set_bit(self._device.gpinten, pin)
                if interrupt != PinEdge.BOTH:
                    self._device.intcon = _set_bit(self._device.intcon, pin)
                    if interrupt == PinEdge.FALLING:
                        self._device.defval = _set_bit(self._device.defval, pin)
        else:
            self._device.iodir = _clear_bit(self._device.iodir, pin)
            self.state = initial

    def publish_state(self) -> None:
        state = self.state_log
        common.publish_queue.put_nowait(
            PublishMessage(path=self._path, content=TEXT_STATE[state])
        )

    @property
    def state(self) -> bool:
        """
        Returns pin state as ``bool`` after applying invert flag
        """
        return bool(_get_bit(self._device.gpio, self._pin) ^ self._invert)

    @state.setter
    def state(self, value: bool) -> None:
        if self._direction == Direction.OUTPUT:
            self._device.gpio = _set_bit(
                self._device.gpio, self._pin, int(value) ^ self._invert
            )

    @property
    def state_log(self) -> bool:
        """
        Returns pin state as ``bool`` after applying invert flag and logs the event
        """
        state = self.state
        self._device.log.debug(
            "Read state %s logic %s from pin GP%02d '%s' on %s '%s'",
            TEXT_STATE[state],
            Logic(int(state ^ self._invert)).name,
            self._pin,
            self._name,
            self._device.device,
            self._device.name,
        )
        return state

    @state_log.setter
    def state_log(self, state: bool) -> None:
        if self._direction == Direction.OUTPUT:
            self._pulse_cancel()
            self.state = state
            self._device.log.debug(
                "Set pin GP%02d '%s' on %s '%s' to %s logic %s",
                self._pin,
                self._name,
                self._device.device,
                self._device.name,
                TEXT_STATE[state],
                Logic(int(state ^ self._invert)).name,
            )

    def _pulse(self, time: int, state: bool) -> None:
        """
        Sets the pin to ``state`` for ``time`` ms then to ``not state``.
        Any calls to ``pulse`` while the timer is running will cancel the previous pulse.
        Any changes to the pin state will cancel the timer.
        """
        self._pulse_cancel()
        self._device.log.debug(
            "Pulsing pin GP%02d '%s' on %s '%s' to %s logic %s for %dms",
            self._pin,
            self._name,
            self._device.device,
            self._device.name,
            TEXT_STATE[state],
            Logic(int(state)).name,
            time,
        )
        self.state_log = state
        self._device.write_gpio()
        self._pulse_timer = Timer(float(time) / 1000, self._pulse_end, args=[not state])
        self._pulse_timer.start()
        self.publish_state()

    def _pulse_end(self, state: bool) -> None:
        """
        End of a pulse cycle, set pin to state and log
        """
        self._pulse_timer = None
        self._device.log.debug(
            "PULSE ended for pin GP%02d '%s' on %s '%s'",
            self._pin,
            self._name,
            self._device.device,
            self._device.name,
        )
        self.state_log = state
        self._device.write_gpio()
        self.publish_state()

    def _pulse_cancel(self) -> None:
        if self._pulse_timer is not None:
            self._pulse_timer.cancel()
            self._pulse_timer = None
            self._device.log.debug(
                "Cancelled PULSE timer for pin GP%02d '%s' on %s '%s'",
                self._pin,
                self._name,
                self._device.device,
                self._device.name,
            )

    def set(self, content: str) -> None:
        """
        Handle a SET message
        """
        if self._direction == Direction.OUTPUT:
            state = str(resolve_type(content))
            if state in TEXT_STATE:
                self._pulse_cancel()
                self.state_log = t.cast(bool, TEXT_STATE[state])
                self._device.write_gpio()
                self.publish_state()
            else:
                self._device.log.warn(
                    "Received unrecognized SET message for pin GP%02d '%s' on %s '%s': %s",
                    self._pin,
                    self._name,
                    self._device.device,
                    self._device.name,
                    content,
                )
        else:
            self._device.log.warn(
                "Received SET command for pin GP%02d '%s' on %s '%s' but it is not "
                "configured as an output",
                self._pin,
                self._name,
                self._device.device,
                self._device.name,
            )

    def pulse(self, content: str) -> None:
        """
        Handle a PULSE message
        """
        if self._direction == Direction.OUTPUT:
            try:
                payload: t.Dict[str, t.Any] = json.loads(content)
            except ValueError:
                self._device.log.warn(
                    "Received unrecognized PULSE command for pin GP%02d '%s' on %s '%s': %s",
                    self._pin,
                    self._name,
                    self._device.device,
                    self._device.name,
                    content,
                )
            else:
                time = payload.get("time")
                state = payload.get("state")
                if not time:
                    self._device.log.error(
                        "Received PULSE command missing 'time' argument for pin "
                        "GP%02d '%s' on %s '%s': %s",
                        self._pin,
                        self._name,
                        self._device.device,
                        self._device.name,
                        content,
                    )
                    return
                if state is None:
                    self._device.read_gpio()
                    state = TEXT_STATE[self.state]
                else:
                    state = str(resolve_type(content))
                if state in TEXT_STATE:
                    self._pulse(time, t.cast(bool, TEXT_STATE[state]))
                else:
                    self._device.log.warn(
                        "Received unrecognized PULSE state for pin GP%02d '%s' on %s '%s': %s",
                        self._pin,
                        self._name,
                        self._device.device,
                        self._device.name,
                        state,
                    )
        else:
            self._device.log.warn(
                "Received PULSE command for pin GP%02d '%s' on %s '%s' but it is not "
                "configured as an output",
                self._pin,
                self._name,
                self._device.device,
                self._device.name,
            )

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def pin(self) -> int:
        return self._pin

    @property
    def direction(self) -> Direction:
        return self._direction

    @property
    def resistor(self) -> Resistor:
        return self._resistor

    @property
    def invert(self) -> bool:
        return self._invert


class MCP230xx(I2CDevice):
    """
    Base class for MCP23008 and MCP23017 GPIO Expanders
    """

    def __init__(
        self,
        id: str,
        name: str,
        device: str,
        address: int,
        bus: object,
        bus_path: str,
        device_config: t.Dict[str, t.Any],
    ) -> None:
        super().__init__(id, name, device, address, bus, bus_path, device_config)
        self._pin_from_path: t.Dict[str, int] = {}
        self._pin_max: int = 0
        self._pins: t.List[Pin] = []
        self.gpio: int = 0x0  # set by subclass
        self.iodir: int = 0x0
        self.gppu: int = 0x0
        self.gpinten: int = 0x0
        self.intcon: int = 0x0
        self.defval: int = 0x0
        self.intf: int = 0x0
        self._int_pin_handle: t.Union[CorePin, None] = None
        self._int_pin: int = device_config[CONF_KEY_MCP][CONF_KEY_INT_PIN]
        self._int_pin_resistor: Resistor = device_config[CONF_KEY_MCP][
            CONF_KEY_INT_RESISTOR
        ]
        self._int_poll_timer = None
        self._int_poll_int: float = device_config[CONF_KEY_MCP][CONF_KEY_INT_POLLING]

        if self._int_poll_int < 50 and self._int_poll_int > 0:
            self.log.warn(
                "Interrupt Polling Interval of %dms is invalid for device '%s', "
                "adjusting to minimum 50ms",
                self._int_poll_int,
                self.name,
            )
            self._int_poll_int = 50
        if self._int_poll_int:
            self._int_poll_int = self._int_poll_int / 1000.0

    def get_node(self) -> BusNode:
        node = super().get_node()
        node.add_property(
            "poll-all",
            BusProperty(name="Poll All Pins", settable=True, callback="device_message"),
        )
        node.add_property(
            "pulse", BusProperty(name="Pulse", settable=True, callback="device_message")
        )
        for pin in [pin for pin in self._pins if pin is not None]:
            node.add_property(
                pin.id,
                BusProperty(
                    name=pin.name,
                    settable=pin.direction == Direction.OUTPUT,
                    callback="device_message",
                ),
            )
            node.add_property(str(pin.pin), node.properties[pin.id])
        return node

    def setup(self) -> bool:
        if not super().setup():
            return False

        if self._int_pin > -1:
            self._int_pin_handle = board.get_pin(
                pin=self._int_pin,
                mode=Mode.SOC,
                pin_mode=PinMode.INPUT,
                bias=self._int_pin_resistor,
                edge=PinEdge.FALLING,
                interrupt_callback=self._poll_interrupts,
                interrupt_debounce=25,
            )
            if self._int_pin_handle and self._int_pin_handle.setup():
                self.log.debug(
                    "%s: configured interrupt pin on %s",
                    self.name,
                    self._int_pin_handle.get_name(Mode.SOC),
                )
        elif self._int_poll_int:
            self.log.debug(
                "Starting interrupt polling timer with interval of %ds for device '%s'",
                self._int_poll_int,
                self.name,
            )
            self._int_poll_timer = Timer(self._int_poll_int, self._poll_interval)
            self._int_poll_timer.start()

        self._setup = True
        return True

    def cleanup(self) -> None:
        """
        Perform cleanup on module shutdown.
        Subclasses may override this method
        """
        if self._setup:
            if self._int_pin_handle is not None:
                self._int_pin_handle.cleanup()
            if self._int_poll_timer is not None:
                self._int_poll_timer.cancel()
                self._int_poll_timer = None
            self.gpio = 0
            for pin in self._pins:
                if pin is not None:
                    pin.state = False  # set all pins to configured OFF
            self.write_gpio()
            self.publish_state()
            self._setup = False

    def publish_state(self) -> None:
        """
        Publishes the state of all configured pins
        """
        if self._setup:
            self._log.debug("Polling all pins")
            self.read_gpio()
            for pin in self._pins:
                if pin is not None:
                    pin.publish_state()

    def message_callback(self, message: SubscribeMessage) -> None:
        """
        Handle messages to any of this device's subscriptions.
        """
        if self._setup:
            path = message.path.strip("/").split("/")[1:]
            if len(path) > 2:
                self._log.debug("Received message on unregistered path: %s", message)
            elif path[0] == "poll-all":
                self.publish_state()
            elif path[0] == "pulse":
                try:
                    content_json = json.loads(message.content)
                except ValueError:
                    self._log.warn(
                        "Received unrecognized PULSE command: %s", message.content
                    )
                else:
                    if content_json.get("pin") in self._pin_from_path:
                        self._pins[self._pin_from_path[content_json["pin"]]].pulse(
                            message.content
                        )
                    else:
                        self._log.warn(
                            "Received PULSE command for unknown pin %s: %s",
                            content_json.get("pin"),
                            message.content,
                        )
            elif path[0] in self._pin_from_path and path[1] == "set":
                self._pins[self._pin_from_path[path[0]]].set(message.content)
            elif path[0] in self._pin_from_path and path[1] == "pulse":
                try:
                    content_json = json.loads(message.content)
                except ValueError:
                    self._log.warn(
                        "Received unrecognized PULSE command for pin GP%02d '%s': %s",
                        self._pins[self._pin_from_path[path[0]]].pin,
                        self._pins[self._pin_from_path[path[0]]].name,
                        message.content,
                    )
                else:
                    self._pins[self._pin_from_path[path[0]]].pulse(message.content)
            else:
                self._log.debug("Received message on unregistered path: %s", message)

    def _poll_interval(self) -> None:
        """
        Triggers interrupt check and restarts the timer
        """
        # self.log.trace("Interrupt polling timer fired for device '%s'", self.name)
        self._int_poll_timer = Timer(self._int_poll_int, self._poll_interval)
        self._int_poll_timer.start()
        self._poll_interrupts(silent=True)

    def _poll_interrupts(
        self, pin_state: t.Union[bool, None] = None, silent: bool = False
    ) -> None:
        """
        Reads interrupt register(s) and publishes any pins with an active interrupt
        """
        if not silent:
            self.log.debug("Reading interrupt register for device '%s'", self.name)
        self.read_intf(silent)
        if self.intf:
            self.read_gpio()
            for i in range(self._pin_max + 1):
                if _get_bit(self.intf, i):
                    self._pins[i].publish_state()

    def _build_pins(self, device_config: t.Dict[str, t.Any]) -> None:
        """
        Setup device pins from config
        """
        for pin_id in [
            key
            for key in device_config[CONF_KEY_MCP]
            if isinstance(device_config[CONF_KEY_MCP][key], dict)
        ]:
            pin_config = device_config[CONF_KEY_MCP].pop(pin_id)
            if isinstance(pin_config[CONF_KEY_PIN], int):  # Single pin definition
                if not isinstance(pin_config[CONF_KEY_NAME], str):
                    self._log.error(
                        "Failed to configure pin '%s' for %s '%s': single pin "
                        "definitions can have only 1 name",
                        pin_id,
                        self.device,
                        self.name,
                    )
                else:
                    self._setup_pin(
                        pin=pin_config[CONF_KEY_PIN],
                        id=pin_id,
                        name=pin_config[CONF_KEY_NAME],
                        pin_config=pin_config,
                    )
            elif isinstance(pin_config[CONF_KEY_PIN], list):  # Multiple pin definition
                if isinstance(pin_config[CONF_KEY_NAME], list) and len(
                    pin_config[CONF_KEY_PIN]
                ) != len(pin_config[CONF_KEY_NAME]):
                    self._log.error(
                        "Failed to configure pin group '%s' for %s '%s': must have the "
                        "same number of pins and names",
                        pin_id,
                        self.device,
                        self.name,
                    )
                else:
                    for index in range(len(pin_config[CONF_KEY_PIN])):
                        if isinstance(pin_config[CONF_KEY_NAME], list):
                            name = pin_config[CONF_KEY_NAME][index]
                        elif "{index}" in pin_config[CONF_KEY_NAME]:
                            name = pin_config[CONF_KEY_NAME]
                        else:
                            name = f"{pin_config[CONF_KEY_NAME]} {index + pin_config[CONF_KEY_FIRST_INDEX]}"
                        self._setup_pin(
                            pin=pin_config[CONF_KEY_PIN][index],
                            id=f"{pin_id}-{index + pin_config[CONF_KEY_FIRST_INDEX]}",
                            name=name,
                            pin_config=pin_config,
                        )

    def _setup_pin(
        self,
        pin: int,
        id: str,
        name: str,
        pin_config: t.Dict[str, t.Any],
    ) -> None:
        """
        Setup pin for given options
        """
        if not validate_id(id):
            self._log.warn("'%s' is not a valid ID and will be ignored", id)
        elif self._pins[pin] is not None:
            self._log.warn(
                "Duplicate configuration for GP%02d '%s' found in '%s' for %s '%s' "
                "will be ignored, pin already configured under '%s'",
                pin,
                id,
                self._id,
                self._device,
                self._name,
                self._pins[pin].name,
            )
        elif pin > self._pin_max:
            self._log.warn(
                "Found pin GP%02d in '%s' for %s '%s' but highest pin for device is GP%02d",
                pin,
                id,
                self._id,
                self._name,
                self._pin_max,
            )
        else:
            self._pins[pin] = Pin(
                pin=pin,
                id=id,
                name=name,
                direction=pin_config[CONF_KEY_DIRECTION],
                resistor=pin_config[CONF_KEY_RESISTOR],
                interrupt=pin_config[CONF_KEY_INTERRUPT],
                invert=pin_config[CONF_KEY_INVERT],
                initial=pin_config[CONF_KEY_INITIAL],
                device=self,
            )
            self._pin_from_path[id] = pin
            self._log.debug(
                "Configured pin GP%02d '%s' on %s '%s' with options: %s",
                pin,
                self._pins[pin].name,
                self.device,
                self.name,
                {
                    "ID": id,
                    CONF_KEY_DIRECTION: self._pins[pin].direction.name,
                    CONF_KEY_RESISTOR: self._pins[pin].resistor.name,
                    CONF_KEY_INVERT: self._pins[pin].invert,
                    CONF_KEY_INITIAL: TEXT_STATE[pin_config[CONF_KEY_INITIAL]],
                },
            )

    def read_gpio(self) -> None:
        """
        Read the GP register(s)
        """
        raise NotImplementedError

    def read_intf(self, silent: bool = False) -> None:
        """
        Read the Interrupt Flag register(s)
        """
        raise NotImplementedError

    def write_gpio(self) -> None:
        """
        Write the GP register(s)
        """
        raise NotImplementedError

    @property
    def log(self) -> logger.mqttanyLogger:
        return self._log


class MCP23008(MCP230xx):
    """
    MCP23008 8-channel GPIO Expander
    """

    # Device Registers
    # fmt: off
    _IODIR =   0x00  # Direction
    _IPOL =    0x01  # Input Polarity (Invert)
    _GPINTEN = 0x02  # Interrupt Enable
    _DEFVAL =  0x03  # Default Compare Value
    _INTCON =  0x04  # Interrupt Control
    _IOCON =   0x05  # I/O Configuration
    _GPPU =    0x06  # Pull Up
    _INTF =    0x07  # Interrupt Flag
    _INTCAP =  0x08  # Interrupt Capture
    _GPIO =    0x09  # GPIO
    _OLAT =    0x0A  # Output Latch
    # fmt: on

    def __init__(
        self,
        id: str,
        name: str,
        device: str,
        address: int,
        bus: object,
        bus_path: str,
        device_config: t.Dict[str, t.Any],
    ) -> None:
        super().__init__(id, name, device, address, bus, bus_path, device_config)
        self._log = logger.get_logger("i2c.mcp23008")
        self._pin_max = 7
        self._pins: t.List[Pin] = [None] * (self._pin_max + 1)  # type: ignore
        self.gpio = 0x00
        self.iodir = 0xFF
        self.gppu = 0x00
        self.gpinten: int = 0x00
        self.intcon: int = 0x00
        self.defval: int = 0x00
        self.intf: int = 0x00
        super()._build_pins(device_config)

    def setup(self) -> bool:
        """
        Setup the hardware
        """
        if not super().setup():
            return False

        self._setup = True
        self._log.debug(
            "Writing initial values to registers of %s '%s' at address 0x%02x on bus '%s'",
            self._device,
            self._name,
            self._address,
            self._bus_path,
        )
        if not self._write_block(
            0x00,
            bytes(
                [
                    self.iodir,
                    0x00,  # IPOL
                    self.gpinten,  # GPINTEN
                    self.defval,  # DEFVAL
                    self.intcon,  # INTCON
                    0x04,  # IOCON
                    self.gppu,
                    0x00,  # INTF
                    0x00,  # INTCAP
                    self.gpio,
                ]
            ),
        ):
            self._setup = False

        return self._setup

    def read_gpio(self) -> None:
        gpio = self._read_byte(self._GPIO)
        if gpio is not None:
            self.gpio = gpio

    def read_intf(self, silent: bool = False) -> None:
        intf = self._read_byte(self._INTF, silent)
        if intf is not None:
            self.intf = intf

    def write_gpio(self) -> None:
        self._write_byte(self._GPIO, self.gpio)


class MCP23017(MCP230xx):
    """
    MCP23017 16-channel GPIO Expander
    """

    # Device Registers
    # fmt: off
    _IODIRA =   0x00  # Direction
    _IODIRB =   0x01
    _IPOLA =    0x02  # Input Polarity (Invert)
    _IPOLB =    0x03
    _GPINTENA = 0x04  # Interrupt Enable
    _GPINTENB = 0x05
    _DEFVALA =  0x06  # Default Compare Value
    _DEFVALB =  0x07
    _INTCONA =  0x08  # Interrupt Control
    _INTCONB =  0x09
    _IOCON =    0x0A  # I/O Configuration
    # IOCON    = 0x0B # duplicate address
    _GPPUA =    0x0C  # Pull Up
    _GPPUB =    0x0D
    _INTFA =    0x0E  # Interrupt Flag
    _INTFB =    0x0F
    _INTCAPA =  0x10  # Interrupt Capture
    _INTCAPB =  0x11
    _GPIOA =    0x12  # GPIO
    _GPIOB =    0x13
    _OLATA =    0x14  # Output Latch
    _OLATB =    0x15
    # fmt: on

    def __init__(
        self,
        id: str,
        name: str,
        device: str,
        address: int,
        bus: object,
        bus_path: str,
        device_config: t.Dict[str, t.Any],
    ):
        super().__init__(id, name, device, address, bus, bus_path, device_config)
        self._log = logger.get_logger("i2c.mcp23017")
        self._pin_max = 15
        self._pins: t.List[Pin] = [None] * (self._pin_max + 1)  # type: ignore
        self.gpio = 0x0000
        self.iodir = 0xFFFF
        self.gppu = 0x0000
        self.gpinten: int = 0x0000
        self.intcon: int = 0x0000
        self.defval: int = 0x0000
        self.intf: int = 0x0000
        super()._build_pins(device_config)

    def setup(self) -> bool:
        """
        Setup the hardware
        """
        if not super().setup():
            return False

        self._setup = True
        self._log.debug(
            "Writing initial values to registers of %s '%s' at address 0x%02x on bus '%s'",
            self._device,
            self._name,
            self._address,
            self._bus_path,
        )
        if not self._write_block(
            0x00,
            bytes(
                [
                    self.iodir & 0xFF,  # IODIRA
                    self.iodir >> 8,  # IODIRB
                    0x00,  # IPOLA
                    0x00,  # IPOLB
                    self.gpinten & 0xFF,  # GPINTENA
                    self.gpinten >> 8,  # GPINTENB
                    self.defval & 0xFF,  # DEFVALA
                    self.defval >> 8,  # DEFVALB
                    self.intcon & 0xFF,  # INTCONA
                    self.intcon >> 8,  # INTCONB
                    0x44,  # IOCON
                    0x44,  # IOCON
                    self.gppu & 0xFF,  # GPPUA
                    self.gppu >> 8,  # GPPUB
                    0x00,  # INTFA
                    0x00,  # INTFB
                    0x00,  # INTCAPA
                    0x00,  # INTCAPB
                    self.gpio & 0xFF,  # GPIOA
                    self.gpio >> 8,  # GPIOB
                ]
            ),
        ):
            self._setup = False

        return self._setup

    def read_gpio(self) -> None:
        gpio = self._read_word(self._GPIOA)
        if gpio is not None:
            self.gpio = gpio

    def read_intf(self, silent: bool = False) -> None:
        intf = self._read_word(self._INTFA, silent)
        if intf is not None:
            self.intf = intf

    def write_gpio(self) -> None:
        self._write_word(self._GPIOA, self.gpio)


SUPPORTED_DEVICES: t.Dict[str, t.Type[I2CDevice]] = {
    "mcp23008": MCP23008,
    "mcp23017": MCP23017,
}
