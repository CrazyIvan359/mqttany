"""
********************
Core GPIO Base Board
********************

:Author: Michael Murton
"""
# Copyright (c) 2019-2022 MQTTany contributors
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

__all__ = ["Board"]

import inspect
import multiprocessing as mproc
import os
import typing as t
from ctypes import c_char

import logger

from ..common import Mode, PinAlternate, PinBias, PinMode
from ..pins import SUPPORTED_PIN_MODES
from ..pins.base import Pin


class structPin:
    """Pin data struct used interally by boards."""

    def __init__(
        self,
        chip: int,
        line: int,
        pin_soc: int,
        pin_board: int,
        pin_wpi: int,
        modes: PinMode,
        biases: PinBias,
        alts: PinAlternate,
    ) -> None:
        self._chip = chip
        self._line = line
        self._soc = pin_soc
        self._board = pin_board
        self._wpi = pin_wpi
        self._modes = modes
        self._biases = biases
        self._alts = alts
        self._name = {
            Mode.SOC: f"GPIO{pin_soc:02d}",
            Mode.BOARD: f"board pin {pin_board}",
            Mode.WIRINGPI: f"WiringPi pin {pin_wpi}",
        }
        self._lock = mproc.Array(c_char, 24)
        if self.alts:
            # Lock pins in use by system
            if self.alts & PinAlternate.ANY_I2C:
                for i in range(6):
                    if self.alts & (
                        getattr(PinAlternate, f"I2C{i}_SDA")
                        | getattr(PinAlternate, f"I2C{i}_SCL")
                    ):
                        if os.access(
                            f"/dev/i2c{i}", os.F_OK, effective_ids=True
                        ) or os.access(f"/dev/i2c-{i}", os.F_OK, effective_ids=True):
                            self.lock(None, module=f"system.i2c{i}")

    @property
    def name(self) -> str:
        return self.get_name(Mode.SOC)

    @property
    def chip(self) -> int:
        return self._chip

    @property
    def line(self) -> int:
        return self._line

    @property
    def soc(self) -> int:
        return self._soc

    @property
    def board(self) -> int:
        return self._board

    @property
    def wpi(self) -> int:
        return self._wpi

    @property
    def modes(self) -> PinMode:
        return self._modes

    @property
    def biases(self) -> PinBias:
        return self._biases

    @property
    def alts(self) -> PinAlternate:
        return self._alts

    def get_name(self, mode: Mode) -> str:
        return self._name[mode]

    def lock(
        self,
        log: t.Optional[logger.mqttanyLogger] = None,
        mode: Mode = Mode.SOC,
        module: t.Optional[str] = None,
    ) -> bool:
        if not module:
            frm = inspect.stack()[2]
            module = ".".join(
                [
                    s
                    for s in inspect.getmodule(frm[0]).__name__.split(".")  # type: ignore
                    if s not in ["mqttany", "modules"]
                ]
            )

        if not self._lock.value:
            self._lock.raw = module.encode()  # type: ignore
            if log:
                log.debug(
                    "'%s' acquired lock on %s (%s)",
                    module,
                    self.get_name(mode),
                    self.name,
                )
            return True
        elif self._lock.raw.strip(bytes([0])).decode() == module:  # type: ignore
            if log:
                log.debug(
                    "'%s' already has a lock on %s (%s)",
                    module,
                    self.get_name(mode),
                    self.name,
                )
            return True
        else:
            if log:
                log.warn(
                    "'%s' failed to lock %s (%s), already locked by '%s'",
                    module,
                    self.get_name(mode),
                    self.name,
                    self._lock.raw.decode(),  # type: ignore
                )
        return False


