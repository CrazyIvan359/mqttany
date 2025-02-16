"""
*********************
Core GPIO Digital Pin
*********************

:Author: Michael Murton
"""
# Copyright (c) 2019-2025 MQTTany contributors
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

__all__ = ["SUPPORTED_PIN_MODES"]

import threading
import typing as t
from datetime import datetime
from time import sleep

from logger import get_logger, log_traceback
from periphery.gpio import GPIO, GPIOError

from .. import common
from ..common import Mode, PinBias, PinEdge, PinMode
from .base import Pin

now = datetime.now
log = get_logger("core.gpio.pin.digital")

periphery_PinMode = {PinMode.INPUT: "in", PinMode.OUTPUT: "out"}
periphery_PinBias = {
    PinBias.NONE: "default",  # "disable" returns err 22 invalid arg
    PinBias.PULL_UP: "pull_up",
    PinBias.PULL_DOWN: "pull_down",
}
periphery_PinEdge = {
    PinEdge.NONE: "none",
    PinEdge.RISING: "rising",
    PinEdge.FALLING: "falling",
    PinEdge.BOTH: "both",
}


class Digital(Pin):
    """
    Digital GPIO Pin

    Additional args that can be provided to ``Board.get_pin``:
        - bias (PinBias): pin bias setting.
        - edge (PinEdge): interrupt edge triggers.
        - interrupt_callback (function): a function to call when an interrupt fires.
          This function **MUST** be thread-safe as it will be run in its own thread.
        - interrupt_debounce (int): edge debounce period in milliseconds.
    """

    def __init__(
        self,
        gpio_mode: Mode,
        chip: int,
        line: int,
        pin_soc: int,
        pin_board: int,
        pin_wpi: int,
        pin_mode: PinMode,
        bias: PinBias = PinBias.NONE,
        edge: PinEdge = PinEdge.NONE,
        interrupt_callback: t.Optional[
            t.Callable[[bool], t.Any]
        ] = None,  # MUST be thread-safe
        interrupt_debounce: int = 50,  # sensible default 50ms
    ) -> None:
        super().__init__(gpio_mode, chip, line, pin_soc, pin_board, pin_wpi, pin_mode)
        self._bias = bias
        self._edge = edge
        self._interrupt_handler: Interrupt = None  # type: ignore
        self._interrupt_callback = (
            interrupt_callback if callable(interrupt_callback) else None
        )
        self._interrupt_debounce = interrupt_debounce
        self._interface: GPIO = None  # type: ignore
        self._setup = False

    def __del__(self) -> None:
        self.cleanup()

    @property
    def bias(self) -> PinBias:
        """Returns the pin bias resistor setting."""
        return self._bias

    @property
    def edge(self) -> PinEdge:
        """Returns the pin interrupt edge trigger."""
        return self._edge

    def set_callback(self, callback: t.Callable[[bool], t.Any]) -> None:
        """Change the interrupt callback"""
        if callable(callback):
            self._interrupt_callback = callback

    def setup(self) -> bool:
        """Setup the pin before use, returns ``True`` on success."""
        if not self._setup:
            sysfs_failover = True
            if common.cdev:
                if self._bias != PinBias.NONE and not common.cdev_bias:
                    self._bias = PinBias.NONE
                    log.warn(
                        "Unable to set resistor on %s, this requires a kernel version "
                        "of 5.5 or higher",
                        self.name,
                    )
                if self._setup_cdev():
                    if self.edge:
                        self._interrupt_handler = cdevInterrupt(self)
                    self._setup = True
                    sysfs_failover = False
            if common.sysfs and sysfs_failover:
                if self._bias != PinBias.NONE:
                    self._bias = PinBias.NONE
                    log.warn(
                        "Unable to set resistor on %s as sysfs does not support this",
                        self.name,
                    )
                if self._setup_sysfs():
                    if self.edge:
                        self._interrupt_handler = sysfsInterrupt(self)
                    self._setup = True
            if self._setup and self._edge:
                self._interrupt_handler.start()

        return self._setup

    def _set_bias_pinctrl(self):
        """
        For cdev on kernel <5.5 and sysfs, attempts to set bias resistor using `ioctl`
        calls to `pinctrl`
        """
        pass

    def _setup_cdev(self) -> bool:
        try:
            log.debug("Setting up pin %s using chardev", self.name)
            self._interface = GPIO(
                f"/dev/gpiochip{self.chip}",
                self.line,
                periphery_PinMode[self.mode],
                edge=periphery_PinEdge[self.edge],
                bias="default"
                if not common.cdev_bias
                else periphery_PinBias[self.bias],
                label="MQTTany",
            )
        except GPIOError as err:
            if err.errno == 16:  # Device or resource busy
                log.error("Failed to setup %s using cdev, pin is in use", self.name)
            elif err.errno == 22:  # Invalid arg (this is not a user error!)
                log.error(
                    "Failed to setup %s using cdev, an invalid argument was given",
                    self.name,
                )
            else:
                log.error("Failed to setup %s using cdev", self.name)
                log_traceback(log)
        except LookupError:
            log.error(
                "Unable to setup %s using cdev, line %d not found on gpiochip%s",
                self.name,
                self.line,
                self.chip,
            )
        else:
            return True
        return False

    def _setup_sysfs(self) -> bool:
        try:
            log.debug("Setting up pin %s using sysfs", self.name)
            self._interface = GPIO(self.soc, periphery_PinMode[self.mode])
        except GPIOError as err:
            if err.errno == 16:  # Device or resource busy
                log.error("Failed to setup %s using sysfs, pin is in use", self.name)
            else:
                log.error("Failed to setup %s using sysfs", self.name)
                log_traceback(log)
        except TimeoutError:
            log.error(
                "Unable to setup %s using sysfs, system calls timed out", self.name
            )
        else:
            return True
        return False

    def read(self) -> t.Union[bool, None]:
        """Read the pin state."""
        if self._setup:
            try:
                return self._interface.read()
            except GPIOError:
                log_traceback(log)
                return None

    input = read
    get = read

    def write(self, state: bool) -> None:
        """Write the state of the pin."""
        if self._setup:
            try:
                self._interface.write(state)
            except GPIOError as err:
                if err.errno == 1:  # Operation not permitted
                    log.error(
                        "Failed to write to to %s, operation not permitted", self.name
                    )
                elif err.errno == 22:  # Invalid arg (this is not a user error!)
                    log.error(
                        "Failed to setup %s using cdev, an invalid argument was given",
                        self.name,
                    )
                else:
                    log_traceback(log)
                raise

    output = write
    set = write

    def cleanup(self) -> None:
        """Perform cleanup when shutting down."""
        if self._interrupt_handler:
            self._interrupt_handler.stop()
        if self._interface:
            try:
                self._interface.close()
            except GPIOError:
                log.error("An error occurred while closing %s", self.name)
                log_traceback(log)


