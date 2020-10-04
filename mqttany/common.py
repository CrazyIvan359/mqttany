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

__all__ = [
    "POISON_PILL",
    "SignalHook",
    "DataType",
    "BusMessage",
    "BusProperty",
    "BusNode",
    "validate_id",
    "validate_tag",
    "update_dict",
]

import collections, signal
from enum import Enum
from typing import Dict, List, Optional, Any
from types import MappingProxyType
import re

import logger
from logger import log_traceback

log = logger.get_logger()

POISON_PILL = {"stop": True}


class SignalHook:
    """
    Hooks to SIGINT, SIGTERM, SIGKILL
    """

    SIGINT = signal.SIGINT
    SIGTERM = signal.SIGTERM
    SIGKILL = signal.SIGKILL

    def __init__(self):
        self._last_signal = None
        try:
            signal.signal(signal.SIGINT, self._signal_received)
        except OSError:
            pass
        try:
            signal.signal(signal.SIGTERM, self._signal_received)
        except OSError:
            pass
        try:
            signal.signal(signal.SIGKILL, self._signal_received)
        except OSError:
            pass

    def _signal_received(self, signum, frame):
        self._last_signal = signal.Signals(signum)  # pylint: disable=no-member

    @property
    def signal(self):
        return self._last_signal

    @property
    def exit(self):
        return self._last_signal in [self.SIGINT, self.SIGTERM, self.SIGKILL]


class DataType(Enum):
    INT = "integer"
    FLOAT = "float"
    BOOL = "boolean"
    STR = "string"
    ENUM = "enum"
    COLOR = "color"
    DATETIME = "datetime"
    DURATION = "duration"


class BusMessage(object):
    """
    Message object used in all queues.

    Args:
        - path (str): path to publish an outgoing message to, or path an incoming message
          was received on.
        - content (str): message content.
        - mqtt_retained (bool): for outgoing messages on MQTT only, if ``None`` then
          default from MQTT module will be used.
        - mqtt_qos (int): for outgoing messages on MQTT only, if ``None`` then
          default from MQTT module will be used.
        - callback (str): **Internal Use** for incoming messages this will be set to the
          name of the function to call if the property is settable.
    """

    __slots__ = "path", "content", "mqtt_retained", "mqtt_qos", "callback"

    def __init__(
        self,
        path: str,
        content: Any,
        mqtt_retained: Optional[bool] = None,
        mqtt_qos: Optional[int] = None,
        callback: Optional[str] = None,
    ):
        path = path.strip("/")
        if len(path.split("/")) < 2:
            raise ValueError(
                f"Message Path '{path}' is less than the minimum 2 levels deep"
            )
        self.path = path
        self.content = content
        self.mqtt_retained = mqtt_retained
        self.mqtt_qos = mqtt_qos
        self.callback = callback

    def __str__(self):
        return f"Message('{self.path}', '{self.content}')"

    def __repr__(self):
        return (
            f"Message(Path: '{self.path}', Content: '{self.content}', "
            f"MQTT Retained: '{self.mqtt_retained}', MQTT QOS: '{self.mqtt_qos}', "
            f"Callback: '{self.callback}')"
        )


