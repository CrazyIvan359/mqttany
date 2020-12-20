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
    "PoisonPill",
    "SignalHook",
    "DataType",
    "BusMessage",
    "PublishMessage",
    "SubscribeMessage",
    "BusProperty",
    "BusNode",
    "validate_id",
    "validate_tag",
    "update_dict",
]

import collections
import re
import signal
import typing as t
from enum import Enum
from types import MappingProxyType

import logger

log = logger.get_logger()


class SignalHook:
    """
    Hooks to SIGINT, SIGTERM, SIGKILL
    """

    SIGINT = signal.SIGINT
    SIGTERM = signal.SIGTERM
    SIGKILL = signal.SIGKILL

    def __init__(self) -> None:
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

    def _signal_received(self, signum: int, frame: t.Any) -> None:
        self._last_signal = signal.Signals(signum)  # pylint: disable=no-member

    @property
    def signal(self) -> t.Union[signal.Signals, None]:
        return self._last_signal

    @property
    def exit(self) -> bool:
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
    Base Message object used in all queues.

    Args:
        - path (str): path to publish an outgoing message to, or path an incoming message
          was received on.
        - content (str): message content.
    """

    __slots__ = "path", "content"

    def __init__(
        self,
        path: str,
        content: t.Any,
    ) -> None:
        path = path.strip("/")
        if len(path.split("/")) < 2:
            raise ValueError(
                f"Message Path '{path}' is less than the minimum 2 levels deep"
            )
        self.path = path
        self.content = content

    def __str__(self) -> str:
        return f"Message('{self.path}', '{self.content}')"

    def __repr__(self) -> str:
        return self.__str__()


class PublishMessage(BusMessage):
    """
    Message object used in Publish queues.

    Args:
        - path (str): path to publish an outgoing message to.
        - content (str): message content.
        - mqtt_retained (bool): for MQTT only, if ``None`` then default from MQTT
          module will be used.
        - mqtt_qos (int): for MQTT only, if ``None`` then default from MQTT module will
          be used.
    """

    __slots__ = "mqtt_retained", "mqtt_qos"

    def __init__(
        self,
        path: str,
        content: t.Any,
        mqtt_retained: t.Optional[bool] = None,
        mqtt_qos: t.Optional[int] = None,
    ) -> None:
        super().__init__(path, content)
        self.mqtt_retained = mqtt_retained
        self.mqtt_qos = mqtt_qos

    def __str__(self) -> str:
        return f"PublishMessage('{self.path}', '{self.content}')"

    def __repr__(self) -> str:
        return (
            f"PublishMessage(Path: '{self.path}', Content: '{self.content}', "
            f"MQTT Retained: '{self.mqtt_retained}', MQTT QOS: '{self.mqtt_qos}')"
        )


class SubscribeMessage(BusMessage):
    """
    Message object used in Subscribe queues.

    Args:
        - path (str): path message was received on.
        - content (str): message content.
        - callback (str): **Internal Use** this will be set to the name of the function
          to call.
    """

    __slots__ = "callback"

    def __init__(
        self,
        path: str,
        content: t.Any,
        callback: str,
    ) -> None:
        super().__init__(path, content)
        self.callback = callback

    def __str__(self) -> str:
        return f"SubscribeMessage('{self.path}', '{self.content}')"

    def __repr__(self) -> str:
        return (
            f"SubscribeMessage(Path: '{self.path}', Content: '{self.content}', "
            f"Callback: '{self.callback}')"
        )


class PoisonPill(BusMessage):
    """
    Special Message object used to shutdown modules
    """

    def __init__(self) -> None:
        self.path = ""
        self.content = None


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
        datatype: DataType = DataType.STR,
        format: str = "",
        unit: t.Optional[str] = None,
        settable: bool = False,
        callback: t.Optional[str] = None,
        tags: t.List[str] = [],
    ) -> None:
        self.name = name
        self.datatype = datatype
        self.format = format
        self.unit = unit
        self.settable = settable
        self.callback = callback
        self._tags: t.List[str] = []
        for tag in tags:
            self.add_tag(tag)

    @property
    def tags(self) -> t.Iterable[str]:
        return tuple(self._tags)

    @tags.setter
    def tags(self, value: t.Iterable[str]) -> None:
        self._tags = []
        for tag in value:
            self.add_tag(tag)

    @tags.deleter
    def tags(self) -> None:
        self._tags = []

    def add_tag(self, tag: str) -> None:
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
        tags: t.List[str] = [],
        properties: t.Dict[str, BusProperty] = {},
    ) -> None:
        self.module: str = None  # type: ignore
        self.name = name
        self.type = type
        self._tags: t.List[str] = []
        for tag in tags:
            self.add_tag(tag)
        self._properties: t.Dict[str, BusProperty] = {}
        for property_name in properties:
            self.add_property(property_name, properties[property_name])

    @property
    def tags(self) -> t.Iterable[str]:
        return tuple(self._tags)

    @tags.setter
    def tags(self, value: t.Iterable[str]) -> None:
        self._tags = []
        for tag in value:
            self.add_tag(tag)

    @tags.deleter
    def tags(self) -> None:
        self._tags = []

    def add_tag(self, tag: str) -> None:
        if not validate_tag(tag):
            raise KeyError(f"Tag '{tag}' is invalid")
        elif tag in self._tags:
            pass
        else:
            self._tags.append(tag)

    @property
    def properties(self) -> t.Mapping[str, BusProperty]:
        return MappingProxyType(self._properties)

    @properties.setter
    def properties(self, value: t.Mapping[str, BusProperty]) -> None:
        self._properties = {}
        for name in value:
            self.add_property(name, value[name])

    @properties.deleter
    def properties(self) -> None:
        self._properties = {}

    def add_property(self, id: str, prop: BusProperty) -> None:
        if not validate_id(id):
            raise KeyError(f"Property id '{id}' is invalid")
        else:
            self._properties[id] = prop


def validate_id(id: str) -> bool:
    return not re.search("^-|[^a-z0-9-]|-$", id)


def validate_tag(tag: str) -> bool:
    return not re.search("[^a-zA-Z0-9]", tag)


def update_dict(
    d: t.MutableMapping[t.Any, t.Any], u: t.Mapping[t.Any, t.Any]
) -> t.MutableMapping[t.Any, t.Any]:
    """
    Recursively update dict ``d`` with dict ``u``
    """
    for k in u:
        dv = d.get(k, {})
        if not isinstance(dv, collections.MutableMapping):  # type: ignore
            d[k] = u[k]
        elif isinstance(u[k], collections.Mapping):  # type: ignore
            d[k] = update_dict(dv, u[k])
        else:
            d[k] = u[k]
    return d
