"""
******
Common
******

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

import time, collections, signal
from ctypes import c_char_p, c_int
import multiprocessing as mproc
from enum import Enum

import logger
log = logger.get_logger()

__all__ = [
    "POISON_PILL", "SignalHook",
    "Mode", "Logic", "Direction", "Resistor", "Interrupt",
    "TEXT_LOGIC_STATE", "TEXT_PIN_PREFIX",
    "acquire_gpio_lock", "release_gpio_lock",
]

POISON_PILL = {"stop": True}

class Mode(Enum):
    BOARD = 50
    SOC = 51
    WIRINGPI = 52

class Logic(Enum):
    LOW = 0
    HIGH = 1

class Direction(Enum):
    INPUT = 10
    OUTPUT = 11

class Resistor(Enum):
    OFF = 20
    PULL_UP = 21
    PULL_DOWN = 22

class Interrupt(Enum):
    NONE = 0
    RISING = 30
    FALLING = 31
    BOTH = 32

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
     28: mproc.Array(c_char_p, 16), # 28
     29: mproc.Array(c_char_p, 16), # 29
     30: mproc.Array(c_char_p, 16), # 30
     31: mproc.Array(c_char_p, 16), # 31

     33: mproc.Array(c_char_p, 16), # 33
     34: mproc.Array(c_char_p, 16), # 34

     74: mproc.Array(c_char_p, 16), # 74
     75: mproc.Array(c_char_p, 16), # 75
     76: mproc.Array(c_char_p, 16), # 76
     77: mproc.Array(c_char_p, 16), # 77

     83: mproc.Array(c_char_p, 16), # 83

     87: mproc.Array(c_char_p, 16), # 87
     88: mproc.Array(c_char_p, 16), # 88

     97: mproc.Array(c_char_p, 16), # 97
     98: mproc.Array(c_char_p, 16), # 98
     99: mproc.Array(c_char_p, 16), # 99
    100: mproc.Array(c_char_p, 16), # 100
    101: mproc.Array(c_char_p, 16), # 101
    102: mproc.Array(c_char_p, 16), # 102
    103: mproc.Array(c_char_p, 16), # 103
    104: mproc.Array(c_char_p, 16), # 104
    105: mproc.Array(c_char_p, 16), # 105
    106: mproc.Array(c_char_p, 16), # 106
    107: mproc.Array(c_char_p, 16), # 107
    108: mproc.Array(c_char_p, 16), # 108

    113: mproc.Array(c_char_p, 16), # 113
    114: mproc.Array(c_char_p, 16), # 114
    115: mproc.Array(c_char_p, 16), # 115
    116: mproc.Array(c_char_p, 16), # 116
    117: mproc.Array(c_char_p, 16), # 117
    118: mproc.Array(c_char_p, 16), # 118

    128: mproc.Array(c_char_p, 16), # 128

    130: mproc.Array(c_char_p, 16), # 130
    131: mproc.Array(c_char_p, 16), # 131
    132: mproc.Array(c_char_p, 16), # 132
    133: mproc.Array(c_char_p, 16), # 133

    171: mproc.Array(c_char_p, 16), # 171
    172: mproc.Array(c_char_p, 16), # 172
    173: mproc.Array(c_char_p, 16), # 173
    174: mproc.Array(c_char_p, 16), # 174

    187: mproc.Array(c_char_p, 16), # 187
    188: mproc.Array(c_char_p, 16), # 188
    189: mproc.Array(c_char_p, 16), # 189
    190: mproc.Array(c_char_p, 16), # 190
    191: mproc.Array(c_char_p, 16), # 191
    192: mproc.Array(c_char_p, 16), # 192

    205: mproc.Array(c_char_p, 16), # 205
    206: mproc.Array(c_char_p, 16), # 206
    207: mproc.Array(c_char_p, 16), # 207
    208: mproc.Array(c_char_p, 16), # 208
    209: mproc.Array(c_char_p, 16), # 209
    210: mproc.Array(c_char_p, 16), # 210

    214: mproc.Array(c_char_p, 16), # 214

    218: mproc.Array(c_char_p, 16), # 218
    219: mproc.Array(c_char_p, 16), # 219

    224: mproc.Array(c_char_p, 16), # 224
    225: mproc.Array(c_char_p, 16), # 225
    226: mproc.Array(c_char_p, 16), # 226
    227: mproc.Array(c_char_p, 16), # 227
    228: mproc.Array(c_char_p, 16), # 228
    229: mproc.Array(c_char_p, 16), # 229
    230: mproc.Array(c_char_p, 16), # 230
    231: mproc.Array(c_char_p, 16), # 231
    232: mproc.Array(c_char_p, 16), # 232
    233: mproc.Array(c_char_p, 16), # 233
    234: mproc.Array(c_char_p, 16), # 234
    235: mproc.Array(c_char_p, 16), # 235
    236: mproc.Array(c_char_p, 16), # 236
    237: mproc.Array(c_char_p, 16), # 237
    238: mproc.Array(c_char_p, 16), # 238
    239: mproc.Array(c_char_p, 16), # 239
    240: mproc.Array(c_char_p, 16), # 240
    241: mproc.Array(c_char_p, 16), # 241

    247: mproc.Array(c_char_p, 16), # 247

    249: mproc.Array(c_char_p, 16), # 249

    464: mproc.Array(c_char_p, 16), # 464

    472: mproc.Array(c_char_p, 16), # 472
    473: mproc.Array(c_char_p, 16), # 473
    474: mproc.Array(c_char_p, 16), # 474
    475: mproc.Array(c_char_p, 16), # 475
    476: mproc.Array(c_char_p, 16), # 476
    477: mproc.Array(c_char_p, 16), # 477
    478: mproc.Array(c_char_p, 16), # 478
    479: mproc.Array(c_char_p, 16), # 479
    480: mproc.Array(c_char_p, 16), # 480
    481: mproc.Array(c_char_p, 16), # 481
    482: mproc.Array(c_char_p, 16), # 482
    483: mproc.Array(c_char_p, 16), # 483
    484: mproc.Array(c_char_p, 16), # 484
    485: mproc.Array(c_char_p, 16), # 485
    486: mproc.Array(c_char_p, 16), # 486
    487: mproc.Array(c_char_p, 16), # 487
    488: mproc.Array(c_char_p, 16), # 488
    489: mproc.Array(c_char_p, 16), # 489
    490: mproc.Array(c_char_p, 16), # 490
    491: mproc.Array(c_char_p, 16), # 491
    492: mproc.Array(c_char_p, 16), # 492
    493: mproc.Array(c_char_p, 16), # 493
    494: mproc.Array(c_char_p, 16), # 494
    495: mproc.Array(c_char_p, 16), # 495
}


class SignalHook:
    """
    Hooks to SIGINT, SIGTERM, SIGKILL
    """
    SIGINT = signal.SIGINT
    SIGTERM = signal.SIGTERM
    SIGKILL = signal.SIGKILL

    def __init__(self):
        self._last_signal = None
        try: signal.signal(signal.SIGINT, self._signal_received)
        except OSError: pass
        try: signal.signal(signal.SIGTERM, self._signal_received)
        except OSError: pass
        try: signal.signal(signal.SIGKILL, self._signal_received)
        except OSError: pass

    def _signal_received(self, signum, frame):
        self._last_signal = signal.Signals(signum)

    @property
    def signal(self): return self._last_signal

    @property
    def exit(self):
        return self._last_signal in [
            self.SIGINT, self.SIGTERM, self.SIGKILL
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
