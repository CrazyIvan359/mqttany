"""
*************
Module Loader
*************

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

__all__ = [
    "ModuleType",
    "call",
    "ATTR_TYPE",
    "ATTR_LOG",
    "ATTR_LOAD",
    "ATTR_START",
    "ATTR_STOP",
    "ATTR_QCORE",
    "ATTR_QRECEIVE",
    "ATTR_QTRANSMIT",
    "ATTR_CBTRANSMIT",
    "ATTR_QRESEND",
    "ATTR_TXREADY",
    "ATTR_QPUBLISH",
    "ATTR_QSUBSCRIBE",
    "ATTR_NODES",
]

import types
import typing as t
from enum import Enum

from logger import log_traceback

ATTR_TYPE = "_module_type"
ATTR_LOG = "log"
ATTR_LOAD = "load"
ATTR_START = "start"
ATTR_STOP = "stop"
ATTR_QCORE = "core_queue"
ATTR_QRECEIVE = "receive_queue"
ATTR_QTRANSMIT = "transmit_queue"
ATTR_QRESEND = "resend_queue"
ATTR_CBTRANSMIT = "transmit_callback"
ATTR_TXREADY = "transmit_ready"
ATTR_QPUBLISH = "publish_queue"
ATTR_QSUBSCRIBE = "subscribe_queue"
ATTR_NODES = "nodes"


class ModuleType(Enum):
    COMMUNICATION = "Communication"
    INTERFACE = "Interface"


def call(module: types.ModuleType, name: str, **kwargs: t.Any) -> t.Any:
    """
    Calls ``name`` if defined in ``module``
    """
    func = getattr(module, name, None)
    if func is not None:
        retval = False
        if callable(func):
            try:
                retval = func(**kwargs)
            except:
                module.log.error(  # type: ignore
                    "An exception occurred while running function '%s'",
                    getattr(func, "__name__", func),
                )
                log_traceback(module.log)  # type: ignore
            finally:
                # This function intentionally swallows exceptions. It is only used by
                # the core to call functions in modules. If there is an error in a
                # module the core must continue to run in order to exit gracefully.
                # If the core were to stop because of exceptions in modules, all child
                # processes would be orphaned and would have to be killed by manually
                # sending SIG.TERM or SIG.KILL to them.
                return retval  # pylint: disable=lost-exception
