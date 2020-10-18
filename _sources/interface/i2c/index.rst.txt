###
I2C
###


The I2C module provides access to I2C/SMBus devices via the Linux kernel
driver.


.. admonition:: Don't forget to install the requirements

    .. code-block:: shell

        pip3 install -r requirements/i2c.txt

.. attention::

    You must have the I2C Kernel module installed and configured for this
    module to work. This process will vary based on the board and operatering
    system you are using.


Permissions
===========

A ``udev`` rule file is provided to simplify access permissions for I2C buses.

First add the ``i2c`` group if it does not exist and add the user running
MQTTany to the ``i2c`` group:

.. code-block:: shell

    sudo addgroup --system i2c
    sudo usermod -aG i2c mqttany

Then install the ``udev`` rule and reboot:

.. code-block:: shell

    sudo cp udev/98-i2c.rules /etc/udev/rules.d/
    sudo reboot now


Devices
=======

See the device pages below for details on each one and to see any additional
options available.

.. toctree::
    :maxdepth: 1
    :glob:

    devices/*


Paths
=====

Device IDs are used as the nodes in this module, giving paths like
``{device-id}/{property-id}``. The device pages give more detail on the properties
they provide.

+--------------------------+-------------------------------------------------+
|           Path           |                   Description                   |
+==========================+=================================================+
| ``i2c/polling-interval`` | The polling interval will be published here     |
|                          | with ``retained = True`` when the device is     |
|                          | started.                                        |
+--------------------------+-------------------------------------------------+
| ``i2c/poll-all/set``     | Sending any message (even blank) here will      |
|                          | poll all configured devices to publish their    |
|                          | current states.                                 |
+--------------------------+-------------------------------------------------+
| ``{device-id}/address``  | Device address will be published here with      |
|                          | ``retained = True`` when the device is started. |
+--------------------------+-------------------------------------------------+


Configuration
=============

Optional settings are commented out with default values shown.

.. code-block:: yaml

    i2c:

      #polling interval: 60

      device-id:
        #name: '{device_id}'
        device: ''
        #bus: 1
        address: 0x


Module Settings
---------------

+----------------------+---------------------------------------------------+
|        Option        |                    Description                    |
+======================+===================================================+
| ``polling interval`` | Interval in seconds to publish all device states. |
|                      |                                                   |
|                      | *Optional, default* ``60``.                       |
+----------------------+---------------------------------------------------+


Device Definition
-----------------

Device configuration section names must be unique throughout the config file as they
are used as node IDs. Node IDs can only contain lowercase letters ``a-z``, numbers
``0-9``, and hyphens ``-``. The following settings are for device definitions:

+-------------+---------------------------------------------------------------------+
|   Option    |                             Description                             |
+=============+=====================================================================+
| ``name``    | Friendly name for the device                                        |
|             |                                                                     |
|             | Substitutions:                                                      |
|             |                                                                     |
|             | ``{device_id}`` will be replaced with the device section name.      |
|             |                                                                     |
|             | ``{address:02d}`` will be replaced with the device's address as a   |
|             | decimal number.                                                     |
|             |                                                                     |
|             | ``0x{address:02x}`` will be replaced with the device's address as a |
|             | hexadecimal number.                                                 |
|             |                                                                     |
|             | *Optional, default* ``{device_id}``.                                |
+-------------+---------------------------------------------------------------------+
| ``device``  | Device model, see :ref:`interface/i2c/index:devices`                |
|             | for available options.                                              |
+-------------+---------------------------------------------------------------------+
| ``bus``     | I2C bus ID or full path to bus                                      |
|             |                                                                     |
|             | *Optional, default* ``1``.                                          |
+-------------+---------------------------------------------------------------------+
| ``address`` | 7-bit hex address of the device (*Ex.* ``0x20`` or                  |
|             | ``32``)                                                             |
+-------------+---------------------------------------------------------------------+
