# MQTTany

[![Latest Version](https://img.shields.io/github/v/tag/CrazyIvan359/mqttany?label=release)](https://github.com/CrazyIvan359/mqttany/releases)
[![Gitter](https://img.shields.io/gitter/room/mqttany/community)](https://gitter.im/mqttany/community)
[![License](https://img.shields.io/github/license/CrazyIvan359/mqttany)](https://github.com/CrazyIvan359/mqttany/blob/master/LICENSE)

MQTTany aims to make it easier to connect things to an MQTT broker. It is a
collection of modules that each provide support for connecting something.

Checkout the [Docs](https://github.com/CrazyIvan359/mqttany/wiki) to get
started using MQTTany or download the latest version from the
[Releases](https://github.com/CrazyIvan359/mqttany/releases) page.

## Modules

### GPIO

Allows you to control GPIO pins on single board computers.
Supported boards:
- Raspberry Pi - all up to 3B+ should work, but not all have been tested.

### MCP230xx

Provides access to MCP23017 and MCP23008 devices over I2C.
Supported boards:
- Raspberry Pi - any up to 3B+ with the 40-pin header should work, but not all
  have been tested.

### OneWire

Provides access to Dallas OneWire devices using the `w1` kernel module. OWFS
support is planned.
Supported devices:
- Temperature sensors - `DS18B20`, `DS18S20`, `DS1822`, `DS1825`, and `DS28EA00`.

<br>

**Note**

If you are using a Python version older than `3.5.4` you may see errors like
the one shown below. This is a Python bug that can be fixed by upgrading to
Python `3.5.4` or higher.

```none
Exception ignored in: <function WeakValueDictionary.__init__.<locals>.remove at 0x7fc874a876a8>
Traceback (most recent call last):
File "/usr/lib/python3.5/weakref.py", line 117, in remove
TypeError: 'NoneType' object is not callable
```
