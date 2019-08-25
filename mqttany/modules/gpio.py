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

import time, os
from threading import Timer
import multiprocessing as mproc
from queue import Empty as QueueEmptyError
from Adafruit_GPIO import GPIO, Platform

from mqttany import logger
log = logger.get_logger("gpio")
from config import load_config
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
CONF_KEY_DEBOUNCE = "debounce time"
CONF_KEY_DIRECTION = "direction"
CONF_MAP_DIRECTION = {"input": GPIO.IN, "in": GPIO.IN, "output": GPIO.OUT, "out": GPIO.OUT}
CONF_KEY_INTERRUPT = "interrupt"
CONF_MAP_INTERRUPT = {"rising": GPIO.RISING, "falling": GPIO.FALLING, "both": GPIO.BOTH, "none": None}
CONF_KEY_RESISTOR = "resistor"
CONF_MAP_RESISTOR = {"pullup": GPIO.PUD_UP, "up": GPIO.PUD_UP, "pulldown": GPIO.PUD_DOWN, "down": GPIO.PUD_DOWN, "off": GPIO.PUD_OFF, "none": GPIO.PUD_OFF}
CONF_KEY_INVERT = "invert"
CONF_OPTIONS = {
    "GPIO": {
        CONF_KEY_TOPIC: {},
        CONF_KEY_TOPIC_SETTER: {"default": "set"},
        CONF_KEY_TOPIC_GETTER: {"default": "get"},
        CONF_KEY_TOPIC_POLL: {"default": "poll"},
        CONF_KEY_PAYLOAD_ON: {"default": "ON"},
        CONF_KEY_PAYLOAD_OFF: {"default": "OFF"},
        CONF_KEY_POLL_INT: {"type": float, "default": 0.0},
        CONF_KEY_DEBOUNCE: {"type": int, "default": 200},
    }
}
CONF_OPTIONS_PIN = {
    CONF_KEY_DIRECTION: {},
    CONF_KEY_TOPIC: {"default": "{pin}"},
    CONF_KEY_INTERRUPT: {"default": None},
    CONF_KEY_RESISTOR: {"default": None},
    CONF_KEY_INVERT: {"type": bool, "default": False},
}

GPIO_PINS_RPI3 = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]
GPIO_PINS = []

gpio = None
config = {}
queue = mproc.Queue()
pins = {}
polling_timer = None


