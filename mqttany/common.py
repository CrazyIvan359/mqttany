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

import time, collections
from ctypes import c_char_p, c_int
import multiprocessing as mproc
from enum import Enum

import logger
log = logger.get_logger()

all = [
    "POISON_PILL",
    "Mode", "Logic", "TEXT_LOGIC_STATE", "TEXT_PIN_PREFIX",
    "acquire_gpio_lock", "release_gpio_lock",
]

POISON_PILL = {"stop": True}

class Mode(Enum):
    BOARD = 50
    SOC = 51
    WIRINGPI = 52

class Logic():
    LOW = 0
    HIGH = 1

TEXT_LOGIC_STATE = ["LOW", "HIGH"]
TEXT_PIN_PREFIX = {
    Mode.BOARD: "pin ",
    Mode.SOC: "GPIO",
    Mode.WIRINGPI: "WiringPi pin "
}

_gpio_lock = { # GPIO pin locks
      0: mproc.Array(c_char_p, 16), # 0
      1: mproc.Array(c_char_p, 16), # 1
      2: mproc.Array(c_char_p, 16), # 2
      3: mproc.Array(c_char_p, 16), # 3
      4: mproc.Array(c_char_p, 16), # 4
      5: mproc.Array(c_char_p, 16), # 5
      6: mproc.Array(c_char_p, 16), # 6
      7: mproc.Array(c_char_p, 16), # 7
      8: mproc.Array(c_char_p, 16), # 8
      9: mproc.Array(c_char_p, 16), # 9
     10: mproc.Array(c_char_p, 16), # 10
     11: mproc.Array(c_char_p, 16), # 11
     12: mproc.Array(c_char_p, 16), # 12
     13: mproc.Array(c_char_p, 16), # 13
     14: mproc.Array(c_char_p, 16), # 14
     15: mproc.Array(c_char_p, 16), # 15
     16: mproc.Array(c_char_p, 16), # 16
     17: mproc.Array(c_char_p, 16), # 17
     18: mproc.Array(c_char_p, 16), # 18
     19: mproc.Array(c_char_p, 16), # 19
     20: mproc.Array(c_char_p, 16), # 20
     21: mproc.Array(c_char_p, 16), # 21
     22: mproc.Array(c_char_p, 16), # 22
     23: mproc.Array(c_char_p, 16), # 23
     24: mproc.Array(c_char_p, 16), # 24
     25: mproc.Array(c_char_p, 16), # 25
     26: mproc.Array(c_char_p, 16), # 26
     27: mproc.Array(c_char_p, 16), # 27
}

_i2c_lock = [ # I2C bus locks
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16), "scl": mproc.Value(c_int, 0), "sda": mproc.Value(c_int, 0)}, # Bus 0
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16), "scl": mproc.Value(c_int, 0), "sda": mproc.Value(c_int, 0)}, # Bus 1
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16), "scl": mproc.Value(c_int, 0), "sda": mproc.Value(c_int, 0)}, # Bus 2
    {"lock": mproc.Lock(), "module": mproc.Array(c_char_p, 16), "scl": mproc.Value(c_int, 0), "sda": mproc.Value(c_int, 0)}, # Bus 3
]


def acquire_gpio_lock(pin, gpio_pin, module, timeout=0, mode=Mode.SOC):
    """
    Acquire lock on GPIO pin
    Timeout is ms
    """
    log.trace("Module '{module}' requested a lock on {pin_prefix}{pin:02d}{gpio_pin}".format(
        module=module, pin=pin, pin_prefix=TEXT_PIN_PREFIX[mode],
        gpio_pin="" if mode == Mode.SOC else " (GPIO{:02d})".format(gpio_pin)))

    if _gpio_lock[gpio_pin].raw == "":
        _gpio_lock[gpio_pin].raw = module
        log.debug("Module '{module}' locked {pin_prefix}{pin:02d}{gpio_pin}".format(
            module=module, pin=pin, pin_prefix=TEXT_PIN_PREFIX[mode],
            gpio_pin="" if mode == Mode.SOC else " (GPIO{:02d})".format(gpio_pin)))
        return True
    elif _gpio_lock[gpio_pin].raw == module:
        _gpio_lock[gpio_pin].raw = module
        log.trace("Module '{module}' already has a lock on {pin_prefix}{pin:02d}{gpio_pin}".format(
            module=module, pin=pin, pin_prefix=TEXT_PIN_PREFIX[mode],
            gpio_pin="" if mode == Mode.SOC else " (GPIO{:02d})".format(gpio_pin)))
        return True
    elif timeout:
        then = time.time() + ( timeout / 1000 )
        while time.time() < then:
            if _gpio_lock[gpio_pin].raw == "":
                _gpio_lock[gpio_pin].raw = module
                log.debug("Module '{module}' locked {pin_prefix}{pin:02d}{gpio_pin}".format(
                    module=module, pin=pin, pin_prefix=TEXT_PIN_PREFIX[mode],
                    gpio_pin="" if mode == Mode.SOC else " (GPIO{:02d})".format(gpio_pin)))
                return True
            else:
                time.sleep(0.025)

    log.warn("Module '{module}' failed to acquire a lock on {pin_prefix}{pin:02d}{gpio_pin} because '{owner}' already has a lock on it".format(
            module=module, pin=pin, owner=_gpio_lock[pin].raw, pin_prefix=TEXT_PIN_PREFIX[mode],
            gpio_pin="" if mode == Mode.SOC else " (GPIO{:02d})".format(gpio_pin)))
    return False


