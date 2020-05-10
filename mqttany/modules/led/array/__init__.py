"""
****************
LED Array Module
****************

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

from modules.led.common import CONF_KEY_OUTPUT, CONF_KEY_TOPIC, CONF_KEY_COUNT, CONF_KEY_PER_PIXEL, CONF_KEY_COLOR_ORDER
from modules.led.array import rpi, sacn

__all__ = [ "getArray", "getConfOptions" ]


def getArray(array_config, log):
    """
    Returns an LED Object or ``None`` if one is not available for the specified hardware.
    """
    array_classes = {}
    array_classes.update(rpi.SUPPORTED_TYPES)
    array_classes.update(sacn.SUPPORTED_TYPES)
    clazz = array_classes[array_config[CONF_KEY_OUTPUT]]

    if not clazz:
        log.error("No library is available for '{name}' configuration".format(name=array_config["name"]))
        return None

    return clazz(
        name=array_config["name"],
        topic=array_config[CONF_KEY_TOPIC],
        count=array_config[CONF_KEY_COUNT],
        leds_per_pixel=array_config[CONF_KEY_PER_PIXEL],
        color_order=array_config[CONF_KEY_COLOR_ORDER],
        array_config=array_config
    )


def getConfOptions():
    """
    Return Conf Options from all array types
    """
    conf = {}
    conf = update_dict(conf, rpi.CONF_OPTIONS)
    conf = update_dict(conf, sacn.CONF_OPTIONS)
    return conf
