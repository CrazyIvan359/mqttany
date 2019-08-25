# MQTTany

MQTTany allows you to connect things to an MQTT Broker.
It is based on modules that each provide a certain functionality.
See the list of modules below, and their configuration files for details.

<br>

## Launching

You must install all requirements first, this can be done with this command:

```sh
pip3 install -r requirements.txt
```

Starting MQTTany:

```sh
python3 mqttany.py
```

You can add `-v` option to enable debug logging

<br>

## Modules

### MQTT

The MQTT module wraps an MQTT client and connects to a broker.

It provides functions for publishing and subscribing to topics, as well as callbacks when messages arrive on a certain topic.

See the configuration file (`mqttany/config/mqtt.conf`) for details on configuring this module.

### GPIO

The GPIO module allows interfacing with single board computer I/O pins.

Currently only the Raspberry Pi 3 is supported.

See the configuration file (`mqttany/config/gpio.conf`) for details on configuring this module.
