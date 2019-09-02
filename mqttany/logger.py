"""
******
Logger
******

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

import os, errno
import logging
from logging import handlers
from logging import DEBUG, INFO, WARN, ERROR

all = [ "get_logger", "set_level", "uninit" ]

_log_file = os.path.join(os.path.dirname(__file__), "log", "mqttany.log")
_log_format = "%(asctime)s [%(levelname)-5s] [%(name)-24s] %(message)s"

def _init_logger():
    """
    Creates the root logger for MQTTany
    """
    logging.addLevelName(logging.WARN, "WARN")

    log = logging.getLogger("mqttany")
    log.setLevel(logging.INFO)

    if not os.path.exists(os.path.dirname(_log_file)):
        try:
            os.makedirs(os.path.dirname(_log_file))
        except OSError as err:
            if err.errno != errno.EEXIST: raise
    handler_file = handlers.RotatingFileHandler(_log_file, maxBytes=5242880, backupCount=5)
    handler_file.setFormatter(logging.Formatter(_log_format))
    log.addHandler(handler_file)

    handler_stdout = logging.StreamHandler()
    handler_stdout.setFormatter(logging.Formatter(_log_format))
    log.addHandler(handler_stdout)

    return log

_log = _init_logger()


def get_logger(name=None, level=None):
    """
    Returns a logger
    """
    logger = logging.getLogger("mqttany{}".format(".{}".format(name) if name else ""))
    logger.setLevel(level or logging.getLogger("mqttany").level)
    return logger

def set_level(level):
    """
    Sets logging level to level
    """
    _log.setLevel(level)

def uninit():
    """
    Flushes and closes all log handlers
    """
    _log.handler_file.flush()
    _log.handler_file.close()
    _log.handler_stdout.flush()
    _log.handler_stdout.close()
