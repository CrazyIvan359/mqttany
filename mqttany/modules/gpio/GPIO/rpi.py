"""
****************************
GPIO Library Wrapper for RPi
****************************

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

import RPi.GPIO as rpi_gpio

from modules.gpio.GPIO.common import baseGPIO, Logic, Direction, Resistor, Interrupt

map_direction = {
    Direction.INPUT: rpi_gpio.IN,
    Direction.OUTPUT: rpi_gpio.OUT,
    rpi_gpio.IN: Direction.INPUT,
    rpi_gpio.OUT: Direction.OUTPUT
}
map_resistor = {
    Resistor.OFF: rpi_gpio.PUD_OFF,
    Resistor.PULL_UP: rpi_gpio.PUD_UP,
    Resistor.PULL_DOWN: rpi_gpio.PUD_DOWN,
    rpi_gpio.PUD_OFF: Resistor.OFF,
    rpi_gpio.PUD_UP: Resistor.PULL_UP,
    rpi_gpio.PUD_DOWN: Resistor.PULL_DOWN
}
map_interrupt = {
    Interrupt.RISING: rpi_gpio.RISING,
    Interrupt.FALLING: rpi_gpio.FALLING,
    Interrupt.BOTH: rpi_gpio.BOTH,
    rpi_gpio.RISING: Interrupt.RISING,
    rpi_gpio.FALLING: Interrupt.FALLING,
    rpi_gpio.BOTH: Interrupt.BOTH
}


class rpiGPIO(baseGPIO):
    """
    GPIO Library Wrapper for RPi.GPIO
    """

    def __init__(self, mode=rpi_gpio.BCM):
        # supress the constant warnings
        rpi_gpio.setwarnings(False)
        if mode in [rpi_gpio.BCM, rpi_gpio.BOARD]:
            rpi_gpio.setmode(mode)
        else:
            raise ValueError("Unexpected value for mode, must be BCM or BOARD")

    def setup(self, pin, direction, resistor=Resistor.OFF):
        """
        Set the pin direction (input or output).
        """
        rpi_gpio.setup(
            pin,
            map_direction[direction],
            pull_up_down=map_resistor[resistor]
        )

    def output(self, pin, value):
        """
        Set the pin state (high or low).
        """
        rpi_gpio.output(pin, value)

    def input(self, pin):
        """
        Read the pin state (high or low).
        """
        return rpi_gpio.input(pin)

    def add_event_detect(self, pin, edge, callback, bouncetime=0):
        """
        Add a pin change interrupt with callback.
        """
        kwargs = {"callback": callback}
        if bouncetime:
            kwargs["bouncetime"] = bouncetime
        rpi_gpio.add_event_detect(pin, map_interrupt[edge], **kwargs)


    def remove_event_detect(self, pin):
        """
        Remove a pin change interurpt.
        """
        rpi_gpio.remove_event_detect(pin)

    def cleanup(self, pin=None):
        """
        Clean up interrupts for pin or all if pin is ``None``.
        """
        if pin is not None:
            rpi_gpio.cleanup(pin)
        else:
            rpi_gpio.cleanup()
