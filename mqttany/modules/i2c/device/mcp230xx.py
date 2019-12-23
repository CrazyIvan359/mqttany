"""
*******************
I2C Device MCP230xx
*******************
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

from collections import OrderedDict
from enum import Enum
import json
from threading import Timer

from common import Logic, Direction, Resistor, Interrupt
import logger
from modules.mqtt import publish, resolve_topic, topic_matches_sub
from modules.i2c.device.common import I2CDevice
from modules.i2c.common import config
from modules.i2c.common import *


__all__ = [ "SUPPORTED_DEVICES", "CONF_OPTIONS", "CONF_DEVICE_OPTIONS" ]

CONF_KEY_MCP = "mcp230xx"
CONF_KEY_TOPIC_SETTER = "topic set"
CONF_KEY_TOPIC_PULSE = "topic pulse"
CONF_KEY_PAYLOAD_ON = "payload on"
CONF_KEY_PAYLOAD_OFF = "payload off"
CONF_KEY_PIN = "pin"
CONF_KEY_DIRECTION = "direction"
CONF_KEY_RESISTOR = "resistor"
CONF_KEY_INVERT = "invert"
CONF_KEY_INITIAL = "initial state"
CONF_KEY_FIRST_INDEX = "first index"

CONF_OPTIONS = { # added to root config section
    CONF_KEY_TOPIC_SETTER: {"default": "set"},
    CONF_KEY_TOPIC_PULSE: {"type": str, "default": "pulse"},
    CONF_KEY_PAYLOAD_ON: {"default": "ON"},
    CONF_KEY_PAYLOAD_OFF: {"default": "OFF"},
}

CONF_DEVICE_OPTIONS = { # added to device definition section
    CONF_KEY_MCP: OrderedDict([
        ("regex:.+", {
            "type": "section",
            "required": False,
            CONF_KEY_PIN: {"type": (int, list)},
            CONF_KEY_TOPIC: {"type": (str, list), "default": "{pin}"},
            CONF_KEY_DIRECTION: {"default": Direction.INPUT, "selection": {"input": Direction.INPUT, "in": Direction.INPUT, "output": Direction.OUTPUT, "out": Direction.OUTPUT}},
            CONF_KEY_RESISTOR: {"default": Resistor.OFF, "selection": {"pullup": Resistor.PULL_UP, "up": Resistor.PULL_UP, "off": Resistor.OFF, "none": Resistor.OFF}},
            CONF_KEY_INVERT: {"type": bool, "default": False},
            CONF_KEY_INITIAL: {"default": "{payload_off}"},
            CONF_KEY_FIRST_INDEX: {"type": int, "default": 0},
        })
    ])
}

TEXT_NAME = ".".join([__name__.split(".")[-3], __name__.split(".")[-1]]) # gives i2c.mcp230xx

PAYLOAD_LOOKUP = {}


# helpers to get/set bits
def _get_bit(val, bit):
    return val & (1 << bit) > 0
def _set_bit(val, bit, bit_val=1):
    return ( ( val & ~(1 << bit) ) | bit_val << bit )
def _clear_bit(val, bit):
    return val & ~(1 << bit)


class Pin(object):
    """
    Device Pin class
    """

    def __init__(self, pin, name, topic, direction, resistor, invert, initial, device):
        self.pin = pin
        self.name = name
        self.topic = topic
        self.direction = direction
        self.invert = invert
        self._device = device
        self._pulse_timer = None
        if direction == Direction.INPUT:
            if resistor == Resistor.PULL_UP:
                device._gppu = _set_bit(device._gppu, pin)
        else:
            device._iodir = _clear_bit(device._iodir, pin)
            if initial in PAYLOAD_LOOKUP:
                self.state_payload = initial
            else:
                self._device.log.warn("Invalid initial state '{state}' for '{pin_name}' on GP{pin:02d} on {device} '{device_name}'".format(
                    state=initial, pin_name=name, pin=pin,
                    device=device.device, device_name=device.name))
                self.state = 0

    def publish_state(self):
        """ Publish pin state """
        publish(self.topic, self.state_payload)

    @property
    def state(self):
        """ Pin state as ``int`` after applying invert flag """
        return self.state_logic ^ self.invert

    @state.setter
    def state(self, value):
        self.state_logic = int(value) ^ self.invert

    @property
    def state_logic(self):
        """ Raw pin state """
        return _get_bit(self._device._gpio, self.pin)

    @state_logic.setter
    def state_logic(self, value):
        if self.direction == Direction.INPUT: return
        self._device._gpio = _set_bit(self._device._gpio, self.pin, int(value))

    @property
    def state_payload(self):
        """ Pin state as one of ``payload_on`` or ``payload_off`` """
        self._device.log.debug("Read state '{state}' logic {logic} from GP{pin:02d} on {device} '{device_name}'".format(
            state=PAYLOAD_LOOKUP[self.state], logic=Logic(self.state).name,
            pin=self.pin, device=self._device.device, device_name=self._device.name))
        return PAYLOAD_LOOKUP[self.state]

    @state_payload.setter
    def state_payload(self, payload):
        if self.direction == Direction.INPUT: return
        if payload in PAYLOAD_LOOKUP:
            if self._pulse_timer is not None:
                self._pulse_timer.cancel()
                self._pulse_timer = None
                self._device.log.debug("Cancelled PULSE timer for '{pin_name}' on GP{pin:02d} on {device} '{device_name}'".format(
                    pin_name=self.name, pin=self.pin,
                    device=self._device.device, device_name=self._device.name))

            self.state = PAYLOAD_LOOKUP[payload]
            self._device.log.debug("Set state '{state}' logic {logic} on GP{pin:02d} on {device} '{device_name}'".format(
                state=PAYLOAD_LOOKUP[self.state], logic=Logic(self.state).name,
                pin=self.pin, device=self._device.device, device_name=self._device.name))
            self.publish_state()

        else:
            self._device.log.warn("Received unrecognized SET payload '{payload}' for '{pin_name}' on GP{pin:02d} on {device} '{device_name}'".format(
                payload=payload, pin_name=self.name, pin=self.pin,
                device=self._device.device, device_name=self._device.name))

    def pulse(self, payload):
        """
        Handle a PULSE message
        """
        if self.direction == Direction.INPUT: return

        # JSON payload
        if "{" in payload:
            try:
                payload = json.loads(payload)
            except ValueError:
                self._device.log.error("Received malformed JSON '{payload}' for PULSE for '{pin_name}' on GP{pin:02d} on {device} '{device_name}'".format(
                    payload=payload, pin_name=self.name, pin=self.pin,
                    device=self._device.device, device_name=self._device.name))
                return
            else:
                if not "time" in payload:
                    self._device.log.error("Received JSON PULSE command missing 'time' argument for '{pin_name}' on GP{pin:02d} on {device} '{device_name}'".format(
                        pin_name=self.name, pin=self.pin,
                        device=self._device.device, device_name=self._device.name))
                    return
                if not "state" in payload:
                    payload["state"] = self.state
                    if payload["state"] is not None:
                        payload["state"] = not payload["state"]
                    else:
                        self._device.log.error("PULSE failed, unable to read pin state for '{pin_name}' on GP{pin:02d} on {device} '{device_name}'".format(
                            pin_name=self.name, pin=self.pin,
                            device=self._device.device, device_name=self._device.name))
                        return

        # List payload "time, state"
        elif len(payload.split(",")) > 1:
            if len(payload.split(",")) != 2:
                self._device.log.error("Received unrecognized PULSE command '{payload}' for '{pin_name}' on GP{pin:02d} on {device} '{device_name}'".format(
                    payload=payload, pin_name=self.name, pin=self.pin,
                    device=self._device.device, device_name=self._device.name))
                return
            payload = {
                "time": resolve_type(payload.split(",")[0].strip()),
                "state": payload.split(",")[1].strip()
            }
            if not isinstance(payload["time"], int):
                self._device.log.error("Received invalid time '{time}' for PULSE command for '{pin_name}' on GP{pin:02d} on {device} '{device_name}'".format(
                    time=payload["time"], pin_name=self.name, pin=self.pin,
                    device=self._device.device, device_name=self._device.name))
                return

        # Time only payload
        else:
            payload = {"time": resolve_type(payload)}
            if not isinstance(payload["time"], int):
                self._device.log.error("Received invalid time '{time}' for PULSE command for '{pin_name}' on GP{pin:02d} on {device} '{device_name}'".format(
                    time=payload["time"], pin_name=self.name, pin=self.pin,
                    device=self._device.device, device_name=self._device.name))
                return
            payload["state"] = self.state
            if payload["state"] is not None:
                payload["state"] = not payload["state"]
            else:
                self._device.log.error("PULSE failed, unable to read pin state for '{pin_name}' on GP{pin:02d} on {device} '{device_name}'".format(
                    pin_name=self.name, pin=self.pin,
                    device=self._device.device, device_name=self._device.name))
                return

        if isinstance(payload["state"], str):
            if payload["state"] in PAYLOAD_LOOKUP:
                payload["state"] = PAYLOAD_LOOKUP[payload["state"]]
            else:
                self._device.log.error("Received unrecognized state '{state}' for PULSE command for '{pin_name}' on GP{pin:02d} on {device} '{device_name}'".format(
                    state=payload["state"], pin_name=self.name, pin=self.pin,
                    device=self._device.device, device_name=self._device.name))
                return

        self._device.log.debug("Pulsing '{pin_name}' on GP{pin:02d} on {device} '{device_name}' to '{state}' logic {logic} for {time}ms".format(
            pin_name=self.name, pin=self.pin, device=self._device.device,
            device_name=self._device.name, logic=Logic(self.state_logic).name,
            state=PAYLOAD_LOOKUP[self.state], time=payload["time"]))

        self.state = payload["state"]
        self._device._write_gpio()
        if self._pulse_timer is not None:
            self._pulse_timer.cancel()
            self._pulse_timer = None
            self._device.log.debug("Cancelled PULSE timer for '{pin_name}' on GP{pin:02d} on {device} '{device_name}'".format(
                pin_name=self.name, pin=self.pin,
                device=self._device.device, device_name=self._device.name))

        self._pulse_timer = Timer(
            float(payload["time"]) / 1000,
            self._pulse_end,
            args=[not payload["state"]]
        )
        self._pulse_timer.start()
        self.publish_state()

    def _pulse_end(self, state):
        """
        End of a pulse cycle, set pin to state and log
        """
        self._pulse_timer = None
        self.state = state
        self._device._write_gpio()
        self._device.log.debug("PULSE ended for '{pin_name}' on GP{pin:02d} on {device} '{device_name}' set pin to '{state}' logic {logic}".format(
            pin_name=self.name, pin=self.pin,
            device=self._device.device, device_name=self._device.name,
            logic=Logic(self.state_logic).name,
            state=PAYLOAD_LOOKUP[self.state]))
        self.publish_state()


class MCP230xx(I2CDevice):
    """
    Base class for MCP23008 and MCP23017 GPIO Expanders
    """

    def __init__(self, name, address, device, bus_path, bus, topic, device_config):
        super().__init__(name, address, device, bus_path, bus, topic, self.log)
        PAYLOAD_LOOKUP[config[CONF_KEY_PAYLOAD_ON]] = 1
        PAYLOAD_LOOKUP[1] = config[CONF_KEY_PAYLOAD_ON]
        PAYLOAD_LOOKUP[config[CONF_KEY_PAYLOAD_OFF]] = 0
        PAYLOAD_LOOKUP[0] = config[CONF_KEY_PAYLOAD_OFF]

        # Setup device pins from config
        for pin_name in [key for key in device_config[CONF_KEY_MCP] if isinstance(device_config[CONF_KEY_MCP][key], dict)]:
            pin_config = device_config[CONF_KEY_MCP].pop(pin_name)
            if isinstance(pin_config[CONF_KEY_PIN], int): # Single pin definition
                if not isinstance(pin_config[CONF_KEY_TOPIC], str):
                    self.log.error("Failed to configure pin group '{pin_name}' for {device} '{device_name}'. Single pin definitions can have only 1 topic".format(
                        pin_name=pin_name, device=self.device, device_name=self.name))
                else:
                    self._setup_pin(
                        pin=pin_config[CONF_KEY_PIN],
                        pin_name=pin_name,
                        pin_topic=pin_config[CONF_KEY_TOPIC],
                        direction=pin_config[CONF_KEY_DIRECTION],
                        resistor=pin_config[CONF_KEY_RESISTOR],
                        invert=pin_config[CONF_KEY_INVERT],
                        initial=pin_config[CONF_KEY_INITIAL],
                    )
            elif isinstance(pin_config[CONF_KEY_PIN], list): # Multiple pin definition
                if isinstance(pin_config[CONF_KEY_TOPIC], list) \
                        and len(pin_config[CONF_KEY_PIN]) != len(pin_config[CONF_KEY_TOPIC]):
                    self.log.error("Failed to configure pin group '{pin_name}' for {device} '{device_name}'. "
                              "There are {pins} and {topics}, must have the same number".format(
                        pin_name=pin_name, device=self.device, device_name=self.name,
                        pins=len(pin_config[CONF_KEY_PIN]), topics=len(pin_config[CONF_KEY_TOPIC])))
                else:
                    for index in range(len(pin_config[CONF_KEY_PIN])):
                        self._setup_pin(
                            pin=pin_config[CONF_KEY_PIN][index],
                            pin_name=pin_name,
                            pin_topic=pin_config[CONF_KEY_TOPIC][index] if isinstance(pin_config[CONF_KEY_TOPIC], list) else pin_config[CONF_KEY_TOPIC],
                            direction=pin_config[CONF_KEY_DIRECTION],
                            resistor=pin_config[CONF_KEY_RESISTOR],
                            invert=pin_config[CONF_KEY_INVERT],
                            initial=pin_config[CONF_KEY_INITIAL],
                            index_sub=index + pin_config[CONF_KEY_FIRST_INDEX]
                        )

    def cleanup(self):
        """
        Perform cleanup on module shutdown.
        Subclasses may override this method
        """
        self._gpio = 0
        for pin in self._pins:
            if pin is None: continue
            pin.state = 0 # set all pins to configured OFF
        self._write_gpio()

    def _setup_pin(self, pin, pin_name, pin_topic, direction, resistor, invert, initial, index_sub=""):
        """
        Setup pin for given options
        """
        if self._pins[pin] is not None:
            self.log.warn("Duplicate configuration for GP{pin:02d} found in '{pin_name}' for {device} '{device_name}' will be ignored, pin already configured under '{original}'".format(
                    pin=pin, pin_name=pin_name, device=self.device,
                    device_name=self._name, original=self._pins[pin].name))
        elif pin > self._pin_max:
            self.log.warn("Found pin GP{pin:02d} in '{pin_name}' for '{device_name}' but highest pin for '{device}' is GP{max}".format(
                    pin=pin, pin_name=pin_name, device_name=self._name, device=self._device, max=self._pin_max))
        else:
            self._pins[pin] = Pin(
                pin=pin,
                name=pin_name,
                topic=resolve_topic(
                    pin_topic,
                    subtopics=["{module_topic}", "{device_topic}"],
                    substitutions={
                        "module_topic": config[CONF_KEY_TOPIC],
                        "module_name": TEXT_PACKAGE_NAME,
                        "device_topic": self._topic,
                        "address": self._address,
                        "device_name": self._name,
                        "pin_name": pin_name,
                        "pin": pin,
                        "index": index_sub
                    }
                ),
                direction=direction,
                resistor=resistor,
                invert=invert,
                initial=initial.format(
                    payload_on=config[CONF_KEY_PAYLOAD_ON], payload_off=config[CONF_KEY_PAYLOAD_OFF]
                ),
                device=self
            )
            self.log.debug("Configured '{pin_name}' on GP{pin:02d} on {device} '{device_name}' with options: {options}".format(
                    pin_name=pin_name, pin=pin, device=self._device, device_name=self._name,
                    options={"direction": direction.name, "resistor": resistor.name, "invert": invert}))

    def publish_state(self):
        """
        Publishes the state of all configured pins
        """
        if not self._setup: return
        self._read_gpio()
        for pin in self._pins:
            if pin is None: continue
            pin.publish_state()

    def handle_message(self, topic, payload):
        """
        Handle messages to any of this device's subscriptions.
        """
        if not self._setup: return
        if topic_matches_sub("{}/{}".format(self._topic, config[CONF_KEY_TOPIC_GETTER]), topic):
            self.publish_state()
        else:
            for pin in self._pins:
                if pin is None: continue
                if topic_matches_sub("{}/+".format(pin.topic), topic):
                    if topic_matches_sub("{}/{}".format(pin.topic, config[CONF_KEY_TOPIC_SETTER]), topic):
                        pin.state_payload = payload.decode("utf-8")
                        self._write_gpio()
                        break
                    elif topic_matches_sub("{}/{}".format(pin.topic, config[CONF_KEY_TOPIC_PULSE]), topic):
                        pin.pulse(payload.decode("utf-8"))
                        break
                    elif topic_matches_sub("{}/{}".format(pin.topic, config[CONF_KEY_TOPIC_GETTER]), topic):
                        self._read_gpio()
                        pin.publish_state()
                        break

    def get_subscriptions(self):
        """
        Return all device and pin topics to subscribe to
        """
        topics = super().get_subscriptions()
        for pin in self._pins:
            if pin is None: continue
            topics.append("{}/{}".format(pin.topic, config[CONF_KEY_TOPIC_GETTER]))
            if pin.direction == Direction.OUTPUT:
                topics.append("{}/{}".format(pin.topic, config[CONF_KEY_TOPIC_SETTER]))
                topics.append("{}/{}".format(pin.topic, config[CONF_KEY_TOPIC_PULSE]))
        return topics

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

    log = logger.get_module_logger(module=".".join([__name__.split(".")[-3], "mcp23008"]))
    _pin_max = 7

    # Device Registers
    _IODIR   = 0x00 # Direction
    _IPOL    = 0x01 # Input Polarity (Invert)
    _GPINTEN = 0x02 # Interrupt Enable
    _DEFVAL  = 0x03 # Default Compare Value
    _INTCON  = 0x04 # Interrupt Control
    _IOCON   = 0x05 # I/O Configuration
    _GPPU    = 0x06 # Pull Up
    _INTF    = 0x07 # Interrupt Flag
    _INTCAP  = 0x08 # Interrupt Capture
    _GPIO    = 0x09 # GPIO
    _OLAT    = 0x0A # Output Latch

    def __init__(self, name, address, device, bus_path, bus, topic, device_config):
        self._pins = [None] * self._pin_max + 1
        self._gpio = 0x0000
        self._iodir = 0xFFFF
        self._gppu = 0x0000
        super().__init__(name, address, device, bus_path, bus, topic, device_config)

    def setup(self):
        """
        Setup the hardware
        """
        if not super().setup():
            return False

        self._setup = True
        self.log.debug("Writing initial values to registers of {device} '{name}' at address 0x{address:02x} on bus '{bus}'".format(
            device=self._device, name=self._name, address=self._address, bus=self._bus_path))
        if not self._write_block(0x00,
                    bytes([
                        self._iodir,
                        0x00, # IPOL
                        0x00, # GPINTEN
                        0x00, # DEFVAL
                        0x00, # INTCON
                        0x04, # IOCON
                        self._gppu,
                        0x00, # INTF
                        0x00, # INTCAP
                        self._gpio
                    ])
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

    log = logger.get_module_logger(module=".".join([__name__.split(".")[-3], "mcp23017"]))
    _pin_max = 15

    # Device Registers
    _IODIRA   = 0x00 # Direction
    _IODIRB   = 0x01
    _IPOLA    = 0x02 # Input Polarity (Invert)
    _IPOLB    = 0x03
    _GPINTENA = 0x04 # Interrupt Enable
    _GPINTENB = 0x05
    _DEFVALA  = 0x06 # Default Compare Value
    _DEFVALB  = 0x07
    _INTCONA  = 0x08 # Interrupt Control
    _INTCONB  = 0x09
    _IOCON    = 0x0A # I/O Configuration
    #IOCON    = 0x0B # duplicate address
    _GPPUA    = 0x0C # Pull Up
    _GPPUB    = 0x0D
    _INTFA    = 0x0E # Interrupt Flag
    _INTFB    = 0x0F
    _INTCAPA  = 0x10 # Interrupt Capture
    _INTCAPB  = 0x11
    _GPIOA    = 0x12 # GPIO
    _GPIOB    = 0x13
    _OLATA    = 0x14 # Output Latch
    _OLATB    = 0x15

    def __init__(self, name, address, device, bus_path, bus, topic, device_config):
        self._pins = [None] * self._pin_max + 1
        self._gpio = 0x0000
        self._iodir = 0xFFFF
        self._gppu = 0x0000
        super().__init__(name, address, device, bus_path, bus, topic, device_config)

    def setup(self):
        """
        Setup the hardware
        """
        if not super().setup():
            return False

        self._setup = True
        self.log.debug("Writing initial values to registers of {device} '{name}' at address 0x{address:02x} on bus '{bus}'".format(
            device=self._device, name=self._name, address=self._address, bus=self._bus_path))
        if not self._write_block(0x00,
                    bytes([
                        self._iodir & 0xFF, # IODIRA
                        self._iodir >> 8,   # IODIRB
                        0x00,               # IPOLA
                        0x00,               # IPOLB
                        0x00,               # GPINTENA
                        0x00,               # GPINTENB
                        0x00,               # DEFVALA
                        0x00,               # DEFVALB
                        0x00,               # INTCONA
                        0x00,               # INTCONB
                        0x04,               # IOCON
                        0x04,               # IOCON
                        self._gppu & 0xFF,  # GPPUA
                        self._gppu >> 8,    # GPPUB
                        0x00,               # INTFA
                        0x00,               # INTFB
                        0x00,               # INTCAPA
                        0x00,               # INTCAPB
                        self._gpio & 0xFF,  # GPIOA
                        self._gpio >> 8     # GPIOB
                    ])
                ):
            self._setup = False

        return self._setup

    def _read_gpio(self):
        gpio = self._read_word(self._GPIOA)
        if gpio is not None:
            self._gpio = gpio

    def _write_gpio(self):
        self._write_word(self._GPIOA, self._gpio)


SUPPORTED_DEVICES = {
    "mcp23008": MCP23008,
    "mcp23017": MCP23017
}
