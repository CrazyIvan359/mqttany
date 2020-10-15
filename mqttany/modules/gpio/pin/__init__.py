"""
********
GPIO Pin
********

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

from common import update_dict

from modules.gpio.pin import digital, counter

__all__ = ["getPin", "updateConfOptions"]


def getPin(pin_mode):
    """
    Returns a class for the pin based on the pin mode or ``None`` if one is
    not available.
    """
    pin_classes = {}
    pin_classes.update(digital.SUPPORTED_PIN_MODES)
    pin_classes.update(counter.SUPPORTED_PIN_MODES)
    return pin_classes.get(pin_mode, None)


def updateConfOptions(conf_options):
    """
    Returns a copy of ``conf_options`` updated with options from each pin type.
    """
    conf_options = update_dict(conf_options, digital.CONF_OPTIONS)
    conf_options = update_dict(conf_options, counter.CONF_OPTIONS)
    return conf_options