class BusProperty(object):
    """
    Property object to be provided to the internal bus by all interface modules in order
    to build a map of all nodes and properties available. Modules may provide as many
    nodes as they need with as many properties as needed. Nodes must be unique within the
    entire application, requests to create a node with a

    Args:
        - name (str): friendly name.
        - datatype (DataType): must be one of Enum ``DataType``.
        - format (str): for numbers it must be the valid range, for enums must be enums.
        - unit (str): one of ``°C``, ``°F``, ``°``, ``L``, ``gal``, ``V``, ``W``, ``A``,
          ``%``, ``m``, ``ft``, ``Pa``, ``psi``, ``#``, or blank, or any other value.
        - settable (bool): ``True`` if this property can receive commands, default ``False``.
        - callback (str): name of a function to call if a message is received that satisfies
          a matching pattern in the communication module it arrived on. Callback must
          accept exactly 1 argument of type ``BusMessage``.
    """

    __slots__ = "name", "datatype", "format", "unit", "settable", "callback", "_tags"

    def __init__(
        self,
        name: str,
        datatype: Optional[DataType] = DataType.STR,
        format: Optional[str] = "",
        unit: Optional[str] = None,
        settable: Optional[bool] = False,
        callback: Optional[str] = None,
        tags: Optional[list] = [],
    ):
        self.name = name
        self.datatype = datatype
        self.format = format
        self.unit = unit
        self.settable = settable
        self.callback = callback
        self._tags = []
        for tag in tags:
            self.add_tag(tag)

    @property
    def tags(self):
        return tuple(self._tags)

    @tags.setter
    def tags(self, value: List[str]):
        self._tags = []
        for tag in value:
            self.add_tag(tag)

    @tags.deleter
    def tags(self):
        self._tags = []

    def add_tag(self, tag: str):
        if not validate_tag(tag):
            raise KeyError(f"Tag '{tag}' is invalid")
        elif tag in self._tags:
            pass
        else:
            self._tags.append(tag)


class BusNode(object):
    """
    Node

    Args:
        - name (str): friendly node name.
        - type (str): node type.
        - tags (list):
        - properties (dict): a dict of ``name: BusProperty`` describing all properties
          in this node.
    """

    __slots__ = "module", "name", "type", "_tags", "_properties"

    def __init__(
        self,
        name: str,
        type: str,
        tags: Optional[List[str]] = [],
        properties: Optional[Dict[str, BusProperty]] = {},
    ):
        self.module = None
        self.name = name
        self.type = type
        self._tags = []
        for tag in tags:
            self.add_tag(tag)
        self._properties = {}
        for property_name in properties:
            self.add_property(property_name, properties[property_name])

    @property
    def tags(self):
        return tuple(self._tags)

    @tags.setter
    def tags(self, value: List[str]):
        self._tags = []
        for tag in value:
            self.add_tag(tag)

    @tags.deleter
    def tags(self):
        self._tags = []

    def add_tag(self, tag: str):
        if not validate_tag(tag):
            raise KeyError(f"Tag '{tag}' is invalid")
        elif tag in self._tags:
            pass
        else:
            self._tags.append(tag)

    @property
    def properties(self):
        return MappingProxyType(self._properties)

    @properties.setter
    def properties(self, value: Dict[str, BusProperty]):
        self._properties = {}
        for name in value:
            self.add_property(name, value[name])

    @properties.deleter
    def properties(self):
        self._properties = {}

    def add_property(self, id: str, prop: BusProperty):
        if not validate_id(id):
            raise KeyError(f"Property id '{id}' is invalid")
        else:
            self._properties[id] = prop


def validate_id(id):
    return not re.search("^-|[^a-z0-9-]|-$", id)


def validate_tag(tag):
    return not re.search("[^a-zA-Z0-9]", tag)


def update_dict(d: dict, u: dict) -> dict:
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


def _call(module, name, **kwargs):
    """
    Calls ``name`` if defined in ``module``
    """
    func = getattr(module, name, None)
    if func is not None:
        retval = False
        if callable(func):
            try:
                retval = func(**kwargs)
            except:
                module.log.error(
                    "An exception occurred while running function '%s'",
                    getattr(func, "__name__", func),
                )
                log_traceback(module.log)
            finally:
                # This function intentionally swallows exceptions. It is only used by
                # the core to call functions in modules. If there is an error in a
                # module the core must continue to run in order to exit gracefully.
                # If the core were to stop because of exceptions in modules, all child
                # processes would be orphaned and would have to be killed by manually
                # sending SIG.TERM or SIG.KILL to them.
                return retval  # pylint: disable=lost-exception