class Interrupt:
    def __init__(
        self,
        pin: Digital,
    ) -> None:
        self._pin = pin
        self._edge = pin.edge
        self._debounce_s = pin._interrupt_debounce / 1000.0  # type: ignore
        self._state: t.Union[bool, None] = None
        self._state_last: t.Union[bool, None] = None
        self._start_s: float = 0
        self._debounce_thread: t.Union[threading.Thread, None] = None
        self._debounce_kill = threading.Event()
        self._poll_thread: t.Union[threading.Thread, None] = None
        self._poll_kill = threading.Event()

    def __del__(self) -> None:
        self.stop()

    def _poll(self) -> None:
        while not self._poll_kill.is_set():
            if self._pin._interface.poll(1):  # type: ignore
                self._state, self._start_s = self.get_event()
                if self._start_s:
                    if self._debounce_thread:
                        self._debounce_kill.set()
                        self._debounce_thread.join()
                    if self._state is not None:
                        self._debounce_thread = threading.Thread(target=self._debounce)
                        self._debounce_thread.start()
                        log.trace(
                            "%s edge detected on pin %s with timestamp %.6fs",
                            "Rising" if self._state else "Falling",
                            self._pin.name,
                            self._start_s,
                        )

    def _debounce(self):
        end_us = self._start_s + self._debounce_s
        while not self._debounce_kill.is_set() and end_us > now().timestamp():
            sleep(0.0005)  # 0.5ms
        if not self._debounce_kill.is_set() and self._state == self._pin.read():
            if callable(self._pin._interrupt_callback):  # type: ignore
                threading.Thread(
                    target=self._pin._interrupt_callback, args=(self._state,)  # type: ignore
                ).run()
        self._debounce_kill.clear()
        self._debounce_thread = None

    def start(self) -> None:
        self._state_last = self._pin.read()
        self._poll_thread = threading.Thread(target=self._poll)
        self._poll_thread.start()

    def stop(self) -> None:
        self._poll_kill.set()
        if self._poll_thread:
            self._poll_thread.join(1)
        self._debounce_kill.set()
        if self._debounce_thread:
            self._debounce_thread.join(1)

    def get_event(self) -> t.Tuple[t.Union[bool, None], float]:
        raise NotImplementedError


class cdevInterrupt(Interrupt):
    def get_event(self) -> t.Tuple[t.Union[bool, None], float]:
        event = self._pin._interface.read_event()  # type: ignore
        return (
            event.edge == periphery_PinEdge[PinEdge.RISING],
            # round(event.timestamp / 1000000000.0, 6),
            now().timestamp(),
        )


class sysfsInterrupt(Interrupt):
    def get_event(self) -> t.Tuple[t.Union[bool, None], float]:
        state = self._pin.read()
        if (state != self._state_last) and (
            (state and self._edge & PinEdge.RISING)
            or (not state and self._edge & PinEdge.FALLING)
        ):
            self._state_last = state
            return state, now().timestamp()
        return None, 0


SUPPORTED_PIN_MODES: t.Dict[PinMode, t.Type[Pin]] = {
    PinMode.INPUT: Digital,
    PinMode.OUTPUT: Digital,
}
