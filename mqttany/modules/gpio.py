"""
***********
GPIO Module
***********

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

import time, os, sys
from threading import Timer, ThreadError
import multiprocessing as mproc
from queue import Empty as QueueEmptyError
from Adafruit_GPIO import GPIO, Platform

import logger
log = logger.get_logger("gpio")
from config import parse_config
from common import POISON_PILL, acquire_gpio_lock, release_gpio_lock

from modules.mqtt import resolve_topic, publish, subscribe, add_message_callback

all = [  ]

CONF_FILE = "gpio.conf"
CONF_KEY_TOPIC = "topic"
CONF_KEY_TOPIC_SETTER = "topic set"
CONF_KEY_TOPIC_GETTER = "topic get"
CONF_KEY_TOPIC_POLL = "topic poll"
CONF_KEY_PAYLOAD_ON = "payload on"
CONF_KEY_PAYLOAD_OFF = "payload off"
CONF_KEY_POLL_INT = "polling interval"
CONF_KEY_DEBOUNCE = "debounce"
CONF_KEY_DIRECTION = "direction"
CONF_KEY_INTERRUPT = "interrupt"
CONF_KEY_RESISTOR = "resistor"
CONF_KEY_INVERT = "invert"
CONF_KEY_INITIAL = "initial state"
CONF_OPTIONS = {
    CONF_KEY_TOPIC: {"default": "{module_name}"},
    CONF_KEY_TOPIC_SETTER: {"default": "set"},
    CONF_KEY_TOPIC_GETTER: {"default": "get"},
    CONF_KEY_TOPIC_POLL: {"default": "poll"},
    CONF_KEY_PAYLOAD_ON: {"default": "ON"},
    CONF_KEY_PAYLOAD_OFF: {"default": "OFF"},
    CONF_KEY_POLL_INT: {"type": float, "default": 0.0},
    CONF_KEY_DEBOUNCE: {"type": int, "default": 200},
}
CONF_OPTIONS_PIN = {
    "type": "section",
    "required": False,
    CONF_KEY_TOPIC: {"default": "{pin}"},
    CONF_KEY_DIRECTION: {"default": GPIO.IN, "selection": {"input": GPIO.IN, "in": GPIO.IN, "output": GPIO.OUT, "out": GPIO.OUT}},
    CONF_KEY_INTERRUPT: {"default": None, "selection": {"rising": GPIO.RISING, "falling": GPIO.FALLING, "both": GPIO.BOTH, "none": None}},
    CONF_KEY_RESISTOR: {"default": GPIO.PUD_OFF, "selection": {"pullup": GPIO.PUD_UP, "up": GPIO.PUD_UP, "pulldown": GPIO.PUD_DOWN, "down": GPIO.PUD_DOWN, "off": GPIO.PUD_OFF, "none": GPIO.PUD_OFF}},
    CONF_KEY_INVERT: {"type": bool, "default": False},
    CONF_KEY_INITIAL: {"default": "{payload_off}"},
}

TEXT_NAME = __name__.split(".")[-1]
TEXT_DIRECTION = {GPIO.IN: "input", GPIO.OUT: "output"}
TEXT_RESISTOR = {GPIO.PUD_UP: "up", GPIO.PUD_DOWN: "down", GPIO.PUD_OFF: "off"}
TEXT_LOGIC_STATE = ["LOW", "HIGH"]

GPIO_PINS_RPI3 = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]
GPIO_PINS = []

gpio = None
config = {}
queue = None
pins = {}
polling_timer = None


def init(config_data={}):
    """
    Initializes the module
    """
    global gpio, GPIO_PINS

    pi_version = Platform.pi_version()
    if pi_version:
        log.debug("Platform is Raspberry Pi {}".format(pi_version))
        if pi_version == 1:
            log.error("No platform config for Raspberry Pi 1")
            return False
        elif pi_version == 2:
            log.error("No platform config for Raspberry Pi 2")
            return False
        elif pi_version == 3:
            GPIO_PINS = GPIO_PINS_RPI3

        gpio = GPIO.get_platform_gpio(mode=11)
    else:
        log.error("Unknown platform")
        return False

    for pin in GPIO_PINS:
        CONF_OPTIONS[pin] = CONF_OPTIONS_PIN
    raw_config = parse_config(config_data, CONF_OPTIONS, log)
    if raw_config:
        log.debug("Config loaded")

        for pin in [key for key in raw_config if isinstance(raw_config[key], dict)]:
            pins[pin] = raw_config.pop(pin)
            pins[pin][CONF_KEY_INITIAL] = pins[pin][CONF_KEY_INITIAL].format(
                    payload_on=raw_config[CONF_KEY_PAYLOAD_ON], payload_off=raw_config[CONF_KEY_PAYLOAD_OFF])
            pins[pin][CONF_KEY_TOPIC] = resolve_topic(
                    pins[pin][CONF_KEY_TOPIC],
                    subtopics=["{module_topic}"],
                    substitutions={
                        "module_topic": raw_config[CONF_KEY_TOPIC],
                        "module_name": TEXT_NAME,
                        "pin": pin
                    }
                )

        config.update(raw_config)
        return True
    else:
        log.error("Error loading config")
        return False

def loop():
    """
    Main function loops until it gets 'poison pill'
    """
    log.debug("Setting up hardware")
    for pin in pins:
        log.info("Setting up GPIO{pin} as {direction}".format(
                pin=pin, direction=TEXT_DIRECTION[pins[pin][CONF_KEY_DIRECTION]]))
        log.debug("  with options [{options}]".format(options=pins[pin]))

        if not acquire_gpio_lock(pin, TEXT_NAME, timeout=2000):
            log.error("Failed to acquire a lock on GPIO{pin}".format(pin=pin))
            pins.pop(pin)
            continue

        gpio.setup(pin, pins[pin][CONF_KEY_DIRECTION], pull_up_down=pins[pin][CONF_KEY_RESISTOR])

        if pins[pin][CONF_KEY_DIRECTION] == GPIO.IN and pins[pin][CONF_KEY_INTERRUPT] is not None:
            log.debug("Adding interrupt event for GPIO{pin} with edge trigger '{edge}'".format(
                    pin=pin, edge=pins[pin][CONF_KEY_INTERRUPT]))
            gpio.add_event_detect(
                    pin,
                    pins[pin][CONF_KEY_INTERRUPT],
                    callback=interrupt_handler,
                    bouncetime=config[CONF_KEY_DEBOUNCE]
                )
        elif pins[pin][CONF_KEY_DIRECTION] == GPIO.OUT:
            log.debug("Adding MQTT subscriptions for GPIO{pin}".format(pin=pin))
            subscribe(
                    pins[pin][CONF_KEY_TOPIC] + "/{setter}",
                    callback=callback_setter,
                    subtopics=["{module_topic}"],
                    substitutions={
                        "module_topic": config[CONF_KEY_TOPIC],
                        "module_name": TEXT_NAME,
                        "setter": config[CONF_KEY_TOPIC_SETTER],
                        "pin": pin
                    }
                )
            log.debug("Setting GPIO{pin} to initial state '{initial_state}'".format(
                    pin=pin, initial_state=pins[pin][CONF_KEY_INITIAL]))
            set_pin(pin, pins[pin][CONF_KEY_INITIAL])

        subscribe(
                pins[pin][CONF_KEY_TOPIC] + "/{getter}",
                callback=callback_getter,
                subtopics=["{module_topic}"],
                substitutions={
                    "module_topic": config[CONF_KEY_TOPIC],
                    "module_name": TEXT_NAME,
                    "getter": config[CONF_KEY_TOPIC_GETTER]
                }
            )

    log.debug("Adding MQTT subscription to poll topic")
    subscribe(
            config[CONF_KEY_TOPIC_POLL],
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

    poison_pill = False
    while not poison_pill:
        try:
            message = queue.get_nowait()
        except QueueEmptyError:
            time.sleep(0.025) # 25ms
        else:
            if message == POISON_PILL:
                poison_pill = True # terminate signal
                log.debug("Received poison pill")
            else:
                log.debug("Received message [{message}]".format(message=message))
                func = getattr(sys.modules[__name__], message["func"])
                if func:
                    func(*message.get("args", []), **message.get("kwargs", {}))
                else:
                    log.warn("Unrecognized function '{func}'".format(func=message["func"]))

    if config[CONF_KEY_POLL_INT] > 0:
        log.debug("Stopping polling timer")
        polling_timer.cancel()

    gpio.cleanup()
    for pin in pins:
        release_gpio_lock(pin, TEXT_NAME)


def callback_setter(client, userdata, message):
    """
    Callback for setters
    """
    queue.put_nowait({
        "func": "_callback_setter",
        "args": [message.topic, message.payload.decode("utf-8")]
    })

def _callback_setter(topic, payload):
    if config[CONF_KEY_TOPIC_SETTER]:
        topic = topic[:-len("/" + config[CONF_KEY_TOPIC_SETTER])]
    for pin in pins:
        if topic == pins[pin][CONF_KEY_TOPIC]:
            set_pin(pin, payload)


def callback_getter(client, userdata, message):
    """
    Callback for getters
    """
    queue.put_nowait({
        "func": "_callback_getter",
        "args": [message.topic]
    })

def _callback_getter(topic):
    if config[CONF_KEY_TOPIC_GETTER]:
        topic = topic[:-len("/" + config[CONF_KEY_TOPIC_GETTER])]
    for pin in pins:
        if topic == pins[pin][CONF_KEY_TOPIC]:
            get_pin(pin)


def callback_poll_all(client, userdata, message):
    """
    Callback for poll all
    """
    queue.put_nowait({
        "func": "poll_all"
    })


def interrupt_handler(pin):
    """
    Handles GPIO pin interrupt callbacks
    """
    log.debug("Interrupt triggered on GPIO{pin}".format(pin=pin))
    get_pin(pin)


def get_pin(pin):
    """
    Read the state from a pin and publish
    """
    state = bool(gpio.input(pin)) ^ pins[pin][CONF_KEY_INVERT] # apply the invert flag
    log.debug("Read state '{state}' from GPIO{pin}".format(
        state=config[CONF_KEY_PAYLOAD_ON] if state else config[CONF_KEY_PAYLOAD_OFF], pin=pin))
    publish(
            pins[pin][CONF_KEY_TOPIC],
            payload=config[CONF_KEY_PAYLOAD_ON] if state else config[CONF_KEY_PAYLOAD_OFF]
        )


def set_pin(pin, payload):
    """
    Set the state of a pin and publish
    ``payload`` expects ``payload on`` or ``payload off``
    """
    if payload == config[CONF_KEY_PAYLOAD_ON]:
        state = True
    elif payload == config[CONF_KEY_PAYLOAD_OFF]:
        state = False
    else:
        log.warn("Received unrecognized SET payload '{payload}' for GPIO{pin}".format(
                payload=payload, pin=pin))
        return

    gpio.output(pin, state ^ pins[pin][CONF_KEY_INVERT])
    log.debug("Set GPIO{pin} to '{payload}' logic {state}".format(
        pin=pin, payload=payload, state=TEXT_LOGIC_STATE[int(state)]))
    get_pin(pin) # publish pin state


def poll_all():
    """
    Polls all configured pins and publishes states
    """
    log.debug("Polling all pins")
    for pin in pins: get_pin(pin)


def poll_interval():
    """ Polls all pins and restarts the timer """
    log.debug("Polling timer fired")
    global polling_timer
    polling_timer = Timer(config[CONF_KEY_POLL_INT], poll_interval)
    polling_timer.start()
    poll_all()
