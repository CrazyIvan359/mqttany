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

import configparser, os

all = [ "load_config" ]


def load_config(filename, options, log):
    """
    Reads config from file
    """
    valid = True
    config = {}

    log.debug("Loading config")
    raw_config = configparser.ConfigParser()
    raw_config.read([
        os.path.join("/etc/mqttany", filename),
        os.path.join(os.path.dirname(__file__), "config", filename)
    ])

    for section in options:
        if raw_config.has_section(section):
            config[section] = {}
            for key in options[section]:
                if not isinstance(options[section][key], dict):
                    continue
                elif options[section][key].get("type", None) == int:
                    value = raw_config.getint(section, key, fallback=None)
                elif options[section][key].get("type", None) == float:
                    value = raw_config.getfloat(section, key, fallback=None)
                elif options[section][key].get("type", None) == bool:
                    value = raw_config.getboolean(section, key, fallback=None)
                else:
                    value = raw_config.get(section, key, fallback=None)

                if value is None and "default" not in options[section][key]:
                    log.error("Missing config option '{option}' in section '{section}'".format(option=key, section=section))
                    valid = False
                elif value is None:
                    value = options[section][key]["default"]
                    log.debug("Using default value '{value}' for config option '{option}' in section '{section}'".format(
                            value=value, option=key, section=section))
                    config[section][key] = value
                else:
                    log.debug("Got value '{value}' for config option '{option}' in section '{section}'".format(
                            value="*"*len(value) if "pass" in key.lower() else value, option=key, section=section))
                    config[section][key] = value
        elif options[section].get("required", True):
            log.error("No section in config named '{section}'".format(section=section))
            valid = False
        else:
            log.debug("No section in config named '{section}'".format(section=section))

    return config if valid else False
