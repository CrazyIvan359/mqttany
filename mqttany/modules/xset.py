"""
***********
XSET Module
***********

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

import json, subprocess
from collections import OrderedDict

import logger
from config import parse_config
from common import BusMessage, BusNode, BusProperty

CONF_KEY_DEFAULT_DISPLAY = "default display"
CONF_KEY_STARTUP_COMMANDS = "startup commands"

CONF_OPTIONS = OrderedDict(
    [
        (CONF_KEY_DEFAULT_DISPLAY, {"type": str, "default": None}),
        (CONF_KEY_STARTUP_COMMANDS, {"type": list}),
    ]
)

log = logger.get_logger("xset")
CONFIG = {}

publish_queue = None
subscribe_queue = None
nodes = {
    "xset": BusNode(
        name="XSET",
        type="Module",
        properties={
            "command": BusProperty(name="XSET Command", settable=True),
            "stdout": BusProperty(name="stdout"),
            "stderr": BusProperty(name="stderr"),
        },
    )
}


def load(config_raw={}):
    """
    Initializes the module
    """
    config_data = parse_config(config_raw, CONF_OPTIONS, log)
    del config_raw
    if config_data:
        log.debug("Config loaded")
        CONFIG.update(config_data)
        del config_data
        return True
    else:
        log.error("Error loading config")
        return False


def start():
    """
    Actions to be done in the subprocess before the loop starts
    """
    if CONFIG[CONF_KEY_STARTUP_COMMANDS]:
        log.info("Running startup commands")
        for command in CONFIG[CONF_KEY_STARTUP_COMMANDS]:
            run_xset(command)


def message_callback(message: BusMessage):
    """
    Callback for commands
    """
    if message.path.strip("/") == "xset/command/set":
        run_xset(message.content)
    else:
        log.debug("Received message on unregistered path: %s", message)


def run_xset(content):
    """
    Processes a command
    """
    try:
        content = json.loads(content)
    except ValueError:
        log.error("Received malformed JSON '%s'", content)
    else:
        command = content.get("command", None)

        if command:
            display = content.get("display", CONFIG[CONF_KEY_DEFAULT_DISPLAY])
            display = f"-display {display}" if display else ""
            # strip out commands that follow for security
            command = command.split(";")[0].split("&")[0].split("|")[0].strip()
            command = f"xset {display} {command}"
            log.debug("Running command '%s'", command)
            publish_queue.put_nowait(BusMessage(path="xset/command", content=command))
            result = subprocess.run(
                command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT
            )
            log.trace("Command '%s' result: %s", command, result.stdout)
            publish_queue.put_nowait(
                BusMessage(path="xset/stdout", content=result.stdout)
            )
            publish_queue.put_nowait(
                BusMessage(path="xset/stderr", content=result.stderr)
            )
        else:
            log.error("No command provided in message '%s'", content)