def release_gpio_lock(pin, gpio_pin, module, mode=Mode.SOC):
    """
    Release lock on GPIO pin
    """
    log.trace("Module '{module}' requested to release a lock on {pin_prefix}{pin:02d}{gpio_pin}".format(
        module=module, pin=pin, pin_prefix=TEXT_PIN_PREFIX[mode],
        gpio_pin="" if mode == Mode.SOC else " (GPIO{:02d})".format(gpio_pin)))

    if _gpio_lock[gpio_pin].raw == module:
        _gpio_lock[gpio_pin].raw == ""
    elif _gpio_lock[gpio_pin].raw == "":
        log.trace("Module '{module}' attempted to release {pin_prefix}{pin:02d}{gpio_pin} but it is not locked.".format(
            module=module, pin=pin, pin_prefix=TEXT_PIN_PREFIX[mode],
            gpio_pin="" if mode == Mode.SOC else " (GPIO{:02d})".format(gpio_pin)))
        return True
    else:
        log.warn("Module '{module}' attempted to release a lock on {pin_prefix}{pin:02d}{gpio_pin} but it is locked by '{owner}'".format(
            module=module, pin=pin, owner=_gpio_lock[pin].raw, pin_prefix=TEXT_PIN_PREFIX[mode],
            gpio_pin="" if mode == Mode.SOC else " (GPIO{:02d})".format(gpio_pin)))
        return False

    log.debug("Module '{module}' released lock on {pin_prefix}{pin:02d}{gpio_pin}".format(
        module=module, pin=pin, pin_prefix=TEXT_PIN_PREFIX[mode],
        gpio_pin="" if mode == Mode.SOC else " (GPIO{:02d})".format(gpio_pin)))
    return True


def acquire_i2c_lock(bus, scl, sda, module, timeout=0):
    """
    Acquire lock on I2C bus
    Timeout is ms
    """
    def lock_bus():
        bus_lock = False
        scl_lock = False
        if not _i2c_lock[bus]["lock"].acquire(False):
            if _i2c_lock[bus]["module"].raw != module:
                return (False, False, False)
        else:
            _i2c_lock[bus]["lock"].release()

        if bus_lock or _i2c_lock[bus]["lock"].acquire(False):
            bus_lock = True

            if scl_lock or acquire_gpio_lock(scl, scl, module):
                scl_lock = True
            else:
                return (False, False, False)

            if not acquire_gpio_lock(sda, sda, module):
                return (False, False, False)

            _i2c_lock[bus]["module"].raw = module

        return (True, bus_lock, scl_lock)


    log.trace("Module '{module}' requested a lock on I2C bus '{bus_id}'".format(
        module=module, bus_id=bus))

    if timeout:
        then = time.time() + ( timeout / 1000 )
        while time.time() < then:
            lock, bus_lock, scl_lock = lock_bus()
            if lock:
                break
            else:
                time.sleep(0.01)
    else:
        lock, bus_lock, scl_lock = lock_bus()

    if lock:
        log.debug("Module '{module}' locked I2C bus '{bus_id}'".format(
            module=module, bus_id=bus))
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
        release_gpio_lock(scl, scl, module)

    if bus_lock:
        _i2c_lock[bus]["lock"].release()

    return False


def release_i2c_lock(bus, scl, sda, module):
    """
    Release lock on I2C bus
    """
    log.trace("Module '{module}' requested to release a lock on I2C bus '{bus_id}'".format(
        module=module, bus_id=bus))
    if not _i2c_lock[bus]["lock"].acquire(False):
        # prevent releasing a lock a module doesn't have
        if _i2c_lock[bus]["module"].raw == module:
            release_gpio_lock(sda, sda, module)
            release_gpio_lock(scl, scl, module)
            _i2c_lock[bus]["lock"].release()
            _i2c_lock[bus]["module"].raw = ""
        else:
            log.warn("Module '{module}' attempted to release a lock on I2C bus '{bus_id}' but it is locked by '{owner}'".format(
                module=module, bus_id=bus, owner=_i2c_lock[bus]["module"].raw))
            return False
    else:
        _i2c_lock[bus]["lock"].release()

    log.debug("Module '{module}' released lock on I2C bus '{bus_id}'".format(
        module=module, bus_id=bus))
    return True


def update_dict(d, u):
    """
    Recursively update dict ``d`` with dict ``u``
    """
    for k in u:
        dv = d.get(k, {})
        if not isinstance(dv, collections.Mapping):
            d[k] = u[k]
        elif isinstance(u[k], collections.Mapping):
            d[k] = update_dict(dv, u[k])
        else:
            d[k] = u[k]
    return d



### Initialize

for pin in _gpio_lock:
    _gpio_lock[pin].raw = ""

for bus in _i2c_lock:
    bus["module"].raw = ""
