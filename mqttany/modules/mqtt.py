"""
***********
MQTT Module
***********

:Author: Michael Murton
"""
# Copyright (c) 2019-2022 MQTTany contributors
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

__all__ = []

import multiprocessing as mproc
import socket
import sys
import typing as t
from collections import OrderedDict
from threading import Timer

import logger
import version
from common import BusMessage, PublishMessage, SubscribeMessage
from config import parse_config

from modules import ModuleType

try:
    import paho.mqtt.client as mqtt
    from paho.mqtt.client import (
        MQTT_LOG_DEBUG,
        MQTT_LOG_ERR,
        MQTT_LOG_INFO,
        MQTT_LOG_NOTICE,
        MQTT_LOG_WARNING,
    )
except ModuleNotFoundError:
    pass

_module_type = ModuleType.COMMUNICATION  # type: ignore

log = logger.get_logger()
CONFIG: t.Dict[str, t.Any] = {}

core_queue: "mproc.Queue[str]" = None  # type: ignore
receive_queue: "mproc.Queue[BusMessage]" = None  # type: ignore
transmit_queue: "mproc.Queue[BusMessage]" = None  # type: ignore
resend_queue: "mproc.Queue[BusMessage]" = None  # type: ignore

CONF_KEY_HOST = "host"
CONF_KEY_PORT = "port"
CONF_KEY_CLIENTID = "client id"
CONF_KEY_USERNAME = "username"
CONF_KEY_PASSWORD = "password"
CONF_KEY_QOS = "qos"
CONF_KEY_RETAIN = "retain"
CONF_KEY_TOPIC_ROOT = "root topic"
CONF_KEY_TOPIC_STATUS = "status topic"
CONF_KEY_TOPIC_LWT = "lwt topic"
CONF_KEY_HEARTBEAT_INT = "heartbeat interval"

CONF_OPTIONS: t.MutableMapping[str, t.Dict[str, t.Any]] = OrderedDict(
    [
        (CONF_KEY_HOST, {}),
        (CONF_KEY_PORT, {"type": int, "default": 1883}),
        (CONF_KEY_CLIENTID, {"default": "{hostname}"}),
        (CONF_KEY_USERNAME, {"default": ""}),
        (CONF_KEY_PASSWORD, {"default": "", "secret": True}),
        (CONF_KEY_QOS, {"type": int, "default": 0}),
        (CONF_KEY_RETAIN, {"type": bool, "default": False}),
        (CONF_KEY_TOPIC_ROOT, {"default": "{client_id}"}),
        (CONF_KEY_TOPIC_LWT, {"default": "lwt"}),
        (CONF_KEY_HEARTBEAT_INT, {"type": int, "default": 300}),
    ]
)

MQTT_MAX_RETRIES = 10

client = None
retries = MQTT_MAX_RETRIES
heartbeat_timer = None


def load(config_raw: t.Dict[str, t.Any]) -> bool:
    """
    This function runs on the main process after the module is imported. It should parse
    and validate the configuration and do other basic setup of the module. Do not start
    any threads or long running tasks here, they should go in the ``start`` function.
    """
    if not hasattr(sys.modules[__name__], "mqtt"):
        log.error(
            "MQTTany's MQTT module requires 'paho-mqtt' to be installed, "
            "please see the wiki for instructions on how to install requirements"
        )
        return False

    config_data = parse_config(config_raw, CONF_OPTIONS, log)
    del config_raw
    if config_data:
        log.debug("Config loaded successfully")

        config_data[CONF_KEY_CLIENTID] = config_data[CONF_KEY_CLIENTID].format(
            hostname=socket.gethostname()
        )

        config_data[CONF_KEY_TOPIC_ROOT] = config_data[CONF_KEY_TOPIC_ROOT].format(
            hostname=socket.gethostname(), client_id=config_data[CONF_KEY_CLIENTID]
        )

        config_data[
            CONF_KEY_TOPIC_LWT
        ] = f"{config_data[CONF_KEY_TOPIC_ROOT]}/{config_data[CONF_KEY_TOPIC_LWT]}"

        CONFIG.update(config_data)
        del config_data
        return True
    else:
        log.error("Error loading config")
        return False


def client_logger() -> t.Callable[[t.Any, t.Any, int, t.Any], None]:

    LEVEL_MAP: t.Dict[int, int] = {
        MQTT_LOG_INFO: logger.LogLevel.DEBUG,
        MQTT_LOG_NOTICE: logger.LogLevel.DEBUG,
        MQTT_LOG_WARNING: logger.LogLevel.WARN,
        MQTT_LOG_ERR: logger.LogLevel.ERROR,
        MQTT_LOG_DEBUG: logger.LogLevel.TRACE,
    }

    client_log = logger.get_logger(f"{log.name}.client")

    def log_callback(client: mqtt, userdata: t.Any, level: int, buf: t.Any) -> None:
        client_log.log(LEVEL_MAP[level], buf)

    return log_callback


