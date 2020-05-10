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

import json, subprocess

import logger
from config import parse_config
from modules.mqtt import subscribe, publish

__all__ = [ "init", "pre_loop", "post_loop", "queue" ]

CONF_KEY_TOPIC = "topic"
CONF_KEY_DEFAULT_DISPLAY = "default display"
CONF_KEY_STARTUP_COMMANDS = "startup commands"

CONF_OPTIONS = {
    CONF_KEY_TOPIC: {"type": str, "default": "{module_name}"},
    CONF_KEY_DEFAULT_DISPLAY: {"type": str, "default": None},
    CONF_KEY_STARTUP_COMMANDS: {"type": list}
}

TEXT_NAME = __name__.split(".")[-1] # gives xset

log = logger.get_module_logger()
queue = None
config = {}


def init(config_data={}):
    """
    Initializes the module
    """
    raw_config = parse_config(config_data, CONF_OPTIONS, log)
    del config_data
    if raw_config:
        log.debug("Config loaded")
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
    if config[CONF_KEY_STARTUP_COMMANDS]:
        log.info("Running startup commands")
        for cmd in config[CONF_KEY_STARTUP_COMMANDS]:
            _command(cmd)

    subscribe(
        config[CONF_KEY_TOPIC],
        callback=callback_command,
        subtopics=["{module_topic}"],
        substitutions={
            "module_topic": config[CONF_KEY_TOPIC],
            "module_name": TEXT_NAME,
        }
    )


def post_loop():
    """
    Actions to be done in the subprocess after the loop is exited
    """
    pass


def callback_command(client, userdata, message):
    """
    Callback for commands
    """
    queue.put_nowait({
        "func": "_command",
        "args": [message.payload.decode("utf-8")]
    })


def _command(payload):
    """
    Processes a command string
    """
    # JSON payload
    if "{" in payload:
        try:
            payload = json.loads(payload)
        except ValueError:
            log.error("Received malformed JSON payload '{payload}'".format(payload=payload))
            return
        else:
            display = payload.get("display", config[CONF_KEY_DEFAULT_DISPLAY])
            command = payload.get("command", None)

    # List payload "display, command"
    elif len(payload.split(",")) > 1:
        if len(payload.split(",")) != 2:
            log.error("Received unrecognized payload '{payload}'".format(payload=payload))
            return
        display, command = payload.split(",", 2)

    # Command only payload
    else:
        display = config[CONF_KEY_DEFAULT_DISPLAY]
        command = payload

    if command:
        # strip out commands that follow for security
        command = command.split(";")[0].split("&")[0].split("|")[0].strip()
        command = "xset{display} {command}" \
                  .format(display="" if display is None else " -display {}".format(display),
                          command=command)
        log.debug("Running command '{command}'".format(command=command))
        result = subprocess.run(command.split(),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        log.trace("Command '{command}' result: {result}"
                  .format(command=command,
                          result=result.stdout))
        publish("{}/result".format(config[CONF_KEY_TOPIC]),
                result.stdout,
                subtopics=["{module_topic}"],
                substitutions={
                    "module_topic": config[CONF_KEY_TOPIC],
                    "module_name": TEXT_NAME,
                })
    else:
        log.error("No command provided in payload '{payload}'".format(payload=payload))
