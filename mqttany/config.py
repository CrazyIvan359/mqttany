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

try:
    import yaml
except ImportError:
    raise ImportError("MQTTany requires 'pyyaml' to be installed, please see \
        the wiki for instructions on how to install requirements")

try:
    import yamlloader
except ImportError:
    raise ImportError("MQTTany requires 'yamlloader' to be installed, please see \
        the wiki for instructions on how to install requirements")

import os, re
from ast import literal_eval

import logger
from logger import log_traceback

all = [ "load_config", "parse_config" ]

log = logger.get_logger()


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
        log.debug("Loading config file")
        try:
            with open(config_file) as fh:
                config = yaml.load(fh, Loader=yamlloader.ordereddict.CSafeLoader)
        except:
            log.error("Config file contains errors")
            log_traceback(log, limit=0)
    else:
        log.error("Config file does not exist: {path}".format(path=config_file))

    return config


def parse_config(data, options, log=log):
    """
    Parse and validate config and values
    """
    def parse_dict(data, options):
        def process_option(name, value, option, config):
            if value == "**NO DATA**" and option.get("type", None) == "section":
                if option.get("required", True):
                    log.error("No section in config named '{section}'".format(section=name))
                    return False
                #else:
                #    log.debug("No section in config named '{section}'".format(section=name))

            elif isinstance(value, dict):
                section_valid, section_config = parse_dict(value, option)
                if not section_valid and option.get("required", True):
                    log.error("Required section '{section}' is not valid".format(section=name))
                    return False
                elif not section_valid:
                    log.warn("Optional section '{section}' is not valid, it will be ignored".format(section=name))
                else:
                    config[name] = section_config

            else:
                if value == "**NO DATA**" and "default" not in option:
                    log.error("Missing config option '{option}'".format(option=name))
                    return False
                elif value == "**NO DATA**":
                    value = option["default"]
                    log.trace("Using default value '{value}' for config option '{option}'".format(
                            value=value, option=name))
                    config[name] = value
                else:
                    if "type" in option:
                        if not isinstance(value, option["type"]):
                            value = resolve_type(value)
                        if not isinstance(value, option["type"]):
                            try:
                                value = option["type"](value)
                            except: pass

                        if isinstance(value, option.get("type", type(value))):
                            log.trace("Got value '{value}' for config option '{option}'".format(
                                    value="*"*len(value) if "pass" in name.lower() else value, option=name))
                            config[name] = value
                        else:
                            log.error("Value '{value}' for config option '{option}' is not type '{type}'".format(
                                    value=value, option=name, type=option["type"]))
                            return False

                    elif "selection" in option:
                        if str(value).lower() in option["selection"]:
                            log.trace("Got selection '{value}' for config option '{option}'".format(
                                    value=value, option=name))
                            if isinstance(option["selection"], dict):
                                config[name] = option["selection"][str(value).lower()]
                        else:
                            log.error("Value '{value}' for config option '{option}' is not one of [{selections}]".format(
                                    value=value, option=name, selections=[key for key in option["selection"]]))
                            return False

                    else:
                        log.trace("Got value '{value}' for config option '{option}'".format(
                                value="*"*len(value) if "pass" in name.lower() else value, option=name))
                        config[name] = value
            return True

        valid = True
        config = {}
        for key in options:
            if not isinstance(options[key], dict):
                continue # 'required' option, skip

            if str(key).split(":", 1)[0] == "regex":
                log.trace("Found regex '{key}' in options".format(key=str(key).split(":", 1)[-1]))
                for data_key in [data_key for data_key in data]:
                    if re.fullmatch(str(key).split(":", 1)[-1], str(data_key)):
                        log.trace("Config key '{data_key}' matched to options regex '{key}'".format(data_key=data_key, key=str(key).split(":", 1)[-1]))
                        valid = valid and process_option(data_key, data.pop(data_key, "**NO DATA**"), options[key], config)
            else:
                valid = valid and process_option(key, data.pop(key, "**NO DATA**"), options[key], config)

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
        # attempt to cast
        try:
            return int(value)
        except:
            pass
        try:
            return float(value)
        except:
            pass
        # attempt to parse
        try:
            return literal_eval(value)
        except ValueError:
            pass
        except SyntaxError: # happens with single topics starting with '/'
            pass
        # unparseable, return as str
        return value
