from typing import Any, List, NamedTuple, Tuple, Type, Union


class GPIOError(IOError):
    ...


class EdgeEvent(NamedTuple("EdgeEvent", Tuple[str, int])):
    edge: str
    timestamp: float

    def __new__(cls, edge: str, timestamp: int) -> Type[EdgeEvent]:
        ...


class GPIO(object):
    def __new__(cls, *args: Any, **kwargs: Any) -> Type[GPIO]:
        ...

    def __del__(self) -> None:
        ...

    def __enter__(self) -> Type[GPIO]:
        ...

    def __exit__(self, t: Any, value: Any, traceback: Any) -> None:
        ...

    # Methods
    def read(self) -> bool:
        ...

    def write(self, value: bool) -> None:
        ...

    def poll(self, timeout: Union[int, float, None] = ...) -> bool:
        ...

    def read_event(self) -> Type[EdgeEvent]:
        ...

    @staticmethod
    def poll_multiple(
        gpios: List[Type[GPIO]], timeout: Union[int, float, None] = ...
    ) -> List[Type[GPIO]]:
        ...

    def close(self) -> None:
        ...

    # Immutable properties
    @property
    def devpath(self) -> str:
        ...

    @property
    def fd(self) -> int:
        ...

    @property
    def line(self) -> int:
        ...

    @property
    def name(self) -> str:
        ...

    @property
    def label(self) -> str:
        ...

    @property
    def chip_fd(self) -> int:
        ...

    @property
    def chip_name(self) -> str:
        ...

    @property
    def chip_label(self) -> str:
        ...

    # Mutable properties
    def _get_direction(self) -> str:
        ...

    def _set_direction(self, direction: str) -> None:
        ...

    direction = property(_get_direction, _set_direction)

    def _get_edge(self) -> str:
        ...

    def _set_edge(self, edge: str) -> None:
        ...

    edge = property(_get_edge, _set_edge)

    def _get_bias(self) -> str:
        ...

    def _set_bias(self, bias: str) -> None:
        ...

    bias = property(_get_bias, _set_bias)

    def _get_drive(self) -> str:
        ...

    def _set_drive(self, drive: str) -> None:
        ...

    drive = property(_get_drive, _set_drive)

    def _get_inverted(self) -> bool:
        ...

    def _set_inverted(self, inverted: bool) -> None:
        ...

    inverted = property(_get_inverted, _set_inverted)

    # String representation
    def __str__(self) -> str:
        ...


