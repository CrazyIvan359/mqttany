#####################
MQTTany Documentation
#####################

.. toctree::
    :maxdepth: 2
    :caption: MQTTany
    :name: mastertoc
    :hidden:

    install
    launch
    Releases <https://github.com/CrazyIvan359/mqttany/releases>
    Change Log <https://github.com/CrazyIvan359/mqttany/blob/dev/CHANGELOG.md>

    MQTT Module <mqtt/index>
    GPIO Module <gpio/index>
    I2C Module <i2c/index>
    OneWire Module <onewire/index>
    LED Module <led/index>


MQTTany aims to make it easier to connect things to an MQTT broker. It is a
collection of modules that each provide support for connecting something.

Get started on the :doc:`install` page or download the latest
`Release <https://github.com/CrazyIvan359/mqttany/releases>`_.

Modules
=======

+----------------------+------------------------------------------------------+
| :doc:`mqtt/index`    | Connects to a broker for control and output.         |
+----------------------+------------------------------------------------------+
| :doc:`gpio/index`    | Allows you to control GPIO pins on single board      |
|                      | computers.                                           |
+----------------------+------------------------------------------------------+
| :doc:`i2c/index`     | Provides access to devices over I2C using the Linux  |
|                      | kernel drivers.                                      |
+----------------------+------------------------------------------------------+
| :doc:`onewire/index` | Provides access to Dallas OneWire devices using the  |
|                      | ``w1`` kernel module. OWFS support is planned.       |
+----------------------+------------------------------------------------------+
| :doc:`led/index`     | Provides control of WS281x and similar LEDs through  |
|                      | animation scripts.                                   |
+----------------------+------------------------------------------------------+

.. note::

    If you are using a Python version older than ``3.5.4`` you may see errors
    like the one shown below. This is a Python bug that can be fixed by
    upgrading to Python ``3.5.4`` or higher.

    .. code-block:: text

        Exception ignored in: <function WeakValueDictionary.__init__.<locals>.remove at 0x7fc874a876a8>
        Traceback (most recent call last):
        File "/usr/lib/python3.5/weakref.py", line 117, in remove
        TypeError: 'NoneType' object is not callable
