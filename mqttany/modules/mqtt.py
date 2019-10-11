"""
***********
MQTT Module
***********

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

try:
    import paho.mqtt.client as mqtt
    from paho.mqtt.client import topic_matches_sub as mqtt_topic_matches_sub
except ImportError:
    raise ImportError("MQTTany's MQTT module requires 'paho-mqtt' to be installed, \
        please see the wiki for instructions on how to install requirements")

import socket

import logger
from logger import log_traceback
from mqttany import queue as main_queue
from config import parse_config
from common import POISON_PILL

all = [
    "resolve_topic", "topic_matches_sub",
    "publish", "subscribe", "unsubscribe",
    "add_message_callback", "remove_message_callback"
    "register_on_connect_callback", "register_on_disconnect_callback"
]

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

CONF_OPTIONS = {
    CONF_KEY_HOST: {},
    CONF_KEY_PORT: {"type": int, "default": 1883},
    CONF_KEY_CLIENTID: {"default": "{hostname}"},
    CONF_KEY_USERNAME: {"default": ""},
    CONF_KEY_PASSWORD: {"default": ""},
    CONF_KEY_QOS: {"type": int, "default": 0},
    CONF_KEY_RETAIN: {"type": bool, "default": False},
    CONF_KEY_TOPIC_ROOT: {"default": "{client_id}"},
    CONF_KEY_TOPIC_LWT: {"default": "lwt"},
}

MQTT_MAX_RETRIES = 10

log = logger.get_module_logger()
queue = None
config = {}
hostname = socket.gethostname()
client = None
retries = MQTT_MAX_RETRIES
subscriptions = []
on_message_callbacks = []
on_connect_callbacks = []
on_disconnect_callbacks = []


def init(config_data={}):
    """
    Initializes the module
    """
    raw_config = parse_config(config_data, CONF_OPTIONS, log)
    del config_data
    if raw_config:
        log.debug("Config loaded")

        raw_config[CONF_KEY_CLIENTID] = raw_config[CONF_KEY_CLIENTID].format(
                hostname=hostname)

        raw_config[CONF_KEY_TOPIC_ROOT] = raw_config[CONF_KEY_TOPIC_ROOT].format(
                hostname=hostname, client_id=raw_config[CONF_KEY_CLIENTID])

        config.update(raw_config)
        del raw_config
        return True
    else:
        log.error("Error loading config")
        return False


def pre_loop():
    """
    Actions to be done in the subprocess before the loop starts
    """
    global client
    log.debug("Creating MQTT client")
    client = mqtt.Client(
            client_id=config[CONF_KEY_CLIENTID],
            clean_session=False
        )
    client.username_pw_set(
            username=config[CONF_KEY_USERNAME],
            password=config[CONF_KEY_PASSWORD]
        )
    client.will_set(
            topic=resolve_topic(config[CONF_KEY_TOPIC_LWT]),
            payload="Offline",
            qos=config[CONF_KEY_QOS],
            retain=True
        )
    client.reconnect_delay_set(
            min_delay=1,
            max_delay=60
        )

    log.debug("Attaching callbacks")
    client._on_connect = _on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message # called for messages without a specfic subscriber
    client.enable_logger(logger=logger.get_logger("{}.client".format(log.name)))

    log.debug("Queuing connect event")
    client.connect_async(
            host=config[CONF_KEY_HOST],
            port=config[CONF_KEY_PORT],
            keepalive=15
        )

    log.debug("Starting MQTT client thread")
    client.loop_start()


def post_loop():
    """
    Actions to be done in the subprocess after the loop is exited
    """
    log.debug("Disconnecting")
    discon_msg = client.publish(
            topic=resolve_topic(config[CONF_KEY_TOPIC_LWT]),
            payload="Offline",
            retain=True
        )
    if discon_msg.rc == mqtt.MQTT_ERR_SUCCESS: discon_msg.wait_for_publish()
    client.disconnect()
    log.debug("Stopping MQTT client loop")
    client.loop_stop()


def resolve_topic(topic, subtopics=[], substitutions={}):
    """
    Resolves an absolute topic (wildcards preserved).
    Absolute topics start with ``/`` (it will be stripped).
    Relative topics will have ``{root_topic}/subtopics[0]/subtopics[n]/``prepended.
    Will sub in ``root_topic``, ``hostname``, ``client_id``, and anything in ``substitutions``.
    """
    if topic[0] != "/": # relative topic
        if topic.split("/")[0] not in ["{root_topic}", config[CONF_KEY_TOPIC_ROOT]]: # topic already starts with root topic
            for i in range(len(subtopics)-1, -1, -1):
                topic = subtopics[i] + "/" + topic
            topic = "{root_topic}/" + topic

    # remove reserved substitutions
    substitutions.pop("root_topic", None)
    substitutions.pop("hostname", None)
    substitutions.pop("client_id", None)

    for i in range(4):
        # this is done in case any substitutions contain substitutions
        topic = topic.format(
            root_topic=config[CONF_KEY_TOPIC_ROOT],
            hostname=hostname,
            client_id=config[CONF_KEY_CLIENTID],
            **substitutions
        )

    topic = topic.replace(" ", "_") # remove spaces
    return topic

def topic_matches_sub(sub, topic):
    """Check whether a topic matches a subscription.

    For example:

    foo/bar would match the subscription foo/# or +/bar
    non/matching would not match the subscription non/+/+
    """
    return mqtt_topic_matches_sub(sub.strip("/"), topic.strip("/"))

def publish(topic, payload, qos=None, retain=None, subtopics=[], substitutions={}):
    """
    Publish a message
    """
    queue.put_nowait({
            "func": "_publish",
            "args": [topic, payload],
            "kwargs": {
                "qos": qos,
                "retain": retain,
                "subtopics": subtopics,
                "substitutions": substitutions
            }
        })

def _publish(topic, payload, qos=None, retain=None, subtopics=[], substitutions={}):
    client.publish(
            resolve_topic(topic, subtopics=subtopics, substitutions=substitutions).strip("/"),
            payload=payload,
            qos=qos if qos is not None else config[CONF_KEY_QOS],
            retain=retain if retain is not None else config[CONF_KEY_RETAIN]
        )


def subscribe(topic, qos=0, callback=None, subtopics=[], substitutions={}):
    """
    Adds a subscription, can use wildcard topics.
    If ``callback`` is specified a ``message_callback`` will be added.
    """
    queue.put_nowait({
            "func": "_subscribe",
            "args": [topic],
            "kwargs": {
                "qos": qos,
                "callback": callback,
                "subtopics": subtopics,
                "substitutions": substitutions
            }
        })

def _subscribe(topic, qos=0, callback=None, subtopics=[], substitutions={}):
    topic = resolve_topic(topic, subtopics=subtopics, substitutions=substitutions).strip("/")
    log.debug("Subscribing to topic '{topic}'".format(topic=topic))
    if not [sub for sub in subscriptions if sub["topic"] == topic]:
        subscriptions.append({"topic": topic, "qos": qos})
    client.subscribe(topic, qos=qos)
    if callback: _add_message_callback(topic, callback)


def unsubscribe(topic, callback=None, subtopics=[], substitutions={}):
    """
    Removes a subscription.
    If ``callback`` is specified it will also remove the ``message_callback``
    matching the ``topic`` and ``callback``.
    """
    queue.put_nowait({
            "func": "_unsubscribe",
            "args": [topic],
            "kwargs": {
                "callback": callback,
                "subtopics": subtopics,
                "substitutions": substitutions
            }
        })

def _unsubscribe(topic, callback=None, subtopics=[], substitutions={}):
    topic = resolve_topic(topic, subtopics=subtopics, substitutions=substitutions).strip("/")
    log.debug("Removing subscription to topic '{topic}'".format(topic=topic))
    subs = [sub for sub in subscriptions if sub["topic"] == topic]
    for sub in subs: subscriptions.remove(sub)
    client.unsubscribe(topic)
    if callback: _remove_message_callback(topic)


def add_message_callback(topic, callback, subtopics=[], substitutions={}):
    """
    Adds a message callback
    """
    queue.put_nowait({
            "func": "_add_message_callback",
            "args": [topic, callback],
            "kwargs": {
                "subtopics": subtopics,
                "substitutions": substitutions
            }
        })

def _add_message_callback(topic, callback, subtopics=[], substitutions={}):
    topic = resolve_topic(topic, subtopics=subtopics, substitutions=substitutions).strip("/")
    if not [cb for cb in on_message_callbacks if cb["topic"] == topic]:
        log.debug("Adding callback '{callback}' for messages matching topic '{topic}'".format(
                callback=callback.__name__, topic=topic))
        on_message_callbacks.append({"topic": topic, "func": callback})
        client.message_callback_add(topic, callback)
    else:
        log.debug("Failed to register callback '{callback}', a callback for the topic string '{topic}' already exists".format(
                callback=callback.__name__, topic=topic))


def remove_message_callback(topic, subtopics=[], substitutions={}):
    """
    Removes a message callback
    """
    queue.put_nowait({
            "func": "_remove_message_callback",
            "args": [topic],
            "kwargs": {
                "subtopics": subtopics,
                "substitutions": substitutions
            }
        })

def _remove_message_callback(topic, subtopics=[], substitutions={}):
    topic = resolve_topic(topic, subtopics=subtopics, substitutions=substitutions).strip("/")
    log.debug("Removing callback for messages matching topic '{topic}'".format(topic=topic))
    cbs = [cb for cb in on_message_callbacks if cb["topic"] == topic]
    for cb in cbs: on_message_callbacks.remove(cb)
    client.message_callback_remove(topic)


def register_on_connect_callback(callback, args=[], kwargs={}):
    """
    Registers a callback to be called when MQTT connects
    """
    queue.put_nowait({
        "func": "_register_on_connect_callback",
        "args": [callback],
        "kwargs": {
            "args": args,
            "kwargs": kwargs
        }
    })

def _register_on_connect_callback(callback, args=[], kwargs={}):
    if not [cb for cb in on_connect_callbacks if cb["func"] == callback]:
        log.debug("Adding on-connect callback '{callback}'".format(callback=callback.__name__))
        on_connect_callbacks.append({
                "func": callback,
                "args": args,
                "kwargs": kwargs
            })
    else:
        log.debug("Failed to register on-connect callback '{callback}', already exists".format(
                callback=callback.__name__))


def register_on_disconnect_callback(callback, args=[], kwargs={}):
    """
    Registers a callback to be called when MQTT disconnects
    """
    queue.put_nowait({
            "func": "_register_on_disconnect_callback",
            "args": [callback],
            "kwargs": {
                "args": args,
                "kwargs": kwargs
            }
        })

def _register_on_disconnect_callback(callback, args=[], kwargs={}):
    if not [cb for cb in on_disconnect_callbacks if cb["func"] == callback]:
        log.debug("Adding on-disconnect callback '{callback}'".format(callback=callback.__name__))
        on_disconnect_callbacks.append({
                "func": callback,
                "args": args,
                "kwargs": kwargs
            })
    else:
        log.debug("Failed to register on-disconnect callback '{callback}', already exists".format(
                callback=callback.__name__))


def _on_connect(client, userdata, flags, rc):
    """
    Gets called when the client connect attempt finishes
    """
    global retries

    if rc == 0: # connected successfully
        log.info("Connected to broker '{host}:{port}'".format(
                host=config[CONF_KEY_HOST], port=config[CONF_KEY_PORT]))
        retries = MQTT_MAX_RETRIES # reset max retries counter
        log.debug("Resuming previous session" if flags["session present"] else "Starting new session")
        client.publish(
            topic=resolve_topic(config[CONF_KEY_TOPIC_LWT]),
            payload="Online",
            retain=True
        )
        for sub in subscriptions:
            subscribe(**sub)
        for callback in on_connect_callbacks:
            try:
                callback["func"](*callback.get("args", []), **callback.get("kwargs", {}))
            except:
                log.error("An exception occurred while running on-connect callback '{func}'".format(
                        func=getattr(callback["func"], "__name__", default=callback["func"])))
                log_traceback(log)

    elif rc == 1: # refused: incorrect mqtt protocol version
        log.error("Connection refused: broker uses a different MQTT protocol version")
        client.disconnect()
        main_queue.put_nowait(POISON_PILL)

    elif rc == 2: # refused: client_id invalid
        log.error("Connection refused: client_id '{client_id}' is invalid".format(client_id=config[CONF_KEY_CLIENTID]))
        client.disconnect()
        main_queue.put_nowait(POISON_PILL)

    elif rc == 3: # refused: server unavailable
        retries -= 1
        if retries > 0:
            log.warn("Connection attempt failed, server did not respond. {retries} retries left".format(retries=retries))
        else: # too many retries, give up
            log.error("Connection to broker failed, server did not respond.")
            client.disconnect()
            main_queue.put_nowait(POISON_PILL)

    elif rc == 4: # refused: bad username and/or password
        log.error("Connection refused: username or password incorrect")
        client.disconnect()
        main_queue.put_nowait(POISON_PILL)

    elif rc == 5: # refused: not authorized
        log.error("Connection refused: you are not authorized on this broker")
        client.disconnect()
        main_queue.put_nowait(POISON_PILL)

    else: # invalid rc
        log.error("Connection failed: invalid return code '{code}' received".format(code=rc))
        client.disconnect()
        main_queue.put_nowait(POISON_PILL)

def on_disconnect(client, userdata, rc):
    """
    Gets called when the client disconnects from the broker
    """
    for callback in on_disconnect_callbacks:
        try:
            callback["func"](*callback.get("args", []), **callback.get("kwargs", {}))
        except:
            log.error("An exception occurred while running on-disconnect callback '{func}'".format(
                    func=getattr(callback["func"], "__name__", default=callback["func"])))
            log_traceback(log)

def on_message(client, userdata, message):
    """
    Gets called when a message is received on a topic without a specific listener
    """
    log.debug("Received message without specific listener: [topic: '{topic}', message: '{message}']".format(
            topic=message.topic, message=message.payload))
