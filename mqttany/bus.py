"""
***********
Pub/Sub Bus
***********

:Author: Michael Murton
"""
# Copyright (c) 2019-2025 MQTTany contributors
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

__all__ = ["data_tree", "get_property_from_path"]


import multiprocessing as mproc
import sys
import threading
import types
import typing as t
from queue import Empty as QueueEmptyError

import logger
from common import BusMessage, BusNode, BusProperty, PublishMessage, SubscribeMessage
from modules import (
    ATTR_NODES,
    ATTR_QCORE,
    ATTR_QPUBLISH,
    ATTR_QRECEIVE,
    ATTR_QRESEND,
    ATTR_QSUBSCRIBE,
    ATTR_QTRANSMIT,
)

log = logger.get_logger("bus")

# Communication module queues
receive_queue: "mproc.Queue[BusMessage]" = mproc.Queue()
transmit_queues: t.Dict[str, "mproc.Queue[BusMessage]"] = {}

# Interface module queues
publish_queue: "mproc.Queue[BusMessage]" = mproc.Queue()
subscribe_queues: t.Dict[str, "mproc.Queue[BusMessage]"] = {}

# Data tree
data_tree: t.Dict[str, BusNode] = {}

# Message Bus threads
_thread_receive: threading.Thread = None  # type: ignore
_thread_transmit: threading.Thread = None  # type: ignore
poison_pill = False


class ReceiveThread(threading.Thread):
    """
    Message bus receive->subscribe thread
    """

    def __init__(self) -> None:
        super().__init__(name="Receive")
        self.log = logger.get_logger("bus.receive")

    def run(self) -> None:
        self.log.trace("Message Bus Receive thread started successfully")
        try:
            while not poison_pill:
                try:
                    message = receive_queue.get(timeout=1)
                except QueueEmptyError:
                    pass
                else:
                    if isinstance(message, SubscribeMessage):
                        self.log.trace("Message received on receive queue: %s", message)
                        node, prop = get_property_from_path(message.path)
                        if node and prop and prop.callback:
                            message.callback = prop.callback
                            getattr(
                                sys.modules[node.module], ATTR_QSUBSCRIBE
                            ).put_nowait(message)
                        elif not prop:
                            self.log.debug(
                                "Received message on unregistered path: %s", message
                            )
                    else:
                        try:
                            self.log.warn(
                                "Got unrecognized message on receive queue: %s", message
                            )
                        except:
                            self.log.warn("Got unrecognized message on receive queue")
        except Exception as err:  # pylint: disable=broad-except
            self.log.error("Error on Message Bus Receive thread")
            self.log.error("  %s", err)
            logger.log_traceback(self.log)
        else:
            self.log.debug("Message Bus Receive thread stopped cleanly")


class TransmitThread(threading.Thread):
    """
    Message bus publish->transmit loop
    """

    def __init__(self) -> None:
        super().__init__(name="Transmit")
        self.log = logger.get_logger("bus.transmit")

    def run(self) -> None:
        self.log.trace("Message Bus Transmit thread started successfully")
        try:
            while not poison_pill:
                try:
                    message = publish_queue.get(timeout=1)
                except QueueEmptyError:
                    pass
                else:
                    if isinstance(message, PublishMessage):
                        self.log.trace("Message received on publish queue: %s", message)
                        for q in transmit_queues:
                            transmit_queues[q].put_nowait(message)
                    else:
                        try:
                            self.log.warn(
                                "Got unrecognized message on publish queue: %s", message
                            )
                        except:
                            self.log.warn("Got unrecognized message on publish queue")
        except Exception as err:  # pylint: disable=broad-except
            self.log.error("Error on Message Bus Transmit thread")
            self.log.error("  %s", err)
            logger.log_traceback(self.log)
        else:
            self.log.debug("Message Bus Transmit thread stopped cleanly")


def setup_comm_module(module: types.ModuleType, core_queue: "mproc.Queue[str]") -> None:
    """
    Add required queues to communication module.
    """
    module_name = ".".join(module.__name__.split(".")[1:2])

    if hasattr(module, "receive_queue"):
        setattr(module, ATTR_QRECEIVE, receive_queue)
        log.debug("Module '%s' added as a receiver", module_name)

    if module_name not in transmit_queues:
        transmit_queues[module_name] = mproc.Queue()
    setattr(module, ATTR_QTRANSMIT, transmit_queues[module_name])
    setattr(module, ATTR_QRESEND, mproc.Queue())
    setattr(module, ATTR_QCORE, core_queue)
    log.debug("Module '%s' added as a transmitter", module_name)


def setup_interface_module(module: types.ModuleType) -> None:
    """
    Add required queues to interface module and parse nodes.
    """
    module_name = ".".join(module.__name__.split(".")[1:2])

    if hasattr(module, "publish_queue"):
        setattr(module, ATTR_QPUBLISH, publish_queue)
        log.debug("Module '%s' added as a publisher", module_name)

    if module_name not in subscribe_queues:
        subscribe_queues[module_name] = mproc.Queue()
    setattr(module, ATTR_QSUBSCRIBE, subscribe_queues[module_name])
    log.debug("Module '%s' added as a subscriber", module_name)

    nodes: t.Dict[str, BusNode] = getattr(module, ATTR_NODES, {})  # type:ignore
    for id in nodes:
        if id not in data_tree:
            nodes[id].module = f"modules.{module_name}"
            data_tree[id] = nodes[id]
        else:
            log.warn(
                "Failed to register node '%s' for module '%s', already "
                "registered by module '%s'",
                id,
                module_name,
                data_tree[id].module,
            )


def start() -> bool:
    """
    Start Message Bus
    """

    def _start_thread(thread: threading.Thread) -> None:
        try:
            log.debug("Starting Message Bus %s thread", thread.name)
            thread.start()
        except Exception as err:  # pylint: disable=broad-except
            log.error("Failed to start Message Bus %s thread", thread.name)
            log.error("  %s", err)
            logger.log_traceback(log)

    global _thread_receive, _thread_transmit
    _thread_receive = ReceiveThread()
    _thread_transmit = TransmitThread()
    _start_thread(_thread_receive)
    _start_thread(_thread_transmit)
    return True if _thread_receive and _thread_transmit else False


def stop() -> None:
    """
    Stop Message Bus
    """

    def _stop_thread(thread: threading.Thread) -> None:
        if thread:
            if thread.is_alive():
                log.trace(
                    "Stopping Message Bus %s thread with 10s timeout", thread.name
                )
                thread.join(10)
                if thread.is_alive():
                    log.warn(
                        "Message Bus %s thread did not stop when requested", thread.name
                    )
            else:
                thread.join(10)
                # second thread was already stopped by the time this func is called
                # log.warn("Message Bus %s thread was not running", thread.name)

    log.trace("Stopping Message Bus threads")
    global poison_pill
    poison_pill = True
    _stop_thread(_thread_receive)
    _stop_thread(_thread_transmit)


def get_property_from_path(
    path: str,
) -> t.Tuple[t.Union[BusNode, None], t.Union[BusProperty, None]]:
    """
    Returns the a tuple of the Node and Property from ``data_tree`` matching ``path``.
    If no Node is found it will return ``(None, None)``. If a Node is found but no
    Property is found it will return ``(BusNode, None)``.
    """
    if len(path.split("/")) < 2:
        # invalid path
        return None, None

    node = data_tree.get(path.split("/")[0])
    prop = None
    if node:
        prop = node.properties.get(path.split("/")[1])
    return node, prop
