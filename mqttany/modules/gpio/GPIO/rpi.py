"""
****************************************
GPIO Library Wrapper for WiringPi-Python
****************************************

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

try:
    import wiringpi
except ImportError:
    raise ImportError("MQTTany's GPIO module requires 'wiringpi' to be installed, \
        please see the wiki for instructions on how to install requirements")

try:
    import adafruit_platformdetect
except ImportError:
    raise ImportError("MQTTany's GPIO module requires 'Adafruit-PlatformDetect' to be installed, \
        please see the wiki for instructions on how to install requirements")

import threading, subprocess
from time import sleep
from datetime import datetime
now = datetime.now

import logger
from common import TEXT_PIN_PREFIX, Mode, Logic
from modules.gpio.common import config, CONF_KEY_MODE
from modules.gpio.GPIO.common import baseGPIO, Direction, Resistor, Interrupt

TEXT_NAME = ".".join([__name__.split(".")[-3], __name__.split(".")[-1]]) # gives gpio.rpi

log = logger.get_module_logger(module=TEXT_NAME)


map_wiringpi_setup = {
    Mode.BOARD: wiringpi.wiringPiSetupPhys,
    Mode.SOC: wiringpi.wiringPiSetupGpio,
    Mode.WIRINGPI: wiringpi.wiringPiSetup
}
map_direction = {
    Direction.INPUT: wiringpi.INPUT,
    Direction.OUTPUT: wiringpi.OUTPUT,
    wiringpi.INPUT: Direction.INPUT,
    wiringpi.OUTPUT: Direction.OUTPUT
}
map_resistor = {
    Resistor.OFF: wiringpi.PUD_OFF,
    Resistor.PULL_UP: wiringpi.PUD_UP,
    Resistor.PULL_DOWN: wiringpi.PUD_DOWN,
    wiringpi.PUD_OFF: Resistor.OFF,
    wiringpi.PUD_UP: Resistor.PULL_UP,
    wiringpi.PUD_DOWN: Resistor.PULL_DOWN
}
map_interrupt = {
    Interrupt.RISING: wiringpi.INT_EDGE_RISING,
    Interrupt.FALLING: wiringpi.INT_EDGE_FALLING,
    Interrupt.BOTH: wiringpi.INT_EDGE_BOTH,
    wiringpi.INT_EDGE_RISING: Interrupt.RISING,
    wiringpi.INT_EDGE_FALLING: Interrupt.FALLING,
    wiringpi.INT_EDGE_BOTH: Interrupt.BOTH
}
map_interrupt_gpio = {
    Interrupt.RISING: "rising",
    Interrupt.FALLING: "falling",
    Interrupt.BOTH: "both"
}

### Valid GPIOs
PINS_40 = [
     0,  1,  2,  3,  4,  5,  6,  7, # 0..7
     8,  9, 10, 11, 12, 13, 14, 15, # 8..15
    16, 17, 18, 19, 20, 21, 22, 23, # 16..23
    24, 25, 26, 27, -1, -1, -1, -1, # 24..31
    -1, -1, -1, -1, -1, -1, -1, -1, # 32..39
    -1, -1, -1, -1, -1, -1, -1, -1, # 40..47
    -1, -1, -1, -1, -1, -1, -1, -1, # 48..55
    -1, -1, -1, -1, -1, -1, -1, -1, # 56..63
]
PINS_26_R2 = [
    -1, -1,  2,  3,  4, -1, -1,  7, # 0..7
     8,  9, 10, 11, -1, -1, 14, 15, # 8..15
    -1, 17, 18, -1, -1, -1, 22, 23, # 16..23
    24, 25, -1, 27, -1, -1, -1, -1, # 24..31
    -1, -1, -1, -1, -1, -1, -1, -1, # 32..39
    -1, -1, -1, -1, -1, -1, -1, -1, # 40..47
    -1, -1, -1, -1, -1, -1, -1, -1, # 48..55
    -1, -1, -1, -1, -1, -1, -1, -1, # 56..63
]
PINS_26_R1 = [
     0,  1, -1, -1,  4, -1, -1,  7, # 0..7
     8,  9, 10, 11, -1, -1, 14, 15, # 8..15
    -1, 17, 18, -1, -1, 21, 22, 23, # 16..23
    24, 25, -1, -1, -1, -1, -1, -1, # 24..31
    -1, -1, -1, -1, -1, -1, -1, -1, # 32..39
    -1, -1, -1, -1, -1, -1, -1, -1, # 40..47
    -1, -1, -1, -1, -1, -1, -1, -1, # 48..55
    -1, -1, -1, -1, -1, -1, -1, -1, # 56..63
]
detector = adafruit_platformdetect.Detector()
board = detector.board.id
rpi_40 = detector.board.any_raspberry_pi_40_pin
rpi_26_r1 = detector.board.id in [
    adafruit_platformdetect.board.RASPBERRY_PI_A,
    adafruit_platformdetect.board.RASPBERRY_PI_B_REV1
]
def gpioPinToGpio(pin):
    if rpi_40:
        return PINS_40[pin]
    elif rpi_26_r1:
        return PINS_26_R1[pin]
    else:
        return PINS_26_R2[pin]

map_pin_lookup = {
    Mode.BOARD: wiringpi.physPinToGpio,
    Mode.SOC: gpioPinToGpio,
    Mode.WIRINGPI: wiringpi.wpiPinToGpio
}


class rpiGPIO(baseGPIO):
    """
    GPIO Library Wrapper for WiringPi-Python
    """

    def __init__(self, mode=Mode.SOC):
        self._mode = mode
        self._interrupts = {}
        if isinstance(mode, Mode):
            map_wiringpi_setup[mode]()
        else:
            raise ValueError("Unexpected value for mode, must be BOARD, SOC, or WIRINGPI")

    @staticmethod
    def getPinFromMode(pin, mode):
        """
        Returns SOC GPIO number for ``pin`` in mode ``mode``
        """
        return map_pin_lookup[mode](pin)

    def pin_valid(self, pin, direction):
        """
        Return ``True`` if pin can be used for ``direction``
        """
        if -1 < pin < 64:
            if map_pin_lookup[self._mode](pin) > -1:
                if direction in [Direction.INPUT, Direction.OUTPUT]:
                    return True
                else:
                    log.error("{pin_prefix}{pin} cannot be used for {direction} on {board}".format(
                        pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]],
                        pin=pin, direction=direction.name, board=board))
            else:
                log.error("{pin_prefix}{pin} cannot be used on {board}".format(
                    pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]],
                    pin=pin, board=board))
        else:
            log.error("{pin_prefix}{pin} is out of range".format(
                pin_prefix=TEXT_PIN_PREFIX[config[CONF_KEY_MODE]],
                pin=pin))
        return False

    def setup(self, pin, direction, resistor=Resistor.OFF):
        """
        Set the pin direction (input or output).
        """
        wiringpi.pinMode(
            pin,
            map_direction[direction]
        )
        if direction == Direction.INPUT:
            wiringpi.pullUpDnControl(pin, map_resistor[resistor])

    def output(self, pin, value):
        """
        Set the pin state (high or low).
        """
        wiringpi.digitalWrite(pin, value)

    def input(self, pin):
        """
        Read the pin state (high or low).
        """
        return wiringpi.digitalRead(pin)

    def add_event_detect(self, pin, edge, callback, bouncetime=0, *args, **kwargs):
        """
        Add a pin change interrupt with callback.
        """
        if pin in self._interrupts:
            with self._interrupts[pin] as isr:
                isr.set_edge(edge)
                isr.set_bouncetime(bouncetime)
                isr.set_callback(callback, *args, **kwargs)
                isr.enable()
        else:
            self._interrupts[pin] = InterruptThread(
                pin,
                edge,
                self._mode,
                callback,
                bouncetime
            )
            if not self._interrupts[pin].is_ok:
                log.error("Failed to setup interrupt for {pin_prefix}{pin:02d}".format(
                    pin=pin, pin_prefix=TEXT_PIN_PREFIX[self._mode]))
                self._interrupts.pop(pin)

    def remove_event_detect(self, pin):
        """
        Remove a pin change interurpt.
        """
        if pin in self._interrupts:
            self._interrupts[pin].disable()

    def cleanup(self, pin=None):
        """
        Clean up interrupts for pin or all if pin is ``None``.
        """
        if pin is not None:
            self.remove_event_detect(pin)
        else:
            for pin in self._interrupts:
                self.remove_event_detect(pin)


class InterruptThread(object):
    """
    WiringPi ISR handler and debounce
    """

    def __init__(self, pin, edge, mode, callback, bouncetime, *args, **kwargs):
        self._gpio = subprocess.run(["which", "gpio"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout.decode("utf-8").strip("\n")
        if self._gpio:
            self._ok = True
            self._pin = pin
            self._edge = edge
            self._mode = mode
            self._bouncetime = bouncetime
            self._thread = None
            self._callback = callback
            self._cbargs = args
            self._cbkwargs = kwargs
            wiringpi.wiringPiISR(pin, map_interrupt[edge], self._isr) # spawns a thread that loops forever
        else:
            self._ok = False
            log.error("Could not find 'gpio' command on this system. Please make sure you have installed 'wiringpi'")

    @property
    def is_ok(self): return self._ok

    def enable(self):
        result = subprocess.run(
            [self._gpio, "edge", str(map_pin_lookup[self._mode](self._pin)), map_interrupt_gpio[self._edge]],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )
        stderr = result.stderr.decode("utf-8").strip("\n")
        if result.returncode:
            self._ok = False
            log.error("An error occurred while enabling the hardware interrupt for {pin_prefix}{pin:02d}{gpio_pin}: {error}".format(
                pin=self._pin, pin_prefix=TEXT_PIN_PREFIX[self._mode], error=stderr,
                gpio_pin="" if self._mode == Mode.SOC else " (GPIO{:02d})".format(rpiGPIO.getPinFromMode(self._pin, self._mode))))
        # re-enable interrupt trigger

    def disable(self):
        result = subprocess.run(
            [self._gpio, "edge", str(map_pin_lookup[self._mode](self._pin)), "none"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        stderr = result.stderr.decode("utf-8").strip("\n")
        if result.returncode:
            self._ok = False
            log.error("An error occurred while disabling the hardware interrupt for {pin_prefix}{pin:02d}{gpio_pin}: {error}".format(
                pin=self._pin, pin_prefix=TEXT_PIN_PREFIX[self._mode], error=stderr,
                gpio_pin="" if self._mode == Mode.SOC else " (GPIO{:02d})".format(rpiGPIO.getPinFromMode(self._pin, self._mode))))
        # doesn't seem to be another way to do this
        # wiringpi offers nothing to remove an interrupt

    def set_edge(self, edge):
        self._edge = edge

    def set_bouncetime(self, bouncetime):
        self._bouncetime = bouncetime

    def set_callback(self, callback, *args, **kwargs):
        self._callback = callback
        self._cbargs = args
        self._cbkwargs = kwargs

    def _isr(self):
        if not self._thread or not self._thread.isAlive():
            self._thread = threading.Thread(
                name="ISR{:02d}".format(self._pin),
                target=self._debounce
            )
            self._thread.start()
        else:
            log.debug("Debounce thread for {pin_prefix}{pin:02d} already exists".format(
                pin=self._pin, pin_prefix=TEXT_PIN_PREFIX[self._mode]))

    def _debounce(self):
        end = now().microsecond + self._bouncetime * 1000
        initial = wiringpi.digitalRead(self._pin)
        while now().microsecond < end:
            sleep(.001)
        if initial == wiringpi.digitalRead(self._pin):
            self._callback(self._pin, *self._cbargs, **self._cbkwargs)
