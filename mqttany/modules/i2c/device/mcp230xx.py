"""
*******************
I2C Device MCP230xx
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

__all__ = ["CONF_OPTIONS", "SUPPORTED_DEVICES"]

from collections import OrderedDict
from enum import Enum
import json
from threading import Timer

import logger
from config import resolve_type
from common import BusMessage, BusNode, BusProperty, validate_id
from modules.i2c.device.base import I2CDevice
from modules.i2c import common
from modules.i2c.common import CONF_KEY_NAME, CONF_KEY_DEVICE


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
CONF_KEY_PIN = "pin"
CONF_KEY_DIRECTION = "direction"
CONF_KEY_RESISTOR = "resistor"
CONF_KEY_INVERT = "invert"
CONF_KEY_INITIAL = "initial state"
CONF_KEY_FIRST_INDEX = "first index"

CONF_OPTIONS = {
    "regex:.+": {
        CONF_KEY_DEVICE: {"selection": ["mcp23008", "mcp23017"]},
        CONF_KEY_MCP: OrderedDict(
            [
                ("type", "section"),
                (
                    "conditions",
                    [(CONF_KEY_DEVICE, "mcp23008"), (CONF_KEY_DEVICE, "mcp23017")],
                ),
                (
                    "regex:.+",
                    {
                        "type": "section",
                        "required": False,
                        CONF_KEY_PIN: {"type": (int, list)},
                        CONF_KEY_NAME: {"type": (str, list), "default": "{pin_id}"},
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
                                "none": Resistor.OFF,
                            },
                        },
                        CONF_KEY_INVERT: {"type": bool, "default": False},
                        CONF_KEY_INITIAL: {
                            "selection": {
                                "ON": True,
                                "on": True,
                                "OFF": False,
                                "off": False,
                            },
                            "default": False,
                        },
                        CONF_KEY_FIRST_INDEX: {"type": int, "default": 0},
                    },
                ),
            ]
        ),
    }
}


# helpers to get/set bits
def _get_bit(val, bit):
    return val & (1 << bit) > 0


def _set_bit(val, bit, bit_val=1):
    return (val & ~(1 << bit)) | bit_val << bit


def _clear_bit(val, bit):
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
        invert: bool,
        initial: bool,
        device: I2CDevice,
    ):
        self._pin = pin
        self._id = id
        self._name = name
        self._direction = direction
        self._invert = invert
        self._device = device
        self._path = f"{self._device.id}/{self.id}"
        self._pulse_timer = None

        if direction == Direction.INPUT:
            if resistor == Resistor.PULL_UP:
                device._gppu = _set_bit(device._gppu, pin)
        else:
            device._iodir = _clear_bit(device._iodir, pin)
            self.state = initial

    def publish_state(self):
        state = self.state_log
        common.publish_queue.put_nowait(
            BusMessage(path=self._path, content=TEXT_STATE[state])
        )

    @property
    def state(self) -> bool:
        """
        Returns pin state as ``bool`` after applying invert flag
        """
        return bool(_get_bit(self._device._gpio, self._pin) ^ self._invert)

    @state.setter
    def state(self, value: bool):
        if self._direction == Direction.OUTPUT:
            self._device._gpio = _set_bit(
                self._device._gpio, self._pin, int(value) ^ self._invert
            )

    @property
    def state_log(self) -> bool:
        """
        Returns pin state as ``bool`` after applying invert flag and logs the event
        """
        state = self.state
        self._device._log.debug(
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
    def state_log(self, state: bool):
        if self._direction == Direction.OUTPUT:
            self._pulse_cancel()
            self.state = state
            self._device._log.debug(
                "Set pin GP%02d '%s' on %s '%s' to %s logic %s",
                self._pin,
                self._name,
                self._device.device,
                self._device.name,
                TEXT_STATE[state],
                Logic(int(state ^ self._invert)).name,
            )

    def _pulse(self, time: int, state: bool):
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
        self._device._write_gpio()
        self._pulse_timer = Timer(float(time) / 1000, self._pulse_end, args=[not state])
        self._pulse_timer.start()
        self.publish_state()

    def _pulse_end(self, state):
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
        self._device._write_gpio()
        self.publish_state()

    def _pulse_cancel(self):
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

    def set(self, content: str):
        """
        Handle a SET message
        """
        if self._direction == Direction.OUTPUT:
            state = str(resolve_type(content))
            if state in TEXT_STATE:
                self._pulse_cancel()
                self.state_log = TEXT_STATE[state]
                self._device._write_gpio()
                self.publish_state()
            else:
                self._device._log.warn(
                    "Received unrecognized SET message for pin GP%02d '%s' on %s '%s': %s",
                    self._pin,
                    self._name,
                    self._device.device,
                    self._device.name,
                    content,
                )
        else:
            self._device._log.warn(
                "Received SET command for pin GP%02d '%s' on %s '%s' but it is not "
                "configured as an output",
                self._pin,
                self._name,
                self._device.device,
                self._device.name,
            )

    def pulse(self, content: str):
        """
        Handle a PULSE message
        """
        if self._direction == Direction.OUTPUT:
            try:
                content = json.loads(content)
            except ValueError:
                self._device._log.warn(
                    "Received unrecognized PULSE command for pin GP%02d '%s' on %s '%s': %s",
                    self._pin,
                    self._name,
                    self._device.device,
                    self._device.name,
                    content,
                )
            else:
                time = content.get("time")
                state = content.get("state")
                if not time:
                    self._device._log.error(
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
                    self._device._read_gpio()
                    state = TEXT_STATE[self.state]
                else:
                    state = str(resolve_type(content))
                if state in TEXT_STATE:
                    self._pulse(time, TEXT_STATE[state])
                else:
                    self._device._log.warn(
                        "Received unrecognized PULSE state for pin GP%02d '%s' on %s '%s': %s",
                        self._pin,
                        self._name,
                        self._device.device,
                        self._device.name,
                        state,
                    )
        else:
            self._device._log.warn(
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
        bus,
        bus_path: str,
    ):
        super().__init__(id, name, device, address, bus, bus_path)
        self._pins = []
        self._pin_max = 0
        self._pin_from_path = {}
        self._gpio = None  # set by subclass

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
                    name=pin._name,
                    settable=pin._direction == Direction.OUTPUT,
                    callback="device_message",
                ),
            )
            node.add_property(str(pin._pin), node.properties[pin.id])
        return node

    def cleanup(self):
        """
        Perform cleanup on module shutdown.
        Subclasses may override this method
        """
        if self._setup:
            self._gpio = 0
            for pin in self._pins:
                if pin is not None:
                    pin.state = 0  # set all pins to configured OFF
            self._write_gpio()
            self.publish_state()
            self._setup = False

    def publish_state(self):
        """
        Publishes the state of all configured pins
        """
        if self._setup:
            self._log.debug("Polling all pins")
            self._read_gpio()
            for pin in self._pins:
                if pin is not None:
                    pin.publish_state()

    def message_callback(self, message: BusMessage) -> None:
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
                        self._pins[self._pin_from_path[path[0]]]._pin,
                        self._pins[self._pin_from_path[path[0]]].name,
                        message.content,
                    )
                else:
                    self._pins[self._pin_from_path[path[0]]].pulse(message.content)
            else:
                self._log.debug("Received message on unregistered path: %s", message)

    def _build_pins(self, device_config):
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
                        direction=pin_config[CONF_KEY_DIRECTION],
                        resistor=pin_config[CONF_KEY_RESISTOR],
                        invert=pin_config[CONF_KEY_INVERT],
                        initial=pin_config[CONF_KEY_INITIAL],
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
                            direction=pin_config[CONF_KEY_DIRECTION],
                            resistor=pin_config[CONF_KEY_RESISTOR],
                            invert=pin_config[CONF_KEY_INVERT],
                            initial=pin_config[CONF_KEY_INITIAL],
                        )

    def _setup_pin(
        self,
        pin: int,
        id: str,
        name: str,
        direction: Direction,
        resistor: Resistor,
        invert: bool,
        initial: bool,
    ):
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
                self._device.id,
                self._device,
                self._name,
                self._pins[pin].name,
            )
        elif pin > self._pin_max:
            self._log.warn(
                "Found pin GP%02d in '%s' for %s '%s' but highest pin for device is GP%02d",
                pin,
                id,
                self._device.id,
                self._name,
                self._pin_max,
            )
        else:
            self._pins[pin] = Pin(
                pin=pin,
                id=id,
                name=name,
                direction=direction,
                resistor=resistor,
                invert=invert,
                initial=initial,
                device=self,
            )
            self._pin_from_path[id] = pin
            self._log.debug(
                "Configured pin GP%02d '%s' on %s '%s' with options: %s",
                pin,
                name,
                self.device,
                self.name,
                {
                    "ID": id,
                    CONF_KEY_DIRECTION: direction.name,
                    CONF_KEY_RESISTOR: resistor.name,
                    CONF_KEY_INVERT: invert,
                    CONF_KEY_INITIAL: TEXT_STATE[initial],
                },
            )

    def _read_gpio(self):
        """
        Read the GP register(s)
        """
        raise NotImplementedError

    def _write_gpio(self):
        """
        Write the GP register(s)
        """
        raise NotImplementedError


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
        bus,
        bus_path: str,
        device_config: dict,
    ):
        super().__init__(id, name, device, address, bus, bus_path)
        self._log = logger.get_logger("i2c.mcp23008")
        self._pin_max = 7
        self._pins = [None] * (self._pin_max + 1)
        self._gpio = 0x0000
        self._iodir = 0xFFFF
        self._gppu = 0x0000
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
                    self._iodir,
                    0x00,  # IPOL
                    0x00,  # GPINTEN
                    0x00,  # DEFVAL
                    0x00,  # INTCON
                    0x04,  # IOCON
                    self._gppu,
                    0x00,  # INTF
                    0x00,  # INTCAP
                    self._gpio,
                ]
            ),
        ):
            self._setup = False

        return self._setup

    def _read_gpio(self):
        gpio = self._read_byte(self._GPIO)
        if gpio is not None:
            self._gpio = gpio

    def _write_gpio(self):
        self._write_byte(self._GPIO, self._gpio)


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
        bus,
        bus_path: str,
        device_config: dict,
    ):
        super().__init__(id, name, device, address, bus, bus_path)
        self._log = logger.get_logger("i2c.mcp23017")
        self._pin_max = 15
        self._pins = [None] * (self._pin_max + 1)
        self._gpio = 0x0000
        self._iodir = 0xFFFF
        self._gppu = 0x0000
        super()._build_pins(device_config)

    def setup(self):
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
                    self._iodir & 0xFF,  # IODIRA
                    self._iodir >> 8,  # IODIRB
                    0x00,  # IPOLA
                    0x00,  # IPOLB
                    0x00,  # GPINTENA
                    0x00,  # GPINTENB
                    0x00,  # DEFVALA
                    0x00,  # DEFVALB
                    0x00,  # INTCONA
                    0x00,  # INTCONB
                    0x04,  # IOCON
                    0x04,  # IOCON
                    self._gppu & 0xFF,  # GPPUA
                    self._gppu >> 8,  # GPPUB
                    0x00,  # INTFA
                    0x00,  # INTFB
                    0x00,  # INTCAPA
                    0x00,  # INTCAPB
                    self._gpio & 0xFF,  # GPIOA
                    self._gpio >> 8,  # GPIOB
                ]
            ),
        ):
            self._setup = False

        return self._setup

    def _read_gpio(self):
        gpio = self._read_word(self._GPIOA)
        if gpio is not None:
            self._gpio = gpio

    def _write_gpio(self):
        self._write_word(self._GPIOA, self._gpio)


SUPPORTED_DEVICES = {"mcp23008": MCP23008, "mcp23017": MCP23017}
