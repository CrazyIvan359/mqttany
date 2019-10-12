"""
***********************************************
GPIO Library Wrapper for Odroid WiringPi-Python
***********************************************

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
    import odroid_wiringpi as wiringpi
except ImportError:
    raise ImportError("MQTTany's GPIO module requires 'odroid_wiringpi' to be installed, \
        please see the wiki for instructions on how to install requirements")

try:
    import adafruit_platformdetect
    detector = adafruit_platformdetect.Detector()
    board = detector.board.id
except ImportError:
    raise ImportError("MQTTany's GPIO module requires 'adafruit_platformdetect' to be installed, \
        please see the wiki for instructions on how to install requirements")

import threading, subprocess
from time import sleep
from datetime import datetime
now = datetime.now

import logger
from common import TEXT_PIN_PREFIX, Mode, Logic
from modules.gpio.GPIO.common import baseGPIO, Direction, Resistor, Interrupt

TEXT_NAME = ".".join([__name__.split(".")[-3], __name__.split(".")[-1]]) # gives gpio.odroid

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

def is_odroid_xu3():
    """Return ``True`` if platform is Odroid XU3"""
    return "ODROID-XU3" in detector.get_cpuinfo_field("Hardware")

def is_odroid_xu4():
    """Return ``True`` if platform is Odroid XU4"""
    return "ODROID-XU3" in detector.get_cpuinfo_field("Hardware")


### Valid GPIOs
PINS_XU = [
     -1,  -1,  -1,  -1,  -1,  -1,  -1,  -1, # 0..7
     -1,  -1,  -1,  -1,  -1,  -1,  -1,  -1, # 8..15
     -1,  -1,  18,  19,  -1,  21,  22,  23, # 16..23
     24,  25,  -1,  -1,  28,  29,  30,  31, # 24..31
     -1,  33,  34,  -1,  -1,  -1,  -1,  -1, # 32..39
]
for i in range(40, 168): PINS_XU.append(-1)
PINS_XU.extend([
     -1,  -1,  -1, 171, 172, 173, 174,  -1, # 168..175
     -1,  -1,  -1,  -1,  -1,  -1,  -1,  -1, # 176..183
     -1,  -1,  -1, 187, 188, 189, 190, 191, # 184..191
    192,  -1,  -1,  -1,  -1,  -1,  -1,  -1, # 192..199
     -1,  -1,  -1,  -1,  -1,  -1,  -1,  -1, # 200..207
     -1, 209, 210,  -1,  -1,  -1,  -1,  -1, # 208..215
     -1,  -1,  -1,  -1,  -1,  -1,  -1,  -1, # 216..223
     -1, 225, 226, 227, 228, 229            # 224..229
])

PINS_C1 = []
for i in range(0, 72): PINS_C1.append(-1)
PINS_C1.extend([
     -1,  -1,  74,  75,  76,  77,  -1,  -1, # 72..79
     -1,  -1,  -1,  83,  -1,  -1,  -1,  87, # 80..87
     88,  -1,  -1,  -1,  -1,  -1,  -1,  -1, # 88..95
     -1,  97,  98,  99, 100, 101, 102, 103, # 96..103
    104, 105, 106, 107, 108,  -1,  -1,  -1, # 104..111
     -1, 113, 114, 115, 116, 117, 118       # 112..118
])

PINS_C1P = [
     -1,  -1,  -1,  -1,  -1,  -1,   6,  -1, # 0..7
      8,   9,  10,  11,  -1,  -1,  -1,  -1  # 8..15
]
for i in range(16, 72): PINS_C1P.append(-1)
PINS_C1.extend([
     -1,  -1,  74,  75,  76,  77,  -1,  -1, # 72..79
     -1,  -1,  -1,  83,  -1,  -1,  -1,  87, # 80..87
     88,  -1,  -1,  -1,  -1,  -1,  -1,  -1, # 88..95
     -1,  97,  98,  99, 100, 101, 102, 103, # 96..103
    104, 105, 106, 107, 108,  -1,  -1,  -1, # 104..111
     -1, 113, 114, 115, 116, 117, 118       # 112..118
])

PINS_C2 = []
for i in range(0, 128): PINS_C2.append(-1)
PINS_C2.extend([
    128,  -1, 130, 131, 132, 133,  -1,  -1, # 128..135
])
for i in range(136, 200): PINS_C2.append(-1)
PINS_C2.extend([
     -1,  -1,  -1,  -1,  -1, 205, 206, 207, # 200..207
    208,  -1,  -1,  -1,  -1,  -1, 214,  -1, # 208..215
     -1,  -1, 218, 219,  -1,  -1,  -1,  -1, # 216..223
    224, 225,  -1,  -1, 228, 229, 230, 231, # 224..231
    232, 233, 234, 235, 236, 237, 238, 239, # 232..239
    240, 241,  -1,  -1,  -1,  -1,  -1, 247, # 240..247
     -1, 249                                # 248..249
])

PINS_N2 = []
for i in range(0, 464): PINS_N2.append(-1)
PINS_N2.extend([
    464,  -1,  -1,  -1,  -1,  -1,  -1,  -1, # 464..471
    472, 473, 474, 475, 476, 477, 478, 479, # 472..479
    480, 481, 482, 483, 484, 485, 486, 487, # 480..487
    488, 489, 490, 491, 492, 493, 494, 495  # 488..495
])


# Identify Board
od_xu = is_odroid_xu3() or is_odroid_xu4()
od_c1 = board == adafruit_platformdetect.board.ODROID_C1
od_c1p = board == adafruit_platformdetect.board.ODROID_C1_PLUS
od_c2 = board == adafruit_platformdetect.board.ODROID_C2
od_n2 = board == adafruit_platformdetect.board.ODROID_N2
MAX_GPIO = 0
if od_xu:
    MAX_GPIO = len(PINS_XU)
elif od_c1 or od_c1p:
    MAX_GPIO = len(PINS_C1)
elif od_c2:
    MAX_GPIO = len(PINS_C2)
elif od_n2:
    MAX_GPIO = len(PINS_N2)


def gpioPinToGpio(pin):
    if od_xu:
        return PINS_XU[pin]
    elif od_c1:
        return PINS_C1[pin]
    elif od_c1p:
        return PINS_C1P[pin]
    elif od_c2:
        return PINS_C2[pin]
    else:
        return PINS_N2[pin]

map_pin_lookup = {
    Mode.BOARD: wiringpi.physPinToGpio,
    Mode.SOC: gpioPinToGpio,
    Mode.WIRINGPI: wiringpi.wpiPinToGpio
}


class odroidGPIO(baseGPIO):
    """
    GPIO Library Wrapper for Odroid WiringPi-Python
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
        if -1 < pin < MAX_GPIO:
            if map_pin_lookup[self._mode](pin) > -1:
                if direction in [Direction.INPUT, Direction.OUTPUT]:
                    return True
                else:
                    log.error("{pin_prefix}{pin} cannot be used for {direction} on {board}".format(
                        pin_prefix=TEXT_PIN_PREFIX[self._mode],
                        pin=pin, direction=direction.name, board=board))
            else:
                log.error("{pin_prefix}{pin} cannot be used on {board}".format(
                    pin_prefix=TEXT_PIN_PREFIX[self._mode],
                    pin=pin, board=board))
        else:
            log.error("{pin_prefix}{pin} is out of range".format(
                pin_prefix=TEXT_PIN_PREFIX[self._mode],
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
        if self._mode == Mode.SOC:
            # This causes SEGFAULTs because of the workaround for not being able to pass
            # arguments to C callbacks and pin numbers > 63
            # see https://github.com/hardkernel/WiringPi2-Python/blob/master/wiringpi.i#L97
            log.error("Pin change interrupts do not work with SOC pin numbering on Odroid boards")
            return

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
