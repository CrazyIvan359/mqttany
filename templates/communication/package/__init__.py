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

__all__ = []

from mprop import mproperty

from modules import ModuleType

from modules.comm_pkg_template.core import transmit_callback, transmit_ready
from modules.comm_pkg_template import common
from modules.comm_pkg_template.common import log

_module_type = ModuleType.COMMUNICATION
_core_queue = None
_receive_queue = None

# These queues are put in the module's attributes whether they are defined here or not
# Do not use these names in your module and do not access these objects
transmit_queue = None
resend_queue = None


@mproperty
def core_queue(module):
    return _core_queue


@core_queue.setter
def core_queue(module, value):
    module._core_queue = value
    common.core_queue = value
    # Do not try assigning the queue to attributes of other files as that
    # will likely result in a circular import!


@mproperty
def receive_queue(module):
    return _receive_queue


@receive_queue.setter
def receive_queue(module, value):
    module._receive_queue = value
    common.receive_queue = value
    # Do not try assigning the queue to attributes of other files as that
    # will likely result in a circular import!
