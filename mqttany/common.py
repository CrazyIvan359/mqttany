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

from mqttany import logger
log = logger.get_logger("mqttany")

all = [
    "POISON_PILL",
    "acquire_gpio_lock", "release_gpio_lock"
]

POISON_PILL = {"stop": True}



_gpio_locked = {}

def acquire_gpio_lock(pin, module):
    """
    Acquire lock on GPIO pins
    """
    if str(pin) in _gpio_locked:
        log.warn("Module '{module}' attempted to acquire a lock on GPIO{pin} but '{owner}' already has a lock on it".format(
                module=module, pin=pin, owner=_gpio_locked[pin]))
        return False
    else:
        _gpio_locked[str(pin)] = module
        return True

def release_gpio_lock(pin, module):
    """
    Release lock on GPIO pin
    """
    if str(pin) in _gpio_locked:
        # prevent releasing a lock a module doesn't have
        if _gpio_locked[str(pin)] == module:
            _gpio_locked.pop(str(pin))
            return True
        else:
            log.warn("Module '{module}' attempted to release a lock on GPIO{pin} but it is locked by '{owner}'".format(
                module=module, pin=pin, owner=_gpio_locked[pin]))
            return False
    else:
        return True
