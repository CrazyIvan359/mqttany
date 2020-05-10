"""
***********
GPIO Module
***********

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

try:
    from mprop import mproperty
except ImportError:
    raise ImportError("MQTTany's GPIO module requires 'mprop' to be installed, \
        please see the wiki for instructions on how to install requirements")

from modules.gpio import core
from modules.gpio.core import init, pre_loop, post_loop
from modules.gpio.core import _pin_message, poll_all
from modules.gpio.common import log

__all__ = [ "init", "pre_loop", "post_loop", "queue" ]

_queue = None

@mproperty
def queue(module):
    return _queue

@queue.setter
def queue(module, value):
    module._queue = value
    core.queue = value
