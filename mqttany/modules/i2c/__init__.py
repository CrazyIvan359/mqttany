"""
**********
I2C Module
**********

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

# Linux kernel driver doc https://www.kernel.org/doc/Documentation/i2c/smbus-protocol

__all__ = ["load", "start", "stop", "device_message", "poll_message", "log", "nodes"]

import multiprocessing as mproc

from modules import ModuleType
from mprop import mproperty

from common import BusMessage

from . import common
from .common import log, nodes
from .core import device_message, load, poll_message, start, stop

_module_type = ModuleType.INTERFACE  # type: ignore
_publish_queue: "mproc.Queue[BusMessage]" = None  # type: ignore
subscribe_queue: "mproc.Queue[BusMessage]" = None  # type: ignore


@mproperty
def publish_queue(module: object) -> "mproc.Queue[BusMessage]":
    return _publish_queue


@publish_queue.setter
def publish_queue(module: object, value: "mproc.Queue[BusMessage]") -> None:
    module._publish_queue = value  # type: ignore
    common.publish_queue = value
