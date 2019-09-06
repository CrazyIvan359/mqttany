"""
**************
Example Module
**************

:Author: Your Name Here
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

import logger
log = logger.get_module_logger()
from logger import log_traceback
from config import parse_config

from modules.mqtt import resolve_topic, topic_matches_sub, publish, subscribe, add_message_callback

all = [  ]

# Configuration keys, best to define them once so they can be changed easily
CONF_KEY_TOPIC = "topic"
CONF_KEY_STRING = "string"
CONF_KEY_FIXED_TYPE = "fixed type"
CONF_KEY_SELECTION = "selection"
CONF_KEY_SUBSECTION = "sub section"

# Configuration layout for `parse_config`
# it should be a dict of `key: {}`
CONF_OPTIONS = {
        # all modules should use this default for their topic
    CONF_KEY_TOPIC: {"default": "{module_name}"}, # if a `default` is given the option is assumed to be optional
    CONF_KEY_STRING: {}, # an empty dict means any value is valid and option is required
    CONF_KEY_FIXED_TYPE: {"type": int, "default": 200}, # fixed type options should provide a type to compare with
    CONF_KEY_SUBSECTION: { # subsections are also possible
        "type": "section", # they must have type set to "section"
        "required": False, # if a subsection is optional you must specify, if this is omitted the subsection is assumed to be required
            # you can limit the possible values by providing a list or dict of possibilities.
            # the config will be invalid if the value is not in "selection".
            # if "selection" is a dict then the key's value will be returned, not the key.
        CONF_KEY_SELECTION: {"default": None, "selection": {"option 1": 1, "option 2": 2}}
    }
}

# Module name, this should be included in all modules and used when the module name is needed
TEXT_NAME = __name__.split(".")[-1]

# Filled with configuration by `init`
config = {}
# All modules must have a `queue`, this will be set by the module loader
queue = None


def init(config_data={}):
    """
    Initializes the module.

    Generally this will just parse the configuration data and do some
    validation of it. No MQTT subscriptions should be made here as it is not
    guaranteed that the MQTT module will be initialized yet, they should be
    done in ``pre_loop()``. Any long running init tasks should also be done in
    ``pre_loop()``. Do not start any timers in this function, they must be done
    in ``pre_loop()`` so that they are run in the module's subprocess.
    """
    raw_config = parse_config(config_data, CONF_OPTIONS, log)
    if raw_config:
        log.debug("Config loaded")
        config.update(raw_config)
        return True
    else:
        log.error("Error loading config")
        return False

def pre_loop():
    """
    Actions to be done in the subprocess before the loop starts.

    This function will be called within the module's subprocess just before
    the loop starts. Longer running init or setup tasks should be done here.
    This is also the recommended place to do MQTT subscriptions.
    """
    log.debug("Adding MQTT subscription to poll topic")
    subscribe(
            "topic",
            callback=message_callback,
            subtopics=["{module_topic}"],
            substitutions={
                "module_topic": config[CONF_KEY_TOPIC], # module topic, all modules should have this option
                "module_name": TEXT_NAME,
            }
        )


def post_loop():
    """
    Actions to be done in the subprocess after the loop is exited.

    This function will be called within the module's subprocess when the loop
    is exited, usually because MQTTany is exiting. Any cleanup actions should
    be done here.
    """
    pass


def message_callback(client, userdata, message):
    """
    Example MQTT message callback function.

    Any functions given to the MQTT module as a callback will be run by the
    MQTT module's process, therefore they must not take any action in this
    module other than adding a message to the queue.

    Messages put in the queue must be a *dict* containing the name of a
    function in this module to call and optionally positional and keyword
    arguments:

    .. code-block:: python

        {
            "func": "function_name",    # must be a string
            "args": [],                 # optional
            "kwargs": {}                # optional
        }

    .. note::

        The ``message.payload`` is of the type ``bytes`` which cannot be cast
        to a string. Use ``s = message.payload.decode("utf-8")`` to get a
        string from ``bytes``.
    """
    queue.put_notwait({
        "func": "function_name",
        "args": [],
        "kwargs": {
            "topic": message.topic,
            "payload": message.payload.decode("utf-8")
        }
    })


def dangerous_method():
    """
    When doing things that might cause a crash you can wrap them in a
    try/except and use ``log_traceback`` if something goes wrong. Each modules'
    subprocess will call the functions in the queue like this, but if you
    catch in the module you can potentially provide clearer logs about what
    went wrong.
    """
    try:
        assert False
    except:
        log.error("Something went terribly wrong!")
        log_traceback(log)
