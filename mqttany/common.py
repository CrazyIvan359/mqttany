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

import time
from ctypes import c_char_p
import multiprocessing as mproc

from mqttany import logger
log = logger.get_logger()

all = [
    "POISON_PILL",
    "acquire_gpio_lock", "release_gpio_lock",
]

POISON_PILL = {"stop": True}

_gpio_lock = [ # GPIO pin locks
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 0
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 1
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 2
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 3
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 4
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 5
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 6
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 7
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 8
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 9
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 10
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 11
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 12
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 13
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 14
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 15
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 16
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 17
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 18
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 19
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 20
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 21
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 22
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 23
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 24
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 25
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 26
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 27
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 28
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 29
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 30
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 31
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 32
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 33
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 34
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 35
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 36
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 37
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 38
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 39
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 40
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 41
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 42
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 43
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 44
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 45
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 46
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16)}, # Pin 47
]

_i2c_lock = [ # I2C bus locks
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16), "scl": mproc.Value(int, 0), "sda": mproc.Value(int, 0)}, # Bus 0
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16), "scl": mproc.Value(int, 0), "sda": mproc.Value(int, 0)}, # Bus 1
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16), "scl": mproc.Value(int, 0), "sda": mproc.Value(int, 0)}, # Bus 2
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16), "scl": mproc.Value(int, 0), "sda": mproc.Value(int, 0)}, # Bus 3
]


def acquire_gpio_lock(pin, module, timeout=0):
    """
    Acquire lock on GPIO pin
    Timeout is ms
    """
    if timeout:
        then = time.time() + ( timeout / 1000 )
        while time.time() < then:
            if _gpio_lock[pin]["lock"].acquire(False):
                _gpio_lock[pin]["module"].raw = module
                return True
            else:
                time.sleep(0.025)

    elif _gpio_lock[pin]["lock"].acquire(False):
        _gpio_lock[pin]["module"].raw = module
        return True

    log.warn("Module '{module}' failed to acquire a lock on GPIO{pin} because '{owner}' already has a lock on it".format(
            module=module, pin=pin, owner=_gpio_lock[pin]["module"].raw))
    return False


def release_gpio_lock(pin, module):
    """
    Release lock on GPIO pin
    """
    if not _gpio_lock[pin]["lock"].acquire(False):
        # prevent releasing a lock a module doesn't have
        if _gpio_lock[pin]["module"].raw == module:
            _gpio_lock[pin]["lock"].release()
        else:
            log.warn("Module '{module}' attempted to release a lock on GPIO{pin} but it is locked by '{owner}'".format(
                module=module, pin=pin, owner=_gpio_lock[pin]["module"].raw))
            return False
    else:
        _gpio_lock[pin]["lock"].release()

    return True


def acquire_i2c_lock(bus, scl, sda, module, timeout=0):
    """
    Acquire lock on I2C bus
    Timeout is ms
    """
    def lock_bus():
        if _i2c_lock[bus]["lock"].locked and _i2c_lock[bus]["module"].raw != module:
            return False

        if bus_lock or _i2c_lock[bus]["lock"].acquire(False):
            bus_lock = True

            if scl_lock or acquire_gpio_lock(scl, module):
                scl_lock = True
            else:
                return False

            if not acquire_gpio_lock(sda, module):
                return False

            _i2c_lock[bus]["module"].raw = module

        return True


    bus_lock = False
    scl_lock = False

    if timeout:
        then = time.time() + ( timeout / 1000 )
        while time.time() < then:
            if lock_bus():
                return True
            else:
                time.sleep(0.01)
    elif lock_bus():
        return True

    if scl_lock and bus_lock:
        log.warn("Module '{module}' failed to acquire a lock on I2C bus '{bus_id}' because SDA pin {pin} is locked by another module".format(
                module=module, bus_id=bus, pin=sda))
    elif bus_lock:
        log.warn("Module '{module}' failed to acquire a lock on I2C bus '{bus_id}' because SCL pin {pin} is locked by another module".format(
                module=module, bus_id=bus, pin=scl))
    else:
        log.warn("Module '{module}' failed to acquire a lock on I2C bus '{bus_id}' because '{owner}' already has a lock on it".format(
                module=module, bus_id=bus, owner=_i2c_lock[bus]["module"].raw))

    if scl_lock:
        release_gpio_lock(scl, module)

    if bus_lock:
        _i2c_lock[bus]["lock"].release()

    return False


def release_i2c_lock(bus, scl, sda, module):
    """
    Release lock on I2C bus
    """
    if _i2c_lock[bus]["lock"].locked:
        # prevent releasing a lock a module doesn't have
        if _i2c_lock[bus]["module"].raw == module:
            release_gpio_lock(sda, module)
            release_gpio_lock(scl, module)
            _i2c_lock[bus]["lock"].release()
            _i2c_lock[bus]["module"].raw = ""
        else:
            log.warn("Module '{module}' attempted to release a lock on I2C bus '{bus_id}' but it is locked by '{owner}'".format(
                module=module, bus_id=bus, owner=_i2c_lock[bus]["module"].raw))
            return False

    return True
