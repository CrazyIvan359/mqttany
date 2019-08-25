"""
MQTTany

Config file loader
"""

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
                if options[section][key].get("type", None) == int:
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
        else:
            log.error("No section in config named '{section}'".format(section=section))
            valid = False

    return config if valid else False
