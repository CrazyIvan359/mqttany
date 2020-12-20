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

__all__ = ["load", "start", "stop", "transmit_callback", "transmit_ready", "log"]

import multiprocessing as mproc

from modules import ModuleType
from mprop import mproperty

from common import BusMessage

from . import common
from .common import log
from .core import load, start, stop, transmit_callback, transmit_ready

_module_type = ModuleType.COMMUNICATION  # type: ignore
_core_queue: "mproc.Queue[str]" = None  # type: ignore
_receive_queue: "mproc.Queue[BusMessage]" = None  # type: ignore

# These queues are put in the module's attributes whether they are defined here or not
# Do not use these names in your module and do not access these objects
transmit_queue: "mproc.Queue[BusMessage]" = None  # type: ignore
resend_queue: "mproc.Queue[BusMessage]" = None  # type: ignore


@mproperty
def core_queue(module: object) -> "mproc.Queue[str]":
    return _core_queue


@core_queue.setter
def core_queue(module: object, value: "mproc.Queue[BusMessage]") -> None:
    module._core_queue = value  # type:ignore
    common.core_queue = value
    # Do not try assigning the queue to attributes of other files as that
    # will likely result in a circular import!


@mproperty
def receive_queue(module: object) -> "mproc.Queue[BusMessage]":
    return _receive_queue


@receive_queue.setter
def receive_queue(module: object, value: "mproc.Queue[BusMessage]") -> None:
    module._receive_queue = value  # type: ignore
    common.receive_queue = value
    # Do not try assigning the queue to attributes of other files as that
    # will likely result in a circular import!
