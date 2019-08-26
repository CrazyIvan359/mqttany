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

from ast import literal_eval
from yaml import safe_load
try: # libyaml is faster
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

import logger
log = logger.get_logger("config")

all = [ "load_config", "parse_config" ]


def load_config(conf_file="/etc/mqttany.yml"):
    """
    Reads configuration file and returns as dict
    """
    log.debug("Loading config")
    with open(conf_file) as fh:
        config = safe_load(fh)
    return config


def parse_config(data, options, log=log):
    """
    Parse and validate config and values
    """
    def parse_dict(data, options):
        global valid
        config = {}
        for key in options:
            if not isinstance(options[key], dict):
                continue # 'required' option, skip

            if key not in data and options[key].get("type", None) == "section":
                if options[key].get("required", True):
                    log.error("No section in config named '{section}'".format(section=key))
                    valid = False
                else:
                    log.debug("No section in config named '{section}'".format(section=key))

            elif isinstance(data.get(key, None), dict):
                config[key] = parse_dict(data[key], options[key])
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
                    if "type" in options[key] and not isinstance(value, options[key]["type"]):
                        value = resolve_type(value)

                    if isinstance(value, options[key].get("type", type(value))):
                        log.debug("Got value '{value}' for config option '{option}'".format(
                                value="*"*len(value) if "pass" in key.lower() else value, option=key))
                        config[key] = value
                    else:
                        log.error("Value '{value}' for config option '{option}' is not type '{type}'".format(
                                value=value, option=key, type=options[key]["type"]))
                        valid = False

        return config

    log.debug("Parsing config")

    valid = True
    config = parse_dict(data, options)

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
