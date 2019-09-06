# MQTTany

MQTTany allows you to connect things to an MQTT Broker.
It is based on modules that each provide a certain functionality.
See the list of modules below, and their configuration files for details.

**It is recommended to use the latest release, as code in the master branch may not be stable**

<br>

**Note**

If you are using Python version older than `3.5.4` you may see errors like the
one shown below. This is a Python bug that can be fixed by upgrading to Python
`3.5.4` or higher.

```none
Exception ignored in: <function WeakValueDictionary.__init__.<locals>.remove at 0x7fc874a876a8>
Traceback (most recent call last):
File "/usr/lib/python3.5/weakref.py", line 117, in remove
TypeError: 'NoneType' object is not callable
```

<br>

## Launching

You must install all requirements first, this can be done with this command:

```sh
pip3 install -r requirements.txt
```

Copy the configuration file and edit it:
```sh
sudo cp mqttany/config/mqttany.yml /etc/mqttany/mqttany.yml
sudo nano /etc/mqttany/mqttany.yml
```

Starting MQTTany:

```sh
python3 mqttany.py
```

<br>

## Modules

### MQTT

The MQTT module wraps an MQTT client and connects to a broker.

It provides functions for publishing and subscribing to topics, as well as callbacks when messages arrive on a certain topic.

See `mqtt` section in the configuration file `mqttany/config/mqttany.yml` for details on configuring this module.

### GPIO

The GPIO module allows interfacing with single board computer I/O pins.

Currently only the Raspberry Pi 3 is supported.

See `gpio` section in the configuration file `mqttany/config/mqttany.yml` for details on configuring this module.
