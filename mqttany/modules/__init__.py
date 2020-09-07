"""
*************
Module Loader
*************

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

__all__ = [
    "ModuleType",
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

from enum import Enum

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
