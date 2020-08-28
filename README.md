# MQTTany

[![Latest Version](https://img.shields.io/github/v/tag/CrazyIvan359/mqttany?label=release)](https://github.com/CrazyIvan359/mqttany/releases)
[![Gitter](https://img.shields.io/gitter/room/mqttany/community)](https://gitter.im/mqttany/community)
[![License](https://img.shields.io/badge/license-MIT-green)](https://github.com/CrazyIvan359/mqttany/blob/master/LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

<br>

MQTTany aims to make it easier to connect things to an MQTT broker. It is a
collection of modules that each provide support for connecting something.

Checkout the [Docs](https://crazyivan359.github.io/mqttany/index.html) to get
started using MQTTany or download the latest version from the
[Releases](https://github.com/CrazyIvan359/mqttany/releases) page.

## Modules

### GPIO

Allows you to control GPIO pins on single board computers.
Supported boards:
- Raspberry Pi - all up to 3B+ should work, but not all have been tested.
- Odroid C1, C1+, C2, XU3, XU4, and N2. Not all have been tested.

### I2C

Provides access to I2C/SMBus devices using the I2C Kernel module.

### OneWire

Provides access to Dallas OneWire devices using the `w1` kernel module. OWFS
support is planned.
Supported devices:
- Temperature sensors - `DS18B20`, `DS18S20`, `DS1822`, `DS1825`, and `DS28EA00`.

### LED

Provides control of WS281x and similar LEDs through animation scripts.

Supported Interfaces:
- Raspberry Pi via SPI, PWM, or PCM depending on board.
- Streaming ACN / ESTA 1.31 unicast and multicast.

### XSET

Allows `xset` commands to be executed to set screensaver and display power
options. This can, for example, be used to wake the display when motion is
detected.

<br>

## Note

If you are using a Python version older than `3.5.4` you may see errors like
the one shown below. This is a Python bug that can be fixed by upgrading to
Python `3.5.4` or higher.

```none
Exception ignored in: <function WeakValueDictionary.__init__.<locals>.remove at 0x7fc874a876a8>
Traceback (most recent call last):
File "/usr/lib/python3.5/weakref.py", line 117, in remove
TypeError: 'NoneType' object is not callable
```
