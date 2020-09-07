"""
*****************************
Communication Module Template
*****************************

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
from common import BusMessage
from modules import ModuleType
from bus import get_property_from_path

_module_type = ModuleType.COMMUNICATION

log = logger.get_module_logger()
CONFIG = {}

# This queue is used to request that MQTTany exit. If a fatal error is encountered put
# a plain string on this queue using `put_nowait()` that will fit in this log entry
# such as `__name__`: "Received exit request from {}"
# An error that results in the module not being able to transmit messages, such as being
# unable to connect to the server, is considered fatal. If a module is unable to transmit
# it must request that MQTTany exit, otherwise it's transmit queue would overflow.
core_queue = None

# If the module can receive messages it must have the `receive_queue` attribute.
# A listener thread should be spawned in the `start` function and should use the `put_nowait()`
# method on the queue to put `BusMessage` objects in this queue
receive_queue = None  # omit this if module is transmit only

# These queues are put in the module's attributes whether they are defined here or not
# Do not use these names in your module and do not access these objects
transmit_queue = None
resend_queue = None

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
        return True
    else:
        log.error("Error loading config")
        return False


def start() -> None:
    """
    This function runs on the module's dedicated process when it is started. Connections
    should be started here and a listener thread should be created for receiving messages
    from the outside connection if required.
    """
    pass


def stop() -> None:
    """
    This function runs on the module's dedicated process when it is exiting. Connections
    should be closed and threads stopped.
    """
    pass


def transmit_callback(message: BusMessage) -> bool:
    """
    This function is required and must accept exactly one argument of type ``BusMessage``.
    It will be called when there is a message to be sent. If the sending succeeds it must
    return ``True``. If sending fails and it returns ``False``, MQTTany will queue the
    message and wait 500ms before attempting to send again.
    """
    return True


def transmit_ready() -> bool:
    """
    This function is required and must return ``True`` if the module is ready to transmit,
    or ``False`` othewise.
    """
    return True
