"""
******
Common
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

import multiprocessing as mproc

all = [
    "POISON_PILL",
    "gpio_lock",
]

POISON_PILL = {"stop": True}

gpio_lock = [ # GPIO pin locks
    mproc.Lock(), # Pin 0
    mproc.Lock(), # Pin 1
    mproc.Lock(), # Pin 2
    mproc.Lock(), # Pin 3
    mproc.Lock(), # Pin 4
    mproc.Lock(), # Pin 5
    mproc.Lock(), # Pin 6
    mproc.Lock(), # Pin 7
    mproc.Lock(), # Pin 8
    mproc.Lock(), # Pin 9
    mproc.Lock(), # Pin 10
    mproc.Lock(), # Pin 11
    mproc.Lock(), # Pin 12
    mproc.Lock(), # Pin 13
    mproc.Lock(), # Pin 14
    mproc.Lock(), # Pin 15
    mproc.Lock(), # Pin 16
    mproc.Lock(), # Pin 17
    mproc.Lock(), # Pin 18
    mproc.Lock(), # Pin 19
    mproc.Lock(), # Pin 20
    mproc.Lock(), # Pin 21
    mproc.Lock(), # Pin 22
    mproc.Lock(), # Pin 23
    mproc.Lock(), # Pin 24
    mproc.Lock(), # Pin 25
    mproc.Lock(), # Pin 26
    mproc.Lock(), # Pin 27
    mproc.Lock(), # Pin 28
    mproc.Lock(), # Pin 29
    mproc.Lock(), # Pin 30
    mproc.Lock(), # Pin 31
    mproc.Lock(), # Pin 32
    mproc.Lock(), # Pin 33
    mproc.Lock(), # Pin 34
    mproc.Lock(), # Pin 35
    mproc.Lock(), # Pin 36
    mproc.Lock(), # Pin 37
    mproc.Lock(), # Pin 38
    mproc.Lock(), # Pin 39
    mproc.Lock(), # Pin 40
    mproc.Lock(), # Pin 41
    mproc.Lock(), # Pin 42
    mproc.Lock(), # Pin 43
    mproc.Lock(), # Pin 44
    mproc.Lock(), # Pin 45
    mproc.Lock(), # Pin 46
    mproc.Lock(), # Pin 47
]
