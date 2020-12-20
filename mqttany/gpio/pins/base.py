"""
******************
Core GPIO Base Pin
******************

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

__all__ = ["Pin"]

import typing as t

from ..common import Mode, PinMode


class Pin:
    """Base GPIO Pin class."""

    def __init__(
        self,
        gpio_mode: Mode,
        chip: int,
        line: int,
        pin_soc: int,
        pin_board: int,
        pin_wpi: int,
        pin_mode: PinMode,
    ) -> None:
        self._gpio_mode = gpio_mode
        self._chip = chip
        self._line = line
        self._mode = pin_mode
        self._setup: bool = False
        self._pin = {Mode.SOC: pin_soc, Mode.BOARD: pin_board, Mode.WIRINGPI: pin_wpi}
        self._name = {
            Mode.SOC: f"GPIO{pin_soc:02d}",
            Mode.BOARD: f"board pin {pin_board}",
            Mode.WIRINGPI: f"WiringPi pin {pin_wpi}",
        }

    @property
    def chip(self) -> int:
        """Return the gpiochip number used with cdev."""
        return self._chip

    @property
    def line(self) -> int:
        """Return the gpiochip line number used with cdev."""
        return self._line

    @property
    def soc(self) -> int:
        """Return the SoC/GPIO pin number."""
        return self.pin(Mode.SOC)

    @property
    def board(self) -> int:
        """Returns the physical pin number."""
        return self.pin(Mode.BOARD)

    @property
    def wpi(self) -> int:
        """Returns the WiringPi pin number."""
        return self.pin(Mode.WIRINGPI)

    @property
    def name(self) -> str:
        """Returns a logging friendly name for this pin."""
        return self.get_name()

    @property
    def mode(self) -> PinMode:
        """Returns the pin mode."""
        return self._mode

    def pin(self, mode: Mode) -> int:
        """Returns the pin number under ``mode``."""
        return self._pin[mode]

    def get_name(self, mode: t.Optional[Mode] = None) -> str:
        """Returns a logging friendly name for this pin using ``mode`` numbering."""
        return self._name[mode or self._gpio_mode]

    def setup(self) -> bool:
        """Setup the pin before use, returns ``True`` on success."""
        raise NotImplementedError

    def cleanup(self) -> None:
        """Perform cleanup when shutting down."""
        self._setup = False
