"""
*************************
Interface Module Template
*************************

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

import typing as t

from config import parse_config

from common import BusNode, BusProperty, DataType, SubscribeMessage

from . import common
from .common import (
    CONF_KEY_FIXED_TYPE,
    CONF_KEY_SELECTION,
    CONF_KEY_STRING,
    CONF_KEY_SUBSECTION,
    CONF_OPTIONS,
    CONFIG,
    log,
    nodes,
)


def load(config_raw: t.Dict[str, t.Any]) -> bool:
    """
    This function runs on the main process after the module is imported. It should parse
    and validate the configuration and create any dynamic nodes or properties. Do not start
    any threads or long running tasks here, they should go in the ``start`` function.
    Limit memory usage here as much as possible.
    """
    config_data = parse_config(config_raw, CONF_OPTIONS, log)
    del config_raw
    if config_data:
        log.debug("Config loaded successfully")
        CONFIG.update(config_data)
        del config_data
        # verify config

        # generate dynamic nodes
        nodes["my-node"] = BusNode(
            name="My Node",
            type="module",
            properties={
                # This property is a string type that this module can publish to
                "my-property": BusProperty(name="Read-Only Property"),
                # This property is an integer that outside systems can set
                "my-writable-property": BusProperty(
                    name="Writable Property",
                    datatype=DataType.INT,
                    settable=True,
                    # This function will be called when a message arrives. Topic/path
                    # matching depends on the communication module.
                    # Must be a string, object references do not cross process borders
                    # Don't forget to import it in the package '__init__.py' as it will
                    # be called by name as 'interface_pkg_template.message_callback'
                    callback="message_callback",
                ),
            },
        )

        return True
    else:
        log.error("Error loading config")
        return False


def start() -> None:
    """
    This function runs on the module's dedicated process when it is started. If your
    module needs to do things other than responding to messages you should start a thread
    here to handle that.
    """
    pass


def stop() -> None:
    """
    This function runs on the module's dedicated process when it is exiting. Threads
    should be stopped and open resources closed.
    """
    pass


def message_callback(message: SubscribeMessage) -> None:
    """
    Example message handler
    """
    if message.path.strip("/") == "my-node/my-writable-property/set":
        # do something with message
        pass
    else:
        log.debug("Received message on unregistered path: %s", message)
