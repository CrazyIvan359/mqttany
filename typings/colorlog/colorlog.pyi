import typing as t
import logging


class ColoredFormatter(logging.Formatter):
    """
    A formatter that allows colors to be placed in the format string.

    Intended to help in creating more readable logging output.
    """

    def __init__(
        self,
        fmt: t.Optional[str] = ...,
        datefmt: t.Optional[str] = ...,
        style: t.Optional[str] = ...,
        log_colors: t.Optional[t.Dict[str, str]] = ...,
        reset: t.Optional[bool] = ...,
        secondary_log_colors: t.Optional[t.Dict[str, t.Dict[str, str]]] = ...,
    ) -> None:
        ...
