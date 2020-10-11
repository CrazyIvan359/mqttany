"""
******
Logger
******

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

__all__ = ["get_logger", "set_level", "log_traceback", "uninit"]

import os, sys, errno, inspect, traceback
from types import MethodType
import logging
from logging import handlers
from logging import DEBUG, INFO, WARNING as WARN
import colorlog

TRACE = 5  # trace level logging

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

_log_handlers = []


def trace_log(self, msg, *args, **kwargs):
    """
    Trace method that will be injected into ``logging.Logger``
    """
    if self.isEnabledFor(TRACE):
        self._log(TRACE, msg, args, **kwargs)


def warn_log(self, msg, *args, **kwargs):
    """
    Warn method that will be injected into ``logging.Logger``.
    Needed because ``log.warn`` is depreciated in Python 3.7
    """
    if self.isEnabledFor(WARN):
        self._log(WARN, msg, args, **kwargs)


def _init_logger():
    """
    Creates the root logger for MQTTany
    """
    logging.addLevelName(WARN, "WARN")
    logging.addLevelName(TRACE, "TRACE")

    log = logging.getLogger("mqttany")
    log.trace = MethodType(trace_log, log)
    log.warn = MethodType(warn_log, log)
    log.setLevel(INFO)

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
    return log


_log = _init_logger()


def get_logger(name=None, level=None):
    """
    Returns a logger, if ``name`` is not specified the import name of the calling
    file will be used.
    """
    if name is None:
        frm = inspect.stack()[1]
        name = inspect.getmodule(frm[0]).__name__
    name = ".".join([s for s in name.split(".") if s not in ["mqttany", "modules"]])
    name = name[len(name) - _LOG_LEN_NAME :] if len(name) > _LOG_LEN_NAME else name
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        for handler in _log_handlers:
            logger.addHandler(handler)
    logger.trace = MethodType(trace_log, logger)
    logger.warn = MethodType(warn_log, logger)
    logger.setLevel(level or logging.getLogger("mqttany").level)
    return logger


def set_level(level):
    """
    Sets logging level to level
    """
    _log.setLevel(level)
    if level <= DEBUG:
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
        # for handler in _log.handlers:
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
    """
    Print a traceback to the log
    """
    for layer in traceback.format_exception(*sys.exc_info(), limit=limit):
        for line in layer.split("\n"):
            log.error(line)


def uninit():
    """
    Flushes and closes all log handlers
    """
    # for handler in _log.handlers:
    for handler in _log_handlers:
        handler.flush()
        handler.close()