def start() -> None:
    """
    This function runs on the module's dedicated process when it is started. Connections
    should be started here and a listener thread should be created for receiving messages
    from the outside connection if required.
    """

    global client
    log.debug("Creating MQTT client")
    client = mqtt.Client(client_id=CONFIG[CONF_KEY_CLIENTID], clean_session=False)
    client.username_pw_set(
        username=CONFIG[CONF_KEY_USERNAME], password=CONFIG[CONF_KEY_PASSWORD]
    )
    client.will_set(
        topic=CONFIG[CONF_KEY_TOPIC_LWT],
        payload="Dropped",
        qos=CONFIG[CONF_KEY_QOS],
        retain=True,
    )
    client.reconnect_delay_set(min_delay=1, max_delay=60)

    log.debug("Attaching callbacks")
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message  # called for messages without a specfic subscriber
    client.on_log = client_logger()

    log.debug("Queuing connect event")
    client.connect_async(
        host=CONFIG[CONF_KEY_HOST], port=CONFIG[CONF_KEY_PORT], keepalive=15
    )

    log.debug("Starting MQTT client thread")
    client.loop_start()


def stop() -> None:
    """
    This function runs on the module's dedicated process when it is exiting. Connections
    should be closed and threads stopped.
    """
    local_client = t.cast(mqtt.Client, client)

    log.debug("Disconnecting")
    discon_msg = local_client.publish(
        topic=CONFIG[CONF_KEY_TOPIC_LWT], payload="Offline", retain=True
    )
    if discon_msg.rc == mqtt.MQTT_ERR_SUCCESS:
        discon_msg.wait_for_publish()
    local_client.disconnect()
    log.debug("Stopping MQTT client loop")
    local_client.loop_stop()


def publish(
    topic: str,
    payload: t.Union[int, float, bytes, str],
    qos: t.Optional[int] = None,
    retain: t.Optional[bool] = None,
) -> None:
    local_client = t.cast(mqtt.Client, client)
    local_client.publish(
        topic=topic,
        payload=payload,
        qos=qos if qos is not None else CONFIG[CONF_KEY_QOS],
        retain=retain if retain is not None else CONFIG[CONF_KEY_RETAIN],
    )


def on_connect(
    client: t.Any,
    userdata: t.Any,
    flags: t.Dict[str, int],
    rc: int,
    reasonCode: t.Any = None,
    properties: t.Any = None,
) -> None:
    """
    Gets called when the client connect attempt finishes
    """

    global retries
    local_client = t.cast(mqtt.Client, client)

    if rc == mqtt.CONNACK_ACCEPTED:
        log.info(
            "Connected to broker '%s:%s'", CONFIG[CONF_KEY_HOST], CONFIG[CONF_KEY_PORT]
        )
        retries = MQTT_MAX_RETRIES  # reset max retries counter
        log.debug(
            "Resuming previous session"
            if flags["session present"]
            else "Starting new session"
        )
        local_client.subscribe(f"{CONFIG[CONF_KEY_TOPIC_ROOT]}/+/+/+/#")
        publish_heartbeat()

    elif rc == mqtt.CONNACK_REFUSED_IDENTIFIER_REJECTED:
        log.error(
            "Connection refused: client_id '%s' is invalid", CONFIG[CONF_KEY_CLIENTID]
        )
        local_client.disconnect()
        core_queue.put_nowait(__name__)

    elif rc == mqtt.CONNACK_REFUSED_SERVER_UNAVAILABLE:
        retries -= 1
        if retries > 0:
            log.warn(
                "Connection attempt failed, server did not respond. %d retries left",
                retries,
            )
        else:  # too many retries, give up
            log.error("Connection to broker failed, server did not respond.")
            local_client.disconnect()
            core_queue.put_nowait(__name__)

    else:
        log.error("%s (%s)", mqtt.connack_string(rc), rc)
        local_client.disconnect()
        core_queue.put_nowait(__name__)


def on_disconnect(client: t.Any, userdata: t.Any, rc: int) -> None:
    """
    Gets called when the client disconnects from the broker
    """
    if heartbeat_timer:
        heartbeat_timer.cancel()


def on_message(client: t.Any, userdata: t.Any, message: t.Any) -> None:
    """
    Gets called when an MQTT message is received
    """
    message = t.cast(mqtt.MQTTMessage, message)

    if mqtt.topic_matches_sub(f"{CONFIG[CONF_KEY_TOPIC_ROOT]}/+/+/+/#", message.topic):
        receive_queue.put_nowait(
            SubscribeMessage(
                path="/".join(message.topic.strip("/").split("/")[1:]),
                content=message.payload.strip(bytes([0])).decode(),
                callback="",
            )
        )


def publish_heartbeat() -> None:
    """
    Publishes the heartbeat messages and restarts the timer
    """
    log.debug("Heartbeat")

    publish(CONFIG[CONF_KEY_TOPIC_LWT], payload="Online", retain=True)
    publish(f"{CONFIG[CONF_KEY_TOPIC_ROOT]}/version", payload=version.__version__)

    if CONFIG[CONF_KEY_HEARTBEAT_INT] > 0:
        global heartbeat_timer
        heartbeat_timer = Timer(CONFIG[CONF_KEY_HEARTBEAT_INT], publish_heartbeat)
        heartbeat_timer.start()


def transmit_callback(message: PublishMessage) -> bool:
    publish(
        topic=f"{CONFIG[CONF_KEY_TOPIC_ROOT]}/{message.path}",
        payload=message.content,
        retain=message.mqtt_retained,
        qos=message.mqtt_qos,
    )
    return True


def transmit_ready() -> bool:
    local_client = t.cast(mqtt.Client, client)
    return local_client.is_connected()
