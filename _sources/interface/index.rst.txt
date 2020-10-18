#################
Interface Modules
#################

.. toctree::
    :maxdepth: 2
    :hidden:

    gpio/index
    i2c/index
    onewire/index
    led/index
    xset/index


Interface modules provide access to hardware on or connected to the platform that
MQTTany is running on.

+----------------------+-----------------------------------------------------+
| :doc:`gpio/index`    | Allows you to control GPIO pins on single board     |
|                      | computers.                                          |
+----------------------+-----------------------------------------------------+
| :doc:`i2c/index`     | Provides access to devices over I2C using the Linux |
|                      | kernel drivers.                                     |
+----------------------+-----------------------------------------------------+
| :doc:`onewire/index` | Provides access to Dallas OneWire devices using the |
|                      | ``w1`` kernel module.                               |
+----------------------+-----------------------------------------------------+
| :doc:`led/index`     | Provides control of WS281x and similar LEDs through |
|                      | animation scripts.                                  |
+----------------------+-----------------------------------------------------+
| :doc:`xset/index`    | Allows ``xset`` commands to be executed to set      |
|                      | screensaver and display power options.              |
+----------------------+-----------------------------------------------------+
