# Copyright (c) 2012-2019 Roger Light and others
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# and Eclipse Distribution License v1.0 which accompany this distribution.
#
# The Eclipse Public License is available at
#    http://www.eclipse.org/legal/epl-v10.html
# and the Eclipse Distribution License is available at
#   http://www.eclipse.org/org/documents/edl-v10.php.
#
# Contributors:
#    Roger Light - initial API and implementation
#    Ian Craggs - MQTT V5 support

import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

# Log levels
MQTT_LOG_INFO: int = 0x01
MQTT_LOG_NOTICE: int = 0x02
MQTT_LOG_WARNING: int = 0x04
MQTT_LOG_ERR: int = 0x08
MQTT_LOG_DEBUG: int = 0x10
LOGGING_LEVEL: Dict[int, int] = {
    MQTT_LOG_DEBUG: logging.DEBUG,
    MQTT_LOG_INFO: logging.INFO,
    MQTT_LOG_NOTICE: logging.INFO,  # This has no direct equivalent level
    MQTT_LOG_WARNING: logging.WARNING,
    MQTT_LOG_ERR: logging.ERROR,
}

# CONNACK codes
CONNACK_ACCEPTED: int = 0
CONNACK_REFUSED_PROTOCOL_VERSION: int = 1
CONNACK_REFUSED_IDENTIFIER_REJECTED: int = 2
CONNACK_REFUSED_SERVER_UNAVAILABLE: int = 3
CONNACK_REFUSED_BAD_USERNAME_PASSWORD: int = 4
CONNACK_REFUSED_NOT_AUTHORIZED: int = 5

# Error values
MQTT_ERR_AGAIN: int = -1
MQTT_ERR_SUCCESS: int = 0
MQTT_ERR_NOMEM: int = 1
MQTT_ERR_PROTOCOL: int = 2
MQTT_ERR_INVAL: int = 3
MQTT_ERR_NO_CONN: int = 4
MQTT_ERR_CONN_REFUSED: int = 5
MQTT_ERR_NOT_FOUND: int = 6
MQTT_ERR_CONN_LOST: int = 7
MQTT_ERR_TLS: int = 8
MQTT_ERR_PAYLOAD_SIZE: int = 9
MQTT_ERR_NOT_SUPPORTED: int = 10
MQTT_ERR_AUTH: int = 11
MQTT_ERR_ACL_DENIED: int = 12
MQTT_ERR_UNKNOWN: int = 13
MQTT_ERR_ERRNO: int = 14
MQTT_ERR_QUEUE_SIZE: int = 15


def connack_string(connack_code: int) -> str:
    ...


def topic_matches_sub(sub: str, topic: str) -> bool:
    ...


class MQTTMessageInfo(object):
    mid: int
    rc: int

    def __init__(self, mid: int) -> None:
        ...

    def wait_for_publish(self) -> None:
        ...

    def is_published(self) -> bool:
        ...


class MQTTMessage(object):
    """This is a class that describes an incoming or outgoing message. It is
    passed to the on_message callback as the message parameter.

    Members:

    topic : String/bytes. topic that the message was published on.
    payload : String/bytes the message payload.
    qos : Integer. The message Quality of Service 0, 1 or 2.
    retain : Boolean. If true, the message is a retained message and not fresh.
    mid : Integer. The message id.
    properties: Properties class. In MQTT v5.0, the properties associated with the message.

    On Python 3, topic must be bytes.
    """

    timestamp: int
    state: int
    dup: bool
    mid: int
    payload: bytes
    qos: int
    retain: bool
    info: MQTTMessageInfo

    def __init__(self, mid: int = ..., topic: bytes = ...) -> None:
        ...

    @property
    def topic(self) -> str:
        ...

    @topic.setter
    def topic(self, value: str) -> None:
        ...


class Client(object):
    def __init__(
        self,
        client_id: str = ...,
        clean_session: Optional[bool] = ...,
        userdata: Optional[Any] = ...,
        protocol: int = ...,
        transport: str = ...,
    ) -> None:
        ...

    def connect_async(
        self,
        host: str,
        port: int = ...,
        keepalive: int = ...,
        bind_address: str = ...,
        bind_port: int = ...,
        clean_start: int = ...,
        properties: Any = ...,
    ) -> int:
        ...

    def reconnect_delay_set(self, min_delay: int = ..., max_delay: int = ...) -> None:
        ...

    def publish(
        self,
        topic: str,
        payload: Optional[Union[int, float, bytes, str]] = ...,
        qos: int = ...,
        retain: bool = ...,
        properties: Optional[Any] = ...,
    ) -> MQTTMessageInfo:
        ...

    def username_pw_set(
        self, username: Union[str, None], password: Optional[str] = ...
    ) -> None:
        ...

    def is_connected(self) -> bool:
        ...

    def disconnect(
        self, reasoncode: Optional[int] = ..., properties: Optional[Any] = ...
    ) -> int:
        ...

    def subscribe(
        self,
        topic: str,
        qos: int = ...,
        options: Optional[Any] = ...,
        properties: Optional[Any] = ...,
    ) -> Tuple[int, int]:
        ...

    def will_set(
        self,
        topic: str,
        payload: Optional[Union[int, float, bytes, str]] = ...,
        qos: int = ...,
        retain: bool = ...,
        properties: Optional[Any] = ...,
    ) -> None:
        ...

    def loop_start(self) -> None:
        ...

    def loop_stop(self, force: bool = ...) -> Union[int, bool]:
        ...

    @property
    def on_log(self) -> Union[Callable[[Client, Any, int, Any], None], None]:
        ...

    @on_log.setter
    def on_log(self, func: Callable[[Client, Any, int, Any], None]) -> None:
        ...

    @property
    def on_connect(
        self,
    ) -> Union[Callable[[Client, Any, Dict[str, int], int, Any, Any], None], None]:
        ...

    @on_connect.setter
    def on_connect(
        self, func: Callable[[Client, Any, Dict[str, int], int, Any, Any], None]
    ) -> None:
        ...

    @property
    def on_subscribe(
        self,
    ) -> Union[
        Callable[[Client, Any, int, List[int], List[Any], List[Any]], None], None
    ]:
        ...

    @on_subscribe.setter
    def on_subscribe(
        self, func: Callable[[Client, Any, int, List[int], List[Any], List[Any]], None]
    ) -> None:
        ...

    @property
    def on_message(self) -> Union[Callable[[Client, Any, MQTTMessage], None], None]:
        ...

    @on_message.setter
    def on_message(self, func: Callable[[Client, Any, MQTTMessage], None]) -> None:
        ...

    @property
    def on_disconnect(self) -> Union[Callable[[Client, Any, int], None], None]:
        ...

    @on_disconnect.setter
    def on_disconnect(self, func: Callable[[Client, Any, int], None]) -> None:
        ...
