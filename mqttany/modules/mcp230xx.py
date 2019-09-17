"""
***************
MCP230xx Module
***************

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

import time, sys
from threading import Timer
from collections import OrderedDict

import busio, microcontroller
from adafruit_blinka.agnostic import board_id, detector
from adafruit_mcp230xx.mcp23008 import MCP23008
from adafruit_mcp230xx.mcp23017 import MCP23017
from digitalio import Direction, Pull

import logger
from config import parse_config
from common import acquire_i2c_lock, release_i2c_lock
from modules.mqtt import resolve_topic, topic_matches_sub, publish, subscribe

all = [  ]

CONF_KEY_TOPIC = "topic"
CONF_KEY_TOPIC_SETTER = "topic set"
CONF_KEY_TOPIC_GETTER = "topic get"
CONF_KEY_PAYLOAD_ON = "payload on"
CONF_KEY_PAYLOAD_OFF = "payload off"
CONF_KEY_POLL_INT = "polling interval"
CONF_KEY_BUS_ID = "bus id"
CONF_KEY_ADDRESS = "address"
CONF_KEY_CHIP = "chip"
CONF_KEY_PIN = "pin"
CONF_KEY_FIRST_INDEX = "first index"
CONF_KEY_DIRECTION = "direction"
CONF_KEY_RESISTOR = "resistor"
CONF_KEY_INVERT = "invert"
CONF_KEY_INITIAL = "initial state"
CONF_OPTIONS = OrderedDict([
    (CONF_KEY_TOPIC, {"default": "{module_name}"}),
    (CONF_KEY_TOPIC_SETTER, {"default": "set"}),
    (CONF_KEY_TOPIC_GETTER, {"default": "poll"}),
    (CONF_KEY_PAYLOAD_ON, {"default": "ON"}),
    (CONF_KEY_PAYLOAD_OFF, {"default": "OFF"}),
    (CONF_KEY_POLL_INT, {"type": float, "default": 0.0}),
    ("regex:.+", OrderedDict([
        ("type", "section"),
        ("required", False),
        (CONF_KEY_BUS_ID, {}),
        (CONF_KEY_ADDRESS, {"type": int, "selection": [0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27]}), # '{address:02x}' address in hex, 0 padded 2 chars
        (CONF_KEY_CHIP, {"selection": {"mcp23008": "MCP23008", "MCP23008": "MCP23008", "23008": "MCP23008", "mcp23017": "MCP23017", "MCP23017": "MCP23017", "23017": "MCP23017"}}),
        (CONF_KEY_TOPIC, {"default": "{device_name}"}),
        ("regex:.+", {
            "type": "section",
            "required": False,
            CONF_KEY_PIN: {"type": (int, list)},
            CONF_KEY_TOPIC: {"type": (str, list), "default": "{pin}"},
            CONF_KEY_FIRST_INDEX: {"type": int, "default": 0},
            CONF_KEY_DIRECTION: {"default": Direction.INPUT, "selection": {"input": Direction.INPUT, "in": Direction.INPUT, "output": Direction.OUTPUT, "out": Direction.OUTPUT}},
            CONF_KEY_RESISTOR: {"default": "off", "selection": {"pullup": Pull.UP, "up": Pull.UP, "off": "off", "none": "off"}},
            CONF_KEY_INVERT: {"type": bool, "default": False},
            CONF_KEY_INITIAL: {"default": "{payload_off}"},
        })
    ]))
])

TEXT_NAME = __name__.split(".")[-1]
TEXT_DIRECTION = {Direction.INPUT: "input", Direction.OUTPUT: "output"}
TEXT_RESISTOR = {Pull.UP: "up", "off": "off"}
TEXT_LOGIC_STATE = ["LOW", "HIGH"]

DEVICE_PIN_MAX = {"MCP23008": 7, "MCP23017": 15}

log = logger.get_module_logger()
queue = None
polling_timer = None
buses = {}
devices = []
config = {}


def init(config_data={}):
    """
    Initializes the module
    """
    def build_pin(name, pin_config, pin=None, index=0):
        if pin is None:
            if isinstance(pin_config[CONF_KEY_PIN], list):
                pin = pin_config[CONF_KEY_PIN][index]
                index_sub = index + pin_config[CONF_KEY_FIRST_INDEX]
            else:
                pin = pin_config[CONF_KEY_PIN]
                index_sub = ""
        if isinstance(pin_config[CONF_KEY_TOPIC], list):
            topic = pin_config[CONF_KEY_TOPIC][index]
        else:
            topic = pin_config[CONF_KEY_TOPIC]
        return {
                "name": name.format(index=index + pin_config[CONF_KEY_FIRST_INDEX]),
                CONF_KEY_TOPIC: resolve_topic(
                        topic,
                        subtopics=["{module_topic}", "{device_topic}"],
                        substitutions={
                            "module_topic": raw_config[CONF_KEY_TOPIC],
                            "module_name": TEXT_NAME,
                            "device_topic": device_config[CONF_KEY_TOPIC],
                            "bus_id": device_config[CONF_KEY_BUS_ID],
                            "address": device_config[CONF_KEY_ADDRESS],
                            "device_name": device_config["name"],
                            "pin_name": name,
                            "pin": pin,
                            "index": index_sub
                        }
                    ),
                CONF_KEY_DIRECTION: pin_config[CONF_KEY_DIRECTION],
                #CONF_KEY_INTERRUPT: pin_config[CONF_KEY_INTERRUPT], # not yet supported
                CONF_KEY_RESISTOR: pin_config[CONF_KEY_RESISTOR],
                CONF_KEY_INVERT: pin_config[CONF_KEY_INVERT],
                CONF_KEY_INITIAL: pin_config[CONF_KEY_INITIAL].format(
                        payload_on=raw_config[CONF_KEY_PAYLOAD_ON], payload_off=raw_config[CONF_KEY_PAYLOAD_OFF])
            }

    if detector.board.any_raspberry_pi_40_pin:
        import adafruit_blinka.microcontroller.bcm283x.pin as mc_pins
        for bus in mc_pins.i2cPorts:
            buses[bus[0]] = {
                    "id": bus[0],
                    "scl": bus[1],
                    "sda": bus[2],
                    "devices": [] # list of used addresses
                }
    else:
        log.error("Unsupported Board {board}".format(board=board_id))
        return False
    log.debug("Board is {board}".format(board=board_id))

    raw_config = parse_config(config_data, CONF_OPTIONS, log)
    if raw_config:
        log.debug("Config loaded")

        for device_name in [key for key in raw_config if isinstance(raw_config[key], dict)]:
            device_config = raw_config.pop(device_name)
            device_config["name"] = device_name
            if device_config[CONF_KEY_BUS_ID] in buses:
                if device_config[CONF_KEY_ADDRESS] in buses[device_config[CONF_KEY_BUS_ID]]["devices"]:
                    log.warn("Duplicate configuration '{device_name}' found for device at address 0x{address:02x} on I2C bus '{bus_id}' will be ignored, address already configured under '{original}'".format(
                            device_name=device_name, address=device_config[CONF_KEY_ADDRESS],
                            bus_id=device_config[CONF_KEY_BUS_ID], original=[dev for dev in devices if dev[CONF_KEY_ADDRESS]==device_config[CONF_KEY_ADDRESS]][0]["name"]))
                else:
                    buses[device_config[CONF_KEY_BUS_ID]]["used"] = True
                    buses[device_config[CONF_KEY_BUS_ID]]["devices"].append(device_config[CONF_KEY_ADDRESS])
                    device_pins = {}
                    for pin_name in [key for key in device_config if isinstance(device_config[key], dict)]:
                        pin_config = device_config.pop(pin_name)
                        if isinstance(pin_config[CONF_KEY_PIN], int):
                            pin = pin_config[CONF_KEY_PIN]
                            if pin in device_pins:
                                log.warn("Duplicate configuration for GP{pin:02d} found in '{pin_name}' for '{device_name}' will be ignored, pin already configured under '{original}'".format(
                                        pin=pin, pin_name=pin_name, device_name=device_name, original=device_pins[pin]["name"]))
                            elif pin > DEVICE_PIN_MAX[device_config[CONF_KEY_CHIP]]:
                                log.warn("Found pin GP{pin:02d} in '{pin_name}' for '{device_name}' but highest pin for {device} is GP{max}".format(
                                        pin=pin, pin_name=pin_name, device_name=device_name, device=device_config[CONF_KEY_CHIP], max=DEVICE_PIN_MAX[device_config[CONF_KEY_CHIP]]))
                            else:
                                device_pins[pin] = build_pin(pin_name, pin_config)
                                log.debug("Configured GP{pin:02d} on {device} at address 0x{address:02x} with options: {options}".format(
                                        pin=pin, device=device_config[CONF_KEY_CHIP], address=device_config[CONF_KEY_ADDRESS], options=device_pins[pin]))
                        elif isinstance(pin_config[CONF_KEY_PIN], list):
                            for index in range(len(pin_config[CONF_KEY_PIN])):
                                pin = pin_config[CONF_KEY_PIN][index]
                                if pin in device_pins:
                                    log.warn("Duplicate configuration for GP{pin:02d} found in '{pin_name}' for '{device_name}' will be ignored, pin already configured under '{original}'".format(
                                            pin=pin, pin_name=pin_name, device_name=device_name, original=device_pins[pin]["name"]))
                                elif pin > DEVICE_PIN_MAX[device_config[CONF_KEY_CHIP]]:
                                    log.warn("Found pin GP{pin:02d} in '{pin_name}' for '{device_name}' but highest pin for {device} is GP{max}".format(
                                            pin=pin, pin_name=pin_name, device_name=device_name, device=device_config[CONF_KEY_CHIP], max=DEVICE_PIN_MAX[device_config[CONF_KEY_CHIP]]))
                                else:
                                    device_pins[pin] = build_pin(pin_name, pin_config, index=index)
                                    log.debug("Configured GP{pin:02d} on '{device}' at address 0x{address:02x} with options: {options}".format(
                                            pin=pin, device=device_config[CONF_KEY_CHIP], address=device_config[CONF_KEY_ADDRESS], options=device_pins[pin]))
                    device_config["bus"] = buses[device_config[CONF_KEY_BUS_ID]]
                    device_config["pins"] = device_pins
                    devices.append(device_config)
            else:
                log.error("Invalid bus id '{bus_id}' for device '{name}'".format(
                        bus_id=device_config[CONF_KEY_BUS_ID], name=device_name))

        config.update(raw_config)
        return True
    else:
        log.error("Error loading config")
        return False


def pre_loop():
    """
    Actions to be done in the subprocess before the loop starts
    """
    log.debug("Setting up hardware")
    for bus_id in buses:
        bus = buses[bus_id]
        if bus.get("used", False):
            log.debug("Initializing I2C bus '{bus_id}'".format(bus_id=bus_id))
            try:
                bus["busio"] = busio.I2C(bus["scl"], bus["sda"])
            except Exception as err:
                log.error("Error while setting up I2C bus '{bus_id}': {error}".format(
                        bus_id=bus_id, error=err))
                bus.pop("busio", None)
            else:
                log.debug("Successfully initialized I2C bus '{bus_id}'".format(bus_id=bus_id))

    for device in devices:
        init_device(device)

    log.debug("Adding MQTT subscription to poll all devices topic")
    subscribe(
            config[CONF_KEY_TOPIC_GETTER],
            callback=callback_poll_all,
            subtopics=["{module_topic}"],
            substitutions={
                "module_topic": config[CONF_KEY_TOPIC],
                "module_name": TEXT_NAME,
            }
        )

    if config[CONF_KEY_POLL_INT] > 0:
        log.debug("Starting polling timer with interval of {interval}s".format(
                interval=config[CONF_KEY_POLL_INT]))
        global polling_timer
        polling_timer = Timer(config[CONF_KEY_POLL_INT], poll_interval)
        polling_timer.start()

    log.debug("Publishing initial pin states")
    poll_all()


def post_loop():
    """
    Actions to be done in the subprocess after the loop is exited
    """
    if config[CONF_KEY_POLL_INT] > 0 and polling_timer is not None:
        log.debug("Stopping polling timer")
        polling_timer.cancel()


def get_pin_for_topic(topic):
    """
    Get the device and pin matching a topic
    """
    # attempt to determine device from device topic
    for device in devices:
        #log.trace("Comparing '{device_name}' topic '{device_topic}' to message topic '{topic}'".format(
        #        device_name=device["name"], device_topic=device[CONF_KEY_TOPIC].strip("/")+"/#", topic=topic))
        if topic_matches_sub(device[CONF_KEY_TOPIC]+"/#", topic):
            log.debug("Inferred device '{device_name}' from message topic '{topic}'".format(
                    device_name=device["name"], topic=topic))
            break
        device = None

    if device is None: # no device topic match
        # attempt to match topic to pin topic
        for device in devices:
            for pin in device["pins"]:
                pin_config = device["pins"][pin]
                #log.trace("Comparing pin '{pin_name}' GP{pin:02d} on '{device_name}' topic '{pin_topic}' to message topic '{topic}'".format(
                #        pin_name=pin_config["name"], pin=pin, device_name=device["name"],
                #        pin_topic=pin_config[CONF_KEY_TOPIC].strip("/")+"/+", topic=topic))
                if topic_matches_sub(pin_config[CONF_KEY_TOPIC]+"/+", topic):
                    log.debug("Found '{pin_name}' GP{pin:02d} on '{device_name}' for message topic '{topic}'".format(
                            pin_name=pin_config["name"], pin=pin, device_name=device["name"], topic=topic))
                    break
                pin = None
            if pin is not None:
                break
            device = None
    else: # device match found
        for pin in device["pins"]:
            pin_config = device["pins"][pin]
            #log.trace("Comparing pin '{pin_name}' GP{pin:02d} on '{device_name}' topic '{pin_topic}' to message topic '{topic}'".format(
            #        pin_name=pin_config["name"], pin=pin, device_name=device["name"],
            #        pin_topic=pin_config[CONF_KEY_TOPIC].strip("/")+"/+", topic=topic))
            if topic_matches_sub(pin_config[CONF_KEY_TOPIC]+"/+", topic):
                log.debug("Found '{pin_name}' GP{pin:02d} on '{device_name}' for message topic '{topic}'".format(
                        pin_name=pin_config["name"], pin=pin, device_name=device["name"], topic=topic))
                break
            pin = None

    return device, pin


def callback_setter(client, userdata, message):
    """
    Callback for setters
    """
    queue.put_nowait({
        "func": "_callback_setter",
        "args": [message.topic, message.payload.decode("utf-8")]
    })

def _callback_setter(topic, payload):
    device, pin = get_pin_for_topic(topic)

    if device is not None and pin is not None:
        set_pin(device, pin, payload)
    else:
        log.debug("Could not find device and pin match for SET on topic '{topic}'".format(
                topic=topic))


def callback_getter(client, userdata, message):
    """
    Callback for getters
    """
    queue.put_nowait({
        "func": "_callback_getter",
        "args": [message.topic]
    })

def _callback_getter(topic):
    device, pin = get_pin_for_topic(topic)

    if device is not None and pin is not None:
        get_pin(device, pin)
    else:
        log.debug("Could not find device and pin match for GET on topic '{topic}'".format(
                topic=topic))


def callback_poll_device(client, userdata, message):
    """
    Callback for poll all
    """
    queue.put_nowait({
        "func": "_callback_poll_device",
        "args": [message.topic]
    })


def callback_poll_all(client, userdata, message):
    """
    Callback for poll all
    """
    queue.put_nowait({
        "func": "poll_all"
    })


# helpers to get/set bits
def _get_bit(val, bit):
    return val & (1 << bit) > 0
def _set_bit(val, bit, bit_val=1):
    return ( ( val & ~(1 << bit) ) | bit_val << bit )
def _clear_bit(val, bit):
    return val & ~(1 << bit)


def init_device(device):
    bus = device["bus"]

    if bus.get("busio", False):
        log.info("Initializing '{device_name}'".format(device_name=device["name"]))
        log.info("Initializing {device} at address 0x{address:02x} on I2C bus '{bus_id}'".format(
                device=device[CONF_KEY_CHIP], address=device["address"], bus_id=bus["id"]))
        if acquire_i2c_lock(bus["id"], bus["scl"].id, bus["sda"].id, TEXT_NAME, timeout=5000):
            try:
                clazz = getattr(sys.modules[__name__], device[CONF_KEY_CHIP])
                device["device"] = clazz(bus["busio"], device["address"])

            except ValueError:
                log.error("'{device_name}' was not found on I2C bus '{bus_id}' at address 0x{address:02x}".format(
                        device_name=device["name"], address=device["address"], bus_id=bus["id"]))
                device.pop("device", None)

            else:
                log.debug("Adding MQTT subscription to device poll topic")
                subscribe(
                        config[CONF_KEY_TOPIC_GETTER],
                        callback=callback_poll_device,
                        subtopics=["{module_topic}", "{device_topic}"],
                        substitutions={
                            "module_topic": config[CONF_KEY_TOPIC],
                            "module_name": TEXT_NAME,
                            "device_topic": device[CONF_KEY_TOPIC],
                            "bus_id": bus["id"],
                            "address": device[CONF_KEY_ADDRESS],
                            "device_name": device["name"],
                        }
                    )

                iodir = 0   # IODIR register(s)
                gppu = 0    # GPPU register(s)
                gpio = 0    # GPIO register(s)

                for pin in device["pins"]:
                    pin_config = device["pins"][pin]
                    log.debug("Setting up '{pin_name}' on GP{pin:02d} as {direction} on {device} at address 0x{address:02x} on I2C bus '{bus_id}'".format(
                            pin_name=pin_config["name"], pin=pin, direction=TEXT_DIRECTION[pin_config[CONF_KEY_DIRECTION]],
                            device=device[CONF_KEY_CHIP], address=device["address"], bus_id=bus["id"]))
                    subscribe(
                            pin_config[CONF_KEY_TOPIC] + "/{getter}",
                            callback=callback_getter,
                            substitutions={
                                "getter": config[CONF_KEY_TOPIC_GETTER]
                            }
                        )

                    if pin_config[CONF_KEY_DIRECTION] == Direction.INPUT:
                        iodir = _set_bit(iodir, pin)
                        if pin_config[CONF_KEY_RESISTOR] == Pull.UP:
                            log.debug("Setting pull-up resistor for '{pin_name}' on GP{pin:02d} on {device} at address 0x{address:02x} on I2C bus '{bus_id}'".format(
                                    pin_name=pin_config["name"], pin=pin, device=device[CONF_KEY_CHIP], address=device["address"], bus_id=bus["id"]))
                            gppu = _set_bit(gppu, pin)
                    else:
                        subscribe(
                                pin_config[CONF_KEY_TOPIC] + "/{setter}",
                                callback=callback_setter,
                                substitutions={"setter": config[CONF_KEY_TOPIC_SETTER]}
                            )

                    if pin_config[CONF_KEY_INITIAL] == config[CONF_KEY_PAYLOAD_ON]:
                        gpio = _set_bit(gpio, pin, 1 ^ pin_config[CONF_KEY_INVERT])
                    elif pin_config[CONF_KEY_INITIAL] == config[CONF_KEY_PAYLOAD_OFF]:
                        gpio = _set_bit(gpio, pin, 0 ^ pin_config[CONF_KEY_INVERT])
                    else:
                        log.warn("Invalid initial state '{state}' for '{pin_name}' on GP{pin:02d} on {device} at address 0x{address:02x} on I2C bus '{bus_id}'".format(
                            state=_get_bit(gpio, pin), pin_name=pin_config["name"], pin=pin, device=device[CONF_KEY_CHIP], address=device["address"], bus_id=bus["id"]))
                        gpio = _set_bit(gpio, pin, 0 ^ pin_config[CONF_KEY_INVERT])
                    log.debug("Setting initial state '{state}' for '{pin_name}' on GP{pin:02d} on {device} at address 0x{address:02x} on I2C bus '{bus_id}'".format(
                            state=_get_bit(gpio, pin), pin_name=pin_config["name"], pin=pin, device=device[CONF_KEY_CHIP], address=device["address"], bus_id=bus["id"]))

                log.debug("Writing IODIR register to {device} '{device_name}' at address 0x{address:02x} on I2C bus '{bus_id}': {value}".format(
                        device=device[CONF_KEY_CHIP], device_name=device["name"], address=device["address"], bus_id=bus["id"], value=bin(iodir)))
                device["device"].iodir = iodir

                log.debug("Writing GPPU register to {device} '{device_name}' at address 0x{address:02x} on I2C bus '{bus_id}': {value}".format(
                        device=device[CONF_KEY_CHIP], device_name=device["name"], address=device["address"], bus_id=bus["id"], value=bin(gppu)))
                device["device"].gppu = gppu

                log.debug("Writing GPIO register to {device} '{device_name}' at address 0x{address:02x} on I2C bus '{bus_id}': {value}".format(
                        device=device[CONF_KEY_CHIP], device_name=device["name"], address=device["address"], bus_id=bus["id"], value=bin(gpio)))
                device["device"].gpio = gpio

                log.debug("Successfully initialized {device} '{device_name}' at address 0x{address:02x} on I2C bus '{bus_id}'".format(
                        device=device[CONF_KEY_CHIP], device_name=device["name"], address=device["address"], bus_id=bus["id"]))

            finally:
                release_i2c_lock(bus["id"], bus["scl"].id, bus["sda"].id, TEXT_NAME)
        else:
            log.error("Failed to initialize {device} '{device_name}' at address 0x{address:02x} was not able to lock I2C bus '{bus_id}'".format(
                    device=device[CONF_KEY_CHIP], device_name=device["name"], address=device["address"], bus_id=bus["id"]))

    else:
        log.error("Unable to initialize {device} '{device_name}' at address 0x{address:02x} because I2C bus '{bus_id}' is not configured".format(
                device=device[CONF_KEY_CHIP], device_name=device["name"], address=device["address"], bus_id=bus["id"]))

    return True if device.get("device", False) else False


def set_pin(device, pin, payload):
    """
    Set the state of a pin and publish
    ``payload`` expects ``payload on`` or ``payload off``
    """
    bus = device["bus"]
    if payload == config[CONF_KEY_PAYLOAD_ON]:
        state = 1
    elif payload == config[CONF_KEY_PAYLOAD_OFF]:
        state = 0
    else:
        log.warn("Received unrecognized SET payload '{payload}' for '{pin_name}' on GP{pin:02d} on '{device_name}' at address 0x{address:02x} on I2C bus '{bus_id}'".format(
                payload=payload, pin=pin, pin_name=device["pins"][pin]["name"],
                device=device["name"], address=device["address"], bus_id=bus["id"]))
        return

    if acquire_i2c_lock(bus["id"], bus["scl"].id, bus["sda"].id, TEXT_NAME, timeout=5000):
        state = state ^ device["pins"][pin][CONF_KEY_INVERT]
        device_gpio = device["device"].gpio
        device["device"].gpio = _set_bit(device_gpio, pin, state)
        release_i2c_lock(bus["id"], bus["scl"].id, bus["sda"].id, TEXT_NAME)
        log.debug("Set state '{state}' logic {logic} from GP{pin:02d} on {device} '{device_name}' at address 0x{address:02x} on I2C bus '{bus_id}'".format(
                state=config[CONF_KEY_PAYLOAD_ON] if state else config[CONF_KEY_PAYLOAD_OFF],
                logic=TEXT_LOGIC_STATE[state ^ device["pins"][pin][CONF_KEY_INVERT]],
                pin=pin, device=device[CONF_KEY_CHIP], device_name=device["name"],
                address=device["address"], bus_id=device["bus"]["id"]))
        get_pin(device, pin, gpio=device_gpio)
    else:
        log.warn("Failed to set {pin_name} GP{pin:02d} on {device} '{device_name}' was not able to lock I2C bus '{bus_id}'".format(
                pin_name=device["pins"][pin]["name"], pin=pin, device=device[CONF_KEY_CHIP],
                device_name=device["name"], bus_id=bus["id"]))


def get_pin(device, pin, gpio=None):
    """
    Read the state from a pin and publish
    Can provide ``gpio`` register value, otherwise will be read from device
    """
    bus = device["bus"]
    if gpio is None:
        if acquire_i2c_lock(bus["id"], bus["scl"].id, bus["sda"].id, TEXT_NAME, timeout=5000):
            gpio = device["device"].gpio
            release_i2c_lock(bus["id"], bus["scl"].id, bus["sda"].id, TEXT_NAME)
        else:
            log.warn("Failed to read '{pin_name}' GP{pin:02d} on {device} '{device_name}' was not able to lock I2C bus '{bus_id}'".format(
                    pin_name=device["pins"][pin]["name"], pin=pin, device=device[CONF_KEY_CHIP],
                    device_name=device["name"], bus_id=bus["id"]))
            return

    if device.get("device", False) or init_device(device):
        state = _get_bit(gpio, pin) ^ device["pins"][pin][CONF_KEY_INVERT]
        log.debug("Read state '{state}' logic {logic} from GP{pin:02d} on {device} '{device_name}' at address 0x{address:02x} on I2C bus '{bus_id}'".format(
                state=config[CONF_KEY_PAYLOAD_ON] if state else config[CONF_KEY_PAYLOAD_OFF], pin=pin,
                logic=TEXT_LOGIC_STATE[state ^ device["pins"][pin][CONF_KEY_INVERT]],
                device=device[CONF_KEY_CHIP], device_name=device["name"],
                address=device["address"], bus_id=device["bus"]["id"]))
        publish(
                device["pins"][pin][CONF_KEY_TOPIC],
                config[CONF_KEY_PAYLOAD_ON] if state else config[CONF_KEY_PAYLOAD_OFF]
            )


def poll_device(device):
    """
    Publishes states for all configured pins on device
    """
    bus = device["bus"]
    pins = device["pins"]

    if device.get("device", False) or init_device(device):
        log.debug("Polling all pins of {device} '{device_name}' at address 0x{address:02x} on I2C bus '{bus_id}'".format(
                device=device[CONF_KEY_CHIP], device_name=device["name"], address=device["address"], bus_id=bus["id"]))

        if acquire_i2c_lock(bus["id"], bus["scl"].id, bus["sda"].id, TEXT_NAME, timeout=5000):
            gpio = device["device"].gpio
            release_i2c_lock(bus["id"], bus["scl"].id, bus["sda"].id, TEXT_NAME)
            for pin in pins:
                get_pin(device, pin, gpio=gpio)
        else:
            log.warn("Failed to poll all pins of {device} '{device_name}' was not able to lock I2C bus '{bus_id}'".format(
                    device=device[CONF_KEY_CHIP], device_name=device["name"], bus_id=bus["id"]))



def poll_all():
    """
    Polls all devices and publishes states for all configured pins
    """
    log.debug("Polling all devices")
    for device in devices:
        poll_device(device)


def poll_interval():
    """ Polls all devices and restarts the timer """
    log.debug("Polling timer fired")
    global polling_timer
    polling_timer = Timer(config[CONF_KEY_POLL_INT], poll_interval)
    polling_timer.start()
    poll_all()
