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

_log_file = os.path.join(os.path.dirname(__file__), "log", "mqttany.log")
_log_format = "%(asctime)s [%(levelname)-5s] [%(name)-24s] %(message)s"
_log_format_debug = (
    "%(asctime)s [%(levelname)-5s] [%(processName)-8s] [%(name)-24s] %(message)s"
)
_log_format_color = "%(asctime)s [%(log_color)s%(levelname)-5s%(reset)s] [%(name)-24s] %(message_log_color)s%(message)s"
_log_format_color_debug = "%(asctime)s [%(log_color)s%(levelname)-5s%(reset)s] [%(processName)-8s] [%(name)-24s] %(message_log_color)s%(message)s"
_log_colors = {
    "TRACE": "white",
    "DEBUG": "bold_white",
    "INFO": "bold_green",
    "WARN": "bold_yellow",
    "ERROR": "bold_red",
    "CRITICAL": "bold_red",
}
_secondary_log_colors = {
    "message": {
        "DEBUG": "bold",
        "INFO": "bold_green",
        "WARN": "bold_yellow",
        "ERROR": "bold_red",
        "CRITICAL": "bold_red",
    }
}


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

    if not os.path.exists(os.path.dirname(_log_file)):
        try:
            os.makedirs(os.path.dirname(_log_file))
        except OSError as err:
            if err.errno != errno.EEXIST:
                raise
    handler_file = handlers.RotatingFileHandler(
        _log_file, maxBytes=5242880, backupCount=5
    )
    handler_file.setFormatter(logging.Formatter(_log_format))
    log.addHandler(handler_file)

    handler_stdout = logging.StreamHandler()
    handler_stdout.setFormatter(
        colorlog.ColoredFormatter(
            _log_format_color,
            log_colors=_log_colors,
            secondary_log_colors=_secondary_log_colors,
        )
    )
    log.addHandler(handler_stdout)

    return log


_log = _init_logger()


def get_logger(name="mqttany", level=None):
    """
    Returns a logger
    """
    logger = logging.getLogger(name)
    logger.trace = MethodType(trace_log, logger)
    logger.warn = MethodType(warn_log, logger)
    logger.setLevel(level or logging.getLogger("mqttany").level)
    return logger


def get_module_logger(module=None, level=None):
    """
    Returns a logger for a module
    """
    if module is None:
        frm = inspect.stack()[1]
        module = ".".join(inspect.getmodule(frm[0]).__name__.split(".")[1:])
    return get_logger("mqttany.{}".format(module), level)


def set_level(level):
    """
    Sets logging level to level
    """
    _log.setLevel(level)
    if level <= DEBUG:
        for handler in _log.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setFormatter(
                    colorlog.ColoredFormatter(
                        _log_format_color_debug,
                        log_colors=_log_colors,
                        secondary_log_colors=_secondary_log_colors,
                    )
                )
            else:
                handler.setFormatter(logging.Formatter(_log_format_debug))
    else:
        for handler in _log.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setFormatter(
                    colorlog.ColoredFormatter(
                        _log_format_color,
                        log_colors=_log_colors,
                        secondary_log_colors=_secondary_log_colors,
                    )
                )
            else:
                handler.setFormatter(logging.Formatter(_log_format))


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
    for handler in _log.handlers:
        handler.flush()
        handler.close()
