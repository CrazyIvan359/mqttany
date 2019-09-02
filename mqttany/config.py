"""
********************
Configuration Loader
********************

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

import os
from ast import literal_eval
import yaml, yamlloader

import logger
log = logger.get_logger()

all = [ "load_config", "parse_config" ]


def load_config(config_file):
    """
    Reads configuration file and returns as dict
    """
    config = {}

    # attempt to determine full path if config_file is only a filename
    if not os.path.isfile(config_file):
        log.debug("Attempting to resolve config file location")
        config_file = os.path.expanduser(config_file)
        if os.path.isfile(os.path.abspath(config_file)):
            config_file = os.path.abspath(config_file)
        elif os.path.isfile(os.path.join(os.getcwd(), config_file)):
            config_file = os.path.join(os.getcwd(), config_file)
        else:
            log.debug("Unable to resolve config file location")
            config_file = None

    if config_file:
        log.debug("Loading config")
        with open(config_file) as fh:
            config = yaml.load(fh, Loader=yamlloader.ordereddict.CSafeLoader)
    else:
        log.error("Config file does not exist: {path}".format(config_file))

    return config


def parse_config(data, options, log=log):
    """
    Parse and validate config and values
    """
    def parse_dict(data, options):
        valid = True
        config = {}
        for key in options:
            if not isinstance(options[key], dict):
                continue # 'required' option, skip

            if key not in data and options[key].get("type", None) == "section":
                if options[key].get("required", True):
                    log.error("No section in config named '{section}'".format(section=key))
                    valid = False
                #else:
                #    log.debug("No section in config named '{section}'".format(section=key))

            elif isinstance(data.get(key, None), dict):
                section_valid, config[key] = parse_dict(data[key], options[key])
                valid = valid and section_valid
            else:
                value = data.get(key, "**NO DATA**")
                if value == "**NO DATA**" and "default" not in options[key]:
                    log.error("Missing config option '{option}'".format(option=key))
                    valid = False
                elif value == "**NO DATA**":
                    value = options[key]["default"]
                    log.debug("Using default value '{value}' for config option '{option}'".format(
                            value=value, option=key))
                    config[key] = value
                else:
                    if "type" in options[key]:
                        if not isinstance(value, options[key]["type"]):
                            value = resolve_type(value)
                        if not isinstance(value, options[key]["type"]):
                            try:
                                value = options[key]["type"](value)
                            except: pass

                        if isinstance(value, options[key].get("type", type(value))):
                            log.debug("Got value '{value}' for config option '{option}'".format(
                                    value="*"*len(value) if "pass" in key.lower() else value, option=key))
                            config[key] = value
                        else:
                            log.error("Value '{value}' for config option '{option}' is not type '{type}'".format(
                                    value=value, option=key, type=options[key]["type"]))
                            valid = False

                    elif "selection" in options[key]:
                        if str(value).lower() in options[key]["selection"]:
                            log.debug("Got selection '{value}' for config option '{option}'".format(
                                    value=value, option=key))
                            if isinstance(options[key]["selection"], dict):
                                config[key] = options[key]["selection"][str(value).lower()]
                        else:
                            log.error("Value '{value}' for config option '{option}' is not one of [{selections}]".format(
                                    value=value, option=key, selections=[key for key in options[key]["selection"]]))
                            valid = False

                    else:
                        log.debug("Got value '{value}' for config option '{option}'".format(
                                value="*"*len(value) if "pass" in key.lower() else value, option=key))
                        config[key] = value


        return valid, config

    log.debug("Parsing config")

    valid, config = parse_dict(data, options)

    return config if valid else False


def resolve_type(value):
    """Attempts to resolve the type of ``value``.

    It will return ``value`` as the python type if possible, otherwise will
    return value as string.
    """
    value = str(value).strip()
    if value.lower() == "true":
        return True
    elif value.lower() == "false":
        return False
    elif value.lower() == "none":
        return None
    else:
        # attempt to parse
        try:
            return literal_eval(value)
        except ValueError:
            pass
        # unparseable, return as str
        return value
