"""
*************************
Interface Module Template
*************************

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

__all__ = []

from collections import OrderedDict

import logger
from config import parse_config
from common import DataType, BusMessage, BusNode, BusProperty
from modules import ModuleType

_module_type = ModuleType.INTERFACE

log = logger.get_logger()
CONFIG = {}

# If the module publishes messages it must have the `publish_queue` attribute. It will
# be assigned a queue that the module can use `put_nowait()` to put BusMessage objects
# in the queue to be transmitted by the communication modules.
publish_queue = None  # omit this if module is subscribe only

# This queue is put in the module's attributes whether it is defined here or not
# Do not use this name in your module and do not access this object
subscribe_queue = None

# Configuration keys, best to define them here so they can be changed easily
CONF_KEY_STRING = "string"
CONF_KEY_FIXED_TYPE = "fixed type"
CONF_KEY_SELECTION = "selection"
CONF_KEY_SUBSECTION = "sub section"

# Configuration layout for `parse_config`
# it should be an OrderedDict of `(key, {})`
CONF_OPTIONS = OrderedDict(
    [
        (  # an empty dict means any value is valid and option is required
            CONF_KEY_STRING,
            {},
        ),
        (  # fixed type options should provide a type to compare with
            CONF_KEY_FIXED_TYPE,
            {
                # if a `default` is given the option is assumed to be optional
                "type": int,
                "default": 200,
                "secret": True,  # This will cause the value to appear as *'s in the log
            },
        ),
        (  # subsections are also possible
            CONF_KEY_SUBSECTION,
            {
                # they must have type set to "section"
                "type": "section",
                # if a subsection is optional you must specify this, if this
                # is omitted the subsection is assumed to be required.
                "required": False,
                # conditions allows you to match a key at the same level (where CONF_KEY_SUBSECTION
                # is in this example) to a specific value. Must provide a list of tuples
                # where the first element is the key and the second is the value to match.
                # If any of the conditions match the option will be parsed. This can be
                # used ex. to have required sections only if an option is set to a specific
                # value. Can also be used on regular options.
                "conditions": [(CONF_KEY_FIXED_TYPE, 200)],
                CONF_KEY_SELECTION: {
                    # you can limit the possible values by providing a list or dict of
                    # possibilities. The config will be invalid if the value is not in
                    # "selection". If "selection" is a dict then the key's value will be
                    # returned, not the key.
                    "default": None,
                    "selection": {"option 1": 1, "option 2": 2},
                },
            },
        ),
        (  # regex pattern sections can also be used, their key must be "regex:{pattern}"
            # when using regex sections that may match other keys they should be last
            # and CONF_OPTIONS
            "regex:pattern",
            {"type": "section"},
        ),
    ]
)

# Interface modules must have a non-empty dict of Nodes that they provide. This can be
# partially or entirely populated at runtime in the `load` function.
nodes = {}


def load(config_raw) -> bool:
    """
    This function runs on the main process after the module is imported. It should parse
    and validate the configuration and do other basic setup of the module. Do not start
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


def message_callback(message: BusMessage) -> None:
    """
    Example message handler
    """
    if message.path.strip("/") == "my-node/my-writable-property/set":
        # do something with message
        pass
    else:
        log.debug("Received message on unregistered path: %s", message)
