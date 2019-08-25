# MQTTany

MQTTany allows you to connect things to an MQTT Broker.
It is based on modules that each provide a certain functionality.
See the list of modules below, and their configuration files for details.

## Modules

### MQTT

The MQTT module wraps an MQTT client and connects to a broker.

It provides functions for publishing and subscribing to topics, as well as callbacks when messages arrive on a certain topic.

See the configuration file (`mqttany/config/mqtt.conf`) for details on configuring this module.
