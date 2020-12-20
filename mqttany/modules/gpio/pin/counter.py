"""
****************
GPIO Counter Pin
****************

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

__all__ = ["SUPPORTED_PIN_MODES", "CONF_OPTIONS"]

import enum
import statistics
import threading
import typing as t
from datetime import datetime

import logger
from common import BusProperty, DataType, PublishMessage
from gpio import Mode, PinBias, PinEdge, PinMode, board

from .. import common
from ..common import CONF_KEY_PIN_MODE, CONFIG
from .base import Pin

now = datetime.now


class Unit(enum.Enum):
    SECONDS = 1
    MILLIS = 1000
    NANOS = 1000000


class Function(enum.Enum):
    RAW = 1
    COUNT = enum.auto()
    AVERAGE = enum.auto()
    MEDIAN = enum.auto()
    MIN = enum.auto()
    MAX = enum.auto()
    FREQ_AVG = enum.auto()
    FREQ_MIN = enum.auto()
    FREQ_MAX = enum.auto()


CONF_KEY_DEBOUNCE = "debounce"  # added by Digital
CONF_KEY_RESISTOR = "resistor"  # added by Digital
CONF_KEY_COUNTER = "counter"
CONF_KEY_INTERVAL = "interval"
CONF_KEY_INTERRUPT = "interrupt"
CONF_KEY_FUNCTION = "function"
CONF_KEY_UNIT = "unit"
CONF_KEY_DIVIDER = "divider"

CONF_OPTIONS: t.MutableMapping[str, t.Dict[str, t.Any]] = {
    "regex:.+": {
        CONF_KEY_PIN_MODE: {
            "selection": {"counter": "COUNTER"},
        },
        CONF_KEY_COUNTER: {
            "type": "section",
            "conditions": [(CONF_KEY_PIN_MODE, "COUNTER")],
            CONF_KEY_INTERVAL: {"default": 60, "type": int},
            CONF_KEY_INTERRUPT: {
                "default": PinEdge.RISING,
                "selection": {
                    "rising": PinEdge.RISING,
                    "falling": PinEdge.FALLING,
                    "both": PinEdge.BOTH,
                },
            },
            CONF_KEY_FUNCTION: {
                "default": Function.COUNT,
                "selection": {
                    "raw": Function.RAW,
                    "count": Function.COUNT,
                    "average": Function.AVERAGE,
                    "median": Function.MEDIAN,
                    "min": Function.MIN,
                    "max": Function.MAX,
                    "frequency": Function.FREQ_AVG,
                    "frequency average": Function.FREQ_AVG,
                    "frequency min": Function.FREQ_MIN,
                    "frequency max": Function.FREQ_MAX,
                },
            },
            CONF_KEY_UNIT: {
                "default": Unit.MILLIS,
                "selection": {
                    "s": Unit.SECONDS,
                    "seconds": Unit.SECONDS,
                    "ms": Unit.MILLIS,
                    "millis": Unit.MILLIS,
                    "milliseconds": Unit.MILLIS,
                    "ns": Unit.NANOS,
                    "nanos": Unit.NANOS,
                    "nanoseconds": Unit.NANOS,
                },
            },
            CONF_KEY_DIVIDER: {"default": 1, "type": int},
        },
    }
}


class CounterEvent(t.NamedTuple):
    timestamp: float
    delta: float


class Counter(Pin):
    """
    GPIO Counter Pin class
    """

    def __init__(
        self,
        pin: int,
        gpio_mode: Mode,
        id: str,
        name: str,
        pin_config: t.Dict[str, t.Any] = {},
    ) -> None:
        pin_config[CONF_KEY_PIN_MODE] = PinMode.INPUT
        super().__init__(pin, gpio_mode, id, name, pin_config)
        self._log = logger.get_logger("gpio.counter")
        self._bias: PinBias = pin_config.get(CONF_KEY_RESISTOR, PinBias.NONE)
        self._interval: int = max(pin_config[CONF_KEY_COUNTER][CONF_KEY_INTERVAL], 5)
        self._edge: PinEdge = pin_config[CONF_KEY_COUNTER][CONF_KEY_INTERRUPT]
        self._function: Function = pin_config[CONF_KEY_COUNTER][CONF_KEY_FUNCTION]
        self._unit: Unit = pin_config[CONF_KEY_COUNTER][CONF_KEY_UNIT]
        self._divider = float(pin_config[CONF_KEY_COUNTER][CONF_KEY_DIVIDER])
        self._timer: t.Union[threading.Timer, None] = None
        self._data_lock = threading.Lock()
        self._data: t.List[CounterEvent] = []
        self._functions: t.Dict[
            Function, t.Callable[[t.List[float]], t.Union[float, str]]
        ] = {
            Function.RAW: lambda data: f'{{"pulses": {[round(f * self._unit.value) for f in data]}}}',
            Function.COUNT: lambda data: len(data) * self._divider,
            Function.AVERAGE: lambda data: getattr(  # use fmean if available
                statistics, "fmean", statistics.mean
            )([round(f * self._unit.value) for f in data])
            * self._divider,
            Function.MEDIAN: lambda data: statistics.median(
                [round(f * self._unit.value) for f in data]
            )
            * self._divider,
            Function.MIN: lambda data: min([round(f * self._unit.value) for f in data])
            * self._divider,
            Function.MAX: lambda data: max([round(f * self._unit.value) for f in data])
            * self._divider,
            Function.FREQ_AVG: lambda data: round(
                1.0
                / (getattr(statistics, "fmean", statistics.mean)(data))
                * self._divider,
                3,
            ),
            Function.FREQ_MIN: lambda data: round(1.0 / (min(data) * self._divider), 3),
            Function.FREQ_MAX: lambda data: round(1.0 / (max(data) * self._divider), 3),
        }
        self._handle = board.get_pin(
            pin=pin,
            mode=gpio_mode,
            pin_mode=self._mode,
            bias=self._bias,
            edge=self._edge,
            interrupt_callback=self.interrupt,
            interrupt_debounce=CONFIG[CONF_KEY_DEBOUNCE],
        )
        if self._handle:
            self._log.debug(
                "Configured '%s' on %s with options: %s",
                self._name,
                self.pin_name,
                {
                    "ID": self.id,
                    CONF_KEY_PIN_MODE: "COUNTER",
                    CONF_KEY_INTERRUPT: self._edge.name,
                    CONF_KEY_RESISTOR: self._bias.name,
                    CONF_KEY_FUNCTION: self._function.name,
                    CONF_KEY_UNIT: self._unit.name,
                    CONF_KEY_DIVIDER: self._divider,
                },
            )

    def get_property(self) -> BusProperty:
        return BusProperty(
            name=self.name,
            datatype=DataType.STR if self._function == Function.RAW else DataType.FLOAT,
        )

    def setup(self) -> bool:
        """
        Configures the pin in hardware, returns ``True`` on success
        """
        if self._handle:
            self._log.info(
                "Setting up '%s' on %s as %s",
                self.name,
                self.pin_name,
                self._mode.name,
            )
            if self._handle.setup():
                self._setup = True
                self._timer = threading.Timer(self._interval, self.report)
                self._timer.start()
        else:
            self._log.warn(
                "Unable to setup '%s' as %s, no available pin class",
                self.name,
                self._mode.name,
            )

        return self._setup

    def cleanup(self) -> None:
        """
        Cleanup actions when stopping
        """
        if self._setup and self._timer:
            self._timer.cancel()
            self._timer = None
        super().cleanup()

    def publish_state(self) -> None:
        """No-op. Counters operate using their own timing."""

    def message_callback(self, path: str, content: str) -> None:
        """
        Handles messages on the pin's paths. Path will have the pin's path removed,
        ex. path may only be ``set``.
        """
        if self._setup:
            self._log.trace(
                "Received unrecognized message on '%s' for '%s' on %s: %s",
                path,
                self.name,
                self.pin_name,
                content,
            )

    def interrupt(self, state: bool) -> None:
        now_ns = now().timestamp()
        self._data_lock.acquire()
        try:
            self._data.append(
                CounterEvent(now_ns, (now_ns - self._data[-1][0]) if self._data else 0)
            )
        finally:
            self._data_lock.release()

    def report(self) -> None:
        """Report counter data"""
        end_ns = now().timestamp()
        self._timer = threading.Timer(self._interval, self.report)
        self._timer.start()
        start_ns = end_ns - self._interval

        self._log.trace("start: %s", start_ns)
        self._log.trace("  end: %s", end_ns)
        self._log.trace("self._data: %s", self._data)

        data = [
            event[1]
            for event in self._data
            if event[0] <= end_ns and event[0] > start_ns
        ]
        self._log.trace("data: %s", data)
        if data:
            self._data_lock.acquire()
            try:
                # keep the last record selected for this report in case it is
                # needed to calculate delta for next event
                self._data = self._data[
                    len([event for event in self._data if event[0] <= end_ns]) - 1 :
                ]
            finally:
                self._data_lock.release()

            message = self._functions[self._function](data)
        else:
            if self._function == Function.RAW:
                message = self._functions[Function.RAW](data)
            else:
                message = 0

        self._log.debug(
            "Selected %d events from '%s' on %s using %s gives: %s",
            len(data),
            self.name,
            self.pin_name,
            self._function.name,
            message,
        )
        common.publish_queue.put_nowait(PublishMessage(path=self.path, content=message))


SUPPORTED_PIN_MODES: t.Dict[t.Union[PinMode, str], t.Type[Pin]] = {"COUNTER": Counter}
