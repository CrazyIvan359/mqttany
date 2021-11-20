"""
******
Logger
******

:Author: Michael Murton
"""
# Copyright (c) 2019-2021 MQTTany contributors
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

__all__ = ["get_logger", "set_level", "log_traceback", "uninit", "LogLevel"]

import enum
import errno
import inspect
import logging
import os
import sys
import traceback
from logging import DEBUG, ERROR, INFO, NOTSET
from logging import WARNING as WARN
from logging import handlers
import colorlog

try:
    import typing as t
except ModuleNotFoundError:
    pass

_LOG_FILE = os.path.join(os.path.dirname(__file__), "log", "mqttany.log")

_LOG_LEN_LEVEL = 5
_LOG_LEN_PROCESS = 8
_LOG_LEN_NAME = 24
_LOG_FORMAT_FILE = (
    "%(asctime)s [%(levelname)-{level}s] [%(name)-{name}s] %(message)s".format(
        level=_LOG_LEN_LEVEL, name=_LOG_LEN_NAME
    )
)
_LOG_FORMAT_FILE_DEBUG = (
    "%(asctime)s [%(levelname)-{level}s] [%(processName)-{process}.{process}s] "
    "[%(name)-{name}s] %(message)s".format(
        level=_LOG_LEN_LEVEL, process=_LOG_LEN_PROCESS, name=_LOG_LEN_NAME
    )
)
_LOG_FORMAT_TERM = (
    "%(asctime)s [%(log_color)s%(levelname)-{level}s%(reset)s] [%(name)-{name}s] "
    "%(message_log_color)s%(message)s".format(level=_LOG_LEN_LEVEL, name=_LOG_LEN_NAME)
)
_LOG_FORMAT_TERM_DEBUG = (
    "%(asctime)s [%(log_color)s%(levelname)-{level}s%(reset)s] [%(processName)-{process}.{process}s] "
    "[%(name)-{name}s] %(message_log_color)s%(message)s".format(
        level=_LOG_LEN_LEVEL, process=_LOG_LEN_PROCESS, name=_LOG_LEN_NAME
    )
)
_LOG_COLORS = {
    "TRACE": "white",
    "DEBUG": "bold_white",
    "INFO": "bold_green",
    "WARN": "bold_yellow",
    "ERROR": "bold_red",
    "CRITICAL": "bold_red",
}
_LOG_SECONDARY_COLORS = {
    "message": {
        "DEBUG": "bold",
        "INFO": "bold_green",
        "WARN": "bold_yellow",
        "ERROR": "bold_red",
        "CRITICAL": "bold_red",
    }
}

_log_handlers: t.List[logging.Handler] = []  # type:ignore


class LogLevel(enum.IntEnum):
    TRACE = 5
    DEBUG = DEBUG
    INFO = INFO
    WARN = WARN
    ERROR = ERROR
    NOTSET = NOTSET


class mqttanyLogger(logging.Logger):
    def __init__(self, name, level=LogLevel.NOTSET.value):
        # type: (str, int) -> None
        super().__init__(name, level)

    def trace(self, msg, *args, **kwargs):
        # type: (t.Any, t.Any, t.Any) -> None
        """
        Log 'msg % args' with severity 'TRACE'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.trace("Houston, we have a %s", "thorny problem", exc_info=1)
        """
        if self.isEnabledFor(LogLevel.TRACE.value):
            self._log(LogLevel.TRACE.value, msg, args, **kwargs)

    def warn(self, msg, *args, **kwargs):  # type: ignore
        # type: (t.Any, t.Any, t.Any) -> None
        """
        Log 'msg % args' with severity 'WARN'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.warn("Houston, we have a %s", "thorny problem", exc_info=1)
        """
        # Added because ``warn`` is depreciated in Python 3.7 but I want to keep
        # log level to less than 5 characters
        if self.isEnabledFor(LogLevel.WARN.value):
            self._log(LogLevel.WARN.value, msg, args, **kwargs)


def _init_logger():
    # type: () -> mqttanyLogger
    """
    Creates the root logger for MQTTany
    """
    logging.addLevelName(LogLevel.WARN.value, "WARN")
    logging.addLevelName(LogLevel.TRACE.value, "TRACE")
    logging.setLoggerClass(mqttanyLogger)

    log = logging.getLogger("mqttany")
    log.setLevel(LogLevel.INFO.value)

    if not os.path.exists(os.path.dirname(_LOG_FILE)):
        try:
            os.makedirs(os.path.dirname(_LOG_FILE))
        except OSError as err:
            if err.errno != errno.EEXIST:
                raise
    handler_file = handlers.RotatingFileHandler(
        _LOG_FILE, maxBytes=5242880, backupCount=5
    )
    handler_file.setFormatter(logging.Formatter(_LOG_FORMAT_FILE))
    _log_handlers.append(handler_file)

    handler_stdout = logging.StreamHandler()
    handler_stdout.setFormatter(
        colorlog.ColoredFormatter(
            _LOG_FORMAT_TERM,
            log_colors=_LOG_COLORS,
            secondary_log_colors=_LOG_SECONDARY_COLORS,
        )
    )
    _log_handlers.append(handler_stdout)

    for handler in _log_handlers:
        log.addHandler(handler)
    return log  # type: ignore


_log = _init_logger()


def get_logger(name=None, level=None):
    # type: (t.Optional[str], t.Optional[int]) -> mqttanyLogger
    """
    Returns a logger, if ``name`` is not specified the import name of the calling
    file will be used.
    """
    if name is None:
        frm = inspect.stack()[1]
        name = inspect.getmodule(frm[0]).__name__  # type: ignore
    name = ".".join([s for s in name.split(".") if s not in ["mqttany", "modules"]])
    name = name[len(name) - _LOG_LEN_NAME :] if len(name) > _LOG_LEN_NAME else name
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        for handler in _log_handlers:
            logger.addHandler(handler)
    logger.setLevel(level or logging.getLogger("mqttany").level)
    return logger  # type: ignore


def set_level(level):
    # type: (LogLevel) -> None
    """
    Sets logging level to level
    """
    _log.setLevel(level.value)
    if level <= LogLevel.DEBUG:
        # for handler in _log.handlers:
        for handler in _log_handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setFormatter(
                    colorlog.ColoredFormatter(
                        _LOG_FORMAT_TERM_DEBUG,
                        log_colors=_LOG_COLORS,
                        secondary_log_colors=_LOG_SECONDARY_COLORS,
                    )
                )
            else:
                handler.setFormatter(logging.Formatter(_LOG_FORMAT_FILE_DEBUG))
    else:
        for handler in _log_handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setFormatter(
                    colorlog.ColoredFormatter(
                        _LOG_FORMAT_TERM,
                        log_colors=_LOG_COLORS,
                        secondary_log_colors=_LOG_SECONDARY_COLORS,
                    )
                )
            else:
                handler.setFormatter(logging.Formatter(_LOG_FORMAT_FILE))


def log_traceback(log, limit=None):
    # type: (mqttanyLogger, t.Optional[int]) -> None
    """
    Print a traceback to the log
    """
    log.error(
        "\n\n" + "".join(traceback.format_exception(*sys.exc_info(), limit=limit))  # type: ignore
    )


def uninit():
    # type: () -> None
    """
    Flushes and closes all log handlers
    """
    # for handler in _log.handlers:
    for handler in _log_handlers:
        handler.flush()
        handler.close()