def init():
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
        CONF_OPTIONS[str(pin)] = CONF_OPTIONS_PIN

    log.debug("Loading config")
    raw_config = load_config(CONF_FILE, CONF_OPTIONS, log)
    if raw_config:
        log.debug("Config loaded")

        config.update(raw_config.pop("GPIO"))

        for pin in raw_config:
            raw_config[pin][CONF_KEY_TOPIC] = resolve_topic(
                    raw_config[pin][CONF_KEY_TOPIC],
                    module_topic=config[CONF_KEY_TOPIC],
                    substitutions={"pin": pin}
                )

            pins[pin] = {
                CONF_KEY_DIRECTION: CONF_MAP_DIRECTION[str(raw_config[pin][CONF_KEY_DIRECTION]).lower()],
                CONF_KEY_TOPIC: raw_config[pin][CONF_KEY_TOPIC],
                CONF_KEY_INTERRUPT: CONF_MAP_INTERRUPT[str(raw_config[pin][CONF_KEY_INTERRUPT]).lower()],
                CONF_KEY_RESISTOR: CONF_MAP_RESISTOR[str(raw_config[pin][CONF_KEY_RESISTOR]).lower()],
                CONF_KEY_INVERT: raw_config[pin][CONF_KEY_INVERT]
            }

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
        log.debug("  Setting up GPIO{pin} with options [{options}]".format(
                pin=pin, options=pins[pin]))

        if not acquire_gpio_lock(pin, __name__):
            log.error("Failed to acquire a lock on GPIO{pin}".format(pin=pin))
            continue

        gpio.setup(int(pin), pins[pin][CONF_KEY_DIRECTION], pull_up_down=pins[pin][CONF_KEY_RESISTOR])

        if pins[pin][CONF_KEY_DIRECTION] == GPIO.IN and pins[pin][CONF_KEY_INTERRUPT] is not None:
            log.debug("    Adding interrupt event for GPIO{pin} with edge trigger '{edge}'".format(
                    pin=pin, edge=pins[pin][CONF_KEY_INTERRUPT]))
            gpio.add_event_detect(
                    int(pin),
                    pins[pin][CONF_KEY_INTERRUPT],
                    callback=interrupt_handler,
                    bouncetime=config[CONF_KEY_DEBOUNCE]
                )
        elif pins[pin][CONF_KEY_DIRECTION] == GPIO.OUT:
            log.debug("    Adding MQTT subscriptions for GPIO{pin}".format(pin=pin))
            subscribe(
                    pins[pin][CONF_KEY_TOPIC] + "/{setter}",
                    callback=on_message,
                    module_topic=config[CONF_KEY_TOPIC],
                    substitutions={"setter":config[CONF_KEY_TOPIC_SETTER]}
                )
        subscribe(
                pins[pin][CONF_KEY_TOPIC] + "/{getter}",
                callback=on_message,
                module_topic=config[CONF_KEY_TOPIC],
                substitutions={"getter":config[CONF_KEY_TOPIC_GETTER]}
            )

    log.debug("Adding MQTT subscription to poll topic")
    subscribe(
            config[CONF_KEY_TOPIC_POLL],
            callback=on_message,
            module_topic=config[CONF_KEY_TOPIC]
        )

    if config[CONF_KEY_POLL_INT] > 0:
        log.debug("Starting polling timer with interval of {interval}s".format(
                interval=config[CONF_KEY_POLL_INT]))
        global polling_timer
        polling_timer = Timer(config[CONF_KEY_POLL_INT], poll_interval)
        polling_timer.start()

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

                # check if topic matches any pins
                match_pins = [pin for pin in pins if pins[pin][CONF_KEY_TOPIC] in message["topic"]]
                if match_pins:
                    for pin in match_pins:
                        if message["topic"].split("/")[-1] == config[CONF_KEY_TOPIC_SETTER]:
                            if pins[pin][CONF_KEY_DIRECTION] == GPIO.OUT:
                                if message["payload"] == config[CONF_KEY_PAYLOAD_ON]:
                                    state = True
                                elif message["payload"] == config[CONF_KEY_PAYLOAD_OFF]:
                                    state = False
                                else:
                                    log.warn("Received unrecognized SET payload '{payload}' for GPIO{pin}".format(
                                            payload=message["payload"], pin=pin))
                                    continue

                                state = state ^ pins[pin][CONF_KEY_INVERT]
                                gpio.output(int(pin), state)
                                log.debug("Set GPIO{pin} to '{state}'".format(pin=pin, state=int(state)))
                                publish_states({pin: state})
                            else:
                                log.warn("Received SET command for GPIO{pin} but it is configured as an input".format(pin=pin))

                        elif message["topic"].split("/")[-1] == config[CONF_KEY_TOPIC_GETTER]:
                            log.debug("Polling state of GPIO{pin}".format(pin=pin))
                            publish_states({pin: read_pin(pin)})

                        else:
                            log.warn("Received unrecognized message '{payload}' on topic '{topic}'".format(
                                    payload=message["payload"], topic=message["topic"]))

                elif config[CONF_KEY_TOPIC_POLL] in message["topic"]:
                    log.debug("Received POLL command")
                    poll_all()

                else:
                    log.warn("Received unrecognized message '{payload}' on topic '{topic}'".format(
                            payload=message["payload"], topic=message["topic"]))

    if config[CONF_KEY_POLL_INT] > 0:
        log.debug("Stopping polling timer")
        polling_timer.cancel()

    gpio.cleanup()
    for pin in pins:
        release_gpio_lock(pin, __name__)


def interrupt_handler(pin):
    """
    Handles GPIO pin interrupt callbacks
    """
    log.debug("Interrupt triggered on GPIO{pin}".format(pin=pin))
    publish_states({str(pin):read_pin(pin)})


def on_message(client, userdata, message):
    """
    MQTT message handler
    """
    #if message.topic.split("/")[0] == root_topic:
    #    topic = message.topic[len(root_topic)+1:]
    #else:
    #    topic = message.topic
    queue.put_nowait({
            "topic": message.topic,
            "payload": message.payload
        })


def publish_states(states):
    """
    Takes a dict of pin:state and publishes mqtt messages for each
    """
    for pin in states:
        publish(
                pins[pin][CONF_KEY_TOPIC],
                config[CONF_KEY_PAYLOAD_ON] if states[pin] else config[CONF_KEY_PAYLOAD_OFF]
            )


def read_pin(pin):
    """
    Read the state from a pin
    """
    state = bool(gpio.input(int(pin))) ^ pins[pin][CONF_KEY_INVERT] # apply the invert flag
    log.debug("Read state '{state}' from GPIO{pin}".format(
            state=state, pin=pin))
    return state


def poll_all():
    """
    Polls all configured pins and publishes states
    """
    log.debug("Polling all pins")
    publish_states({pin:read_pin(int(pin)) for pin in pins})


def poll_interval():
    """ Polls all pins and restarts the timer """
    log.debug("Polling timer fired")
    global polling_timer
    polling_timer = Timer(config[CONF_KEY_POLL_INT], poll_interval)
    polling_timer.start()
    poll_all()