class CdevGPIO(GPIO):
    # Constants scraped from <linux/gpio.h>
    _GPIOHANDLE_GET_LINE_VALUES_IOCTL = 0xC040B408
    _GPIOHANDLE_SET_LINE_VALUES_IOCTL = 0xC040B409
    _GPIO_GET_CHIPINFO_IOCTL = 0x8044B401
    _GPIO_GET_LINEINFO_IOCTL = 0xC048B402
    _GPIO_GET_LINEHANDLE_IOCTL = 0xC16CB403
    _GPIO_GET_LINEEVENT_IOCTL = 0xC030B404
    _GPIOHANDLE_REQUEST_INPUT = 0x1
    _GPIOHANDLE_REQUEST_OUTPUT = 0x2
    _GPIOHANDLE_REQUEST_ACTIVE_LOW = 0x4
    _GPIOHANDLE_REQUEST_OPEN_DRAIN = 0x8
    _GPIOHANDLE_REQUEST_OPEN_SOURCE = 0x10
    _GPIOHANDLE_REQUEST_BIAS_PULL_UP = 0x20
    _GPIOHANDLE_REQUEST_BIAS_PULL_DOWN = 0x40
    _GPIOHANDLE_REQUEST_BIAS_DISABLE = 0x80
    _GPIOEVENT_REQUEST_RISING_EDGE = 0x1
    _GPIOEVENT_REQUEST_FALLING_EDGE = 0x2
    _GPIOEVENT_REQUEST_BOTH_EDGES = 0x3
    _GPIOEVENT_EVENT_RISING_EDGE = 0x1
    _GPIOEVENT_EVENT_FALLING_EDGE = 0x2

    def __init__(
        self,
        path: str,
        line: Union[int, str],
        direction: str,
        edge: str = ...,
        bias: str = ...,
        drive: str = ...,
        inverted: bool = ...,
        label: str = ...,
    ) -> Type[CdevGPIO]:
        ...

    def __new__(
        self, path: str, line: Union[int, str], direction: str, **kwargs: Any  # type: ignore
    ) -> Type[CdevGPIO]:
        ...

    def _open(
        self,
        path: str,
        line: Union[int, str],
        direction: str,
        edge: str,
        bias: str,
        drive: str,
        inverted: bool,
        label: str,
    ) -> None:
        ...

    def _reopen(
        self, direction: str, edge: str, bias: str, drive: str, inverted: bool
    ) -> None:
        ...

    def _find_line_by_name(self, path: str, line: str) -> int:
        ...

    # Methods

    def read(self) -> bool:
        ...

    def write(self, value: bool) -> None:
        ...

    def poll(self, timeout: Union[int, float, None] = ...) -> bool:
        ...

    def read_event(self) -> type[EdgeEvent]:
        ...

    def close(self) -> None:
        ...

    # Immutable properties

    @property
    def devpath(self) -> str:
        ...

    @property
    def fd(self) -> int:
        ...

    @property
    def line(self) -> int:
        ...

    @property
    def name(self) -> str:
        ...

    @property
    def label(self) -> str:
        ...

    @property
    def chip_fd(self) -> int:
        ...

    @property
    def chip_name(self) -> str:
        ...

    @property
    def chip_label(self) -> str:
        ...

    # Mutable properties

    def _get_direction(self) -> str:
        ...

    def _set_direction(self, direction: str) -> None:
        ...

    direction = property(_get_direction, _set_direction)

    def _get_edge(self) -> str:
        ...

    def _set_edge(self, edge: str) -> None:
        ...

    edge = property(_get_edge, _set_edge)

    def _get_bias(self) -> str:
        ...

    def _set_bias(self, bias: str) -> None:
        ...

    bias = property(_get_bias, _set_bias)

    def _get_drive(self) -> str:
        ...

    def _set_drive(self, drive: str) -> None:
        ...

    drive = property(_get_drive, _set_drive)

    def _get_inverted(self) -> bool:
        ...

    def _set_inverted(self, inverted: bool) -> None:
        ...

    inverted = property(_get_inverted, _set_inverted)

    # String representation

    def __str__(self) -> str:
        ...


class SysfsGPIO(GPIO):
    # Number of retries to check for GPIO export or direction write on open
    GPIO_OPEN_RETRIES = 10
    # Delay between check for GPIO export or direction write on open (100ms)
    GPIO_OPEN_DELAY = 0.1

    def __init__(self, line: int, direction: str) -> Type[SysfsGPIO]:
        ...

    def __new__(self, line: int, direction: str) -> Type[SysfsGPIO]:  # type: ignore
        ...

    def _open(self, line: int, direction: str) -> None:
        ...

    # Methods

    def read(self) -> bool:
        ...

    def write(self, value: bool) -> None:
        ...

    def poll(self, timeout: Union[int, float, None] = ...) -> bool:
        ...

    def read_event(self) -> None:
        ...

    def close(self) -> None:
        ...

    # Immutable properties

    @property
    def devpath(self) -> str:
        ...

    @property
    def fd(self) -> int:
        ...

    @property
    def line(self) -> int:
        ...

    @property
    def name(self) -> str:
        ...

    @property
    def label(self) -> str:
        ...

    @property
    def chip_fd(self) -> None:
        ...

    @property
    def chip_name(self) -> str:
        ...

    @property
    def chip_label(self) -> str:
        ...

    # Mutable properties

    def _get_direction(self) -> str:
        ...

    def _set_direction(self, direction: str) -> None:
        ...

    def _get_edge(self) -> str:
        ...

    def _set_edge(self, edge: str) -> None:
        ...

    edge = property(_get_edge, _set_edge)

    def _get_bias(self) -> None:
        ...

    def _set_bias(self, bias: str) -> None:
        ...

    bias = property(_get_bias, _set_bias)

    def _get_drive(self) -> None:
        ...

    def _set_drive(self, drive: str) -> None:
        ...

    drive = property(_get_drive, _set_drive)

    def _get_inverted(self) -> bool:
        ...

    def _set_inverted(self, inverted: bool) -> None:
        ...

    inverted = property(_get_inverted, _set_inverted)

    # String representation

    def __str__(self) -> str:
        ...