class Board:
    """Base Board class."""

    def __init__(self) -> None:
        self._id: str = ""
        self._chips: t.List[int] = []
        self._pins: t.List[structPin] = []
        self._pin_lookup: t.Dict[Mode, t.Dict[int, structPin]] = {
            Mode.SOC: {},
            Mode.BOARD: {},
            Mode.WIRINGPI: {},
        }
        self.log = logger.get_logger("core.gpio.board")

    @property
    def chips(self) -> t.Tuple[int, ...]:
        """Returns a tuple of the gpiochip numbers available on this board."""
        return tuple(self._chips)

    @property
    def id(self) -> str:
        """Returns the detected board ID."""
        return self._id

    def _add_pin(
        self,
        chip: int,
        line: int,
        pin_soc: int,
        pin_board: int,
        pin_wpi: int,
        modes: PinMode,
        biases: PinBias = PinBias.NONE,
        alts: PinAlternate = PinAlternate.NONE,
    ) -> None:
        """Add a pin to this board."""
        if chip not in self._chips:
            self._chips.append(chip)
        self._pins.append(
            structPin(chip, line, pin_soc, pin_board, pin_wpi, modes, biases, alts)
        )
        self._pin_lookup[Mode.SOC][pin_soc] = self._pins[-1]
        if pin_board > -1:
            self._pin_lookup[Mode.BOARD][pin_board] = self._pins[-1]
        if pin_wpi > -1:
            self._pin_lookup[Mode.WIRINGPI][pin_wpi] = self._pins[-1]

    def valid(self, pin: int, mode: Mode, pin_mode: PinMode) -> bool:
        """
        Returns ``True`` if ``pin`` is valid for ``pin_mode`` on this board.
        """
        if pin in self._pin_lookup[mode]:
            if self._pin_lookup[mode][pin].modes & pin_mode:
                return True
            else:
                self.log.error(
                    "%s cannot be used as %s",
                    self._pin_lookup[mode][pin].name.capitalize(),
                    pin_mode.name,
                )
        else:
            self.log.error(
                "%s is not available on this board",
                {
                    Mode.SOC: "GPIO{:02d}",
                    Mode.BOARD: "Board pin {}",
                    Mode.WIRINGPI: "WiringPi pin {}",
                }[mode].format(pin),
            )
        return False

    def lock(self, pin: int, mode: Mode) -> bool:
        """
        Acquire a lock on a pin (this is done automatically in ``get_pin``).
        Returns ``True`` if a lock is acquired, ``False`` otherwise.
        """
        if pin in self._pin_lookup[mode]:
            return self._pin_lookup[mode][pin].lock(self.log, mode)
        else:
            self.log.error(
                "%s is not available on this board",
                {
                    Mode.SOC: "GPIO{:02d}",
                    Mode.BOARD: "Board pin {}",
                    Mode.WIRINGPI: "WiringPi pin {}",
                }[mode].format(pin),
            )
        return False

    def get_pin(
        self, pin: int, mode: Mode, pin_mode: PinMode, **kwargs: t.Any
    ) -> t.Union[Pin, None]:
        """
        Returns an instance of ``Pin``, subclassed based on ``pin_mode``.

        Locks a GPIO pin to a module and returns a class instance used to interact
        with the hardware pin specified.

        Args:
            - pin (int): pin number under ``mode`` numbering.
            - mode (Mode): pin numbering mode to use, also affects the name returned by
              ``pin.name``.
            - pin_mode (PinMode): pin function desired, ex ``Digital``.
            - kwargs: each pin subclass may require additional args, look in ``gpio.pins``
              for details.

        Returns:
            A subclassed instance of ``Pin`` based on ``pin_mode``, or ``None``. If
            ``None`` is returned it may be because the pin is already in use, the pin
            is not available for use as ``pin_mode``, or the pin is not available on
            this board.
        """
        if self.valid(pin, mode, pin_mode):
            pin_object = self._pin_lookup[mode][pin]
            if (
                kwargs.get("bias", PinBias.NONE) != PinBias.NONE
                and not pin_object.biases & kwargs["bias"]
            ):
                self.log.warn(
                    "%s does not support bias %s, defaulting to %s",
                    pin_object.name,
                    kwargs["bias"].name,
                    PinBias.NONE.name,  # pylint: disable=no-member
                )
                kwargs["bias"] = PinBias.NONE

            if pin_object.lock(self.log, mode):
                return SUPPORTED_PIN_MODES[pin_mode](
                    gpio_mode=mode,
                    chip=pin_object.chip,
                    line=pin_object.line,
                    pin_soc=pin_object.soc,
                    pin_board=pin_object.board,
                    pin_wpi=pin_object.wpi,
                    pin_mode=pin_mode,
                    **kwargs,
                )
        return None
