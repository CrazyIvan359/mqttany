"""
**********
I2C Device
**********
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

__all__ = [ "getDeviceClass", "getConfOptions", "getDeviceOptions" ]

from modules.i2c.device import mcp230xx


def getDeviceClass(device):
    """
    Returns an I2CDevice subclass to handle ``device`` or ``None`` if one
    is not available.
    """
    dev_classes = {}
    dev_classes.update(mcp230xx.SUPPORTED_DEVICES)
    return dev_classes.get(device, None)


def getConfOptions():
    """
    Return a dict of all additional config options
    """
    conf = {}
    conf.update(mcp230xx.CONF_OPTIONS)
    return conf


def getDeviceOptions():
    """
    Return a dict of all additional device config options
    """
    conf = {}
    conf.update(mcp230xx.CONF_DEVICE_OPTIONS)
    return conf
