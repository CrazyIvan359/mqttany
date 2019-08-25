"""
MQTTany

Logger
"""

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
    handler_file = handlers.RotatingFileHandler(_log_file, maxBytes=5368709120, backupCount=5)
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
