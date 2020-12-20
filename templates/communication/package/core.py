"""
*****************************
Communication Module Template
*****************************

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

import typing as t

from config import parse_config

from common import SubscribeMessage

from . import common
from .common import (
    CONF_KEY_FIXED_TYPE,
    CONF_KEY_SELECTION,
    CONF_KEY_STRING,
    CONF_KEY_SUBSECTION,
    CONF_OPTIONS,
    CONFIG,
    core_queue,
    log,
    receive_queue,
)


def load(config_raw: t.Dict[str, t.Any]) -> bool:
    """
    This function runs on the main process after the module is imported. It should parse
    and validate the configuration and do other basic setup of the module. Do not start
    any threads or long running tasks here, they should go in the ``start`` function.
    Limit memory usage here as much as possible.
    """
    config_data = parse_config(config_raw, CONF_OPTIONS, log)
    del config_raw
    if config_data:
        log.debug("Config loaded successfully")
        CONFIG.update(config_data)
        del config_data
        return True
    else:
        log.error("Error loading config")
        return False


def start() -> None:
    """
    This function runs on the module's dedicated process when it is started. Connections
    should be started here and a listener thread should be created for receiving messages
    from the outside connection if required.
    """
    pass


def stop() -> None:
    """
    This function runs on the module's dedicated process when it is exiting. Connections
    should be closed and threads stopped.
    """
    pass


def transmit_callback(message: SubscribeMessage) -> bool:
    """
    This function is required and must accept exactly one argument of type ``SubscribeMessage``.
    It will be called when there is a message to be sent. If the sending succeeds it must
    return ``True``. If sending fails and it returns ``False``, MQTTany will queue the
    message and wait 500ms before attempting to send again.
    """
    return True


def transmit_ready() -> bool:
    """
    This function is required and must return ``True`` if the module is ready to transmit,
    or ``False`` othewise.
    """
    return True
