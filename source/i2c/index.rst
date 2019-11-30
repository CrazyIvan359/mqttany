###
I2C
###


The I2C modules provides access to I2C/SMBus devices via the Linux kernel
driver.

**You must have the I2C Kernel module installed and configured for this**
**module to work**


.. admonition:: Don't forget to install the requirements

    .. code-block:: shell

        pip3 install -r requirements/i2c.txt


Devices
=======

See the device module pages below for details on each one and to see any
additional options available for them.

.. toctree::
    :maxdepth: 1
    :glob:

    devices/*


Substitutions
=============

The following additional substitutions are available for device topics:

+----------------------+------------------------------------------------------+
| ``{device_name}``    | will be replaced with the device definition section  |
|                      | name.                                                |
+----------------------+------------------------------------------------------+
| ``{device_topic}``   | will be replaced with the device's topic.            |
+----------------------+------------------------------------------------------+
| ``{address:02d}``    | will be replaced with the device's address as a      |
|                      | decimal number.                                      |
+----------------------+------------------------------------------------------+
| ``0x{address:02x}``  | will be replaced with the device's address as a      |
|                      | hexadecimal number.                                  |
+----------------------+------------------------------------------------------+


Configuration
=============

Optional settings are commented out, default values are shown.

.. code-block:: yaml

    i2c:

      #topic: '{module_name}'
      #topic get: 'poll'
      #polling interval: 0.0
      #bus scan: false

      single_device:
        device:
        #bus: 1
        address: 0x
        #topic: '{device_name}'


Module Settings
---------------

+----------------------+------------------------------------------------------+
| ``topic``            | Module topic to use for relative topics.             |
|                      |                                                      |
|                      | *Optional, default* ``{module_name}``.               |
+----------------------+------------------------------------------------------+
| ``topic get``        | Any message received on a device topic plus this     |
|                      | topic will result in the immediate publishing of the |
|                      | device's state. Default topics result in             |
|                      | ``{root_topic}/{module_topic}/poll`` for all devices |
|                      | and                                                  |
|                      | ``{root_topic}/{module_topic}/{device_name}/poll``   |
|                      | for individual devices.                              |
|                      |                                                      |
|                      | *Optional, default* ``poll``.                        |
+----------------------+------------------------------------------------------+
| ``polling interval`` | Interval in seconds to publish all pin states.       |
|                      |                                                      |
|                      | *Optional, default* ``0.0`` *(off)*.                 |
+----------------------+------------------------------------------------------+
| ``bus scan``         | Set to ``true`` to have the I2C module scan the bus  |
|                      | for any devices that are not defined in the          |
|                      | configuration file. A list of discovered devices     |
|                      | will be printed in the log.                          |
|                      |                                                      |
|                      | *Optional, default* ``false``.                       |
+----------------------+------------------------------------------------------+


Device Definition
-----------------

Device configuration section names must be unique and are used only in logging
and for the `{device_name}` substitution in topics. The following settings are
for device definitions:

+----------------------+------------------------------------------------------+
| ``device``           | Device model, see :ref:`i2c/index:devices` for       |
|                      | available options.                                   |
+----------------------+------------------------------------------------------+
| ``bus``              | I2C bus ID or full path to bus                       |
|                      |                                                      |
|                      | *Optional, default* ``1``.                           |
+----------------------+------------------------------------------------------+
| ``address``          | 7-bit hex address of the device (*Ex.* ``0x20`` or   |
|                      | ``32``)                                              |
+----------------------+------------------------------------------------------+
| ``topic``            | Topic for the device.                                |
|                      |                                                      |
|                      | *Optional, default* ``{device_name}``.               |
+----------------------+------------------------------------------------------+
