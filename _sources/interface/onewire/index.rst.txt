#######
OneWire
#######


The OneWire module provides access to Dallas/Maxim OneWire devices using the
``w1`` kernel module.

.. admonition:: Don't forget to install the requirements

    .. code-block:: shell

        pip3 install -r requirements/onewire.txt

.. attention::

    You need to have ``wire-1`` installed and configured for this module to work.
    This process will vary based on the board and operatering system you are using.


Permissions
===========

A ``udev`` rule file is provided to simplify access permissions for ``wire-1`` devices.

First add the ``wire`` group if it does not exist and add the user running
MQTTany to the ``wire`` group:

.. code-block:: shell

    sudo addgroup --system wire
    sudo usermod -aG wire mqttany

Then install the ``udev`` rule and reboot:

.. code-block:: shell

    sudo cp udev/98-w1.rules /etc/udev/rules.d/
    sudo reboot now


Devices
=======

See the device pages below for details on each one and to see any
additional options available for them.

.. toctree::
    :maxdepth: 1
    :glob:

    devices/*


Paths
=====

Device IDs are used as the nodes in this module, giving paths like
``{device-id}/{property-id}``. The device pages give more detail on the properties
they provide.

+------------------------------+-------------------------------------------------+
|             Path             |                   Description                   |
+==============================+=================================================+
| ``onewire/polling-interval`` | The polling interval will be published here     |
|                              | with ``retained = True`` when the device is     |
|                              | started.                                        |
+------------------------------+-------------------------------------------------+
| ``onewire/poll-all/set``     | Sending any message (even blank) here will      |
|                              | poll all configured devices to publish their    |
|                              | current states.                                 |
+------------------------------+-------------------------------------------------+
| ``{device-id}/address``      | Device address will be published here with      |
|                              | ``retained = True`` when the device is started. |
+------------------------------+-------------------------------------------------+


Configuration
=============

Optional settings are commented out, default values are shown.

.. code-block:: yaml

    onewire:

      #bus: 'w1'
      #polling interval: 0
      #bus scan: false

      device-id:
        address: ''
        #name: '{device_id}'

      batch-id:
        address: ['', '']
        #name: '{device_id}'
        #name: [  ]    # can also provide a matching list of names
        #first index: 0


Module Settings
---------------

+----------------------+-----------------------------------------------------+
|        Option        |                     Description                     |
+======================+=====================================================+
| ``bus``              | OneWire bus interface, currently only ``w1`` is     |
|                      | supported.                                          |
|                      |                                                     |
|                      | *Optional, default* ``w1``.                         |
+----------------------+-----------------------------------------------------+
| ``polling interval`` | Interval in seconds to publish all pin states.      |
|                      |                                                     |
|                      | *Optional, default* ``60``.                         |
+----------------------+-----------------------------------------------------+
| ``bus scan``         | Set to ``true`` to have the OneWire module scan the |
|                      | bus for any devices that are not defined in the     |
|                      | configuration file. Any devices found will be added |
|                      | with default options and their device topic set to  |
|                      | ``{address}``.                                      |
|                      |                                                     |
|                      | *Optional, default* ``false``.                      |
+----------------------+-----------------------------------------------------+


Single Device Definition
------------------------

Device configuration section names must be unique throughout the config file as they
are used as node IDs. Node IDs can only contain lowercase letters ``a-z``, numbers
``0-9``, and hyphens ``-``. The following settings are for single device definitions:

+-------------+----------------------------------------------------------------+
|   Option    |                          Description                           |
+=============+================================================================+
| ``address`` | The device's address, can be 7 or 8 bytes, can use             |
|             | ``w1`` style ``xx-xxxxxxxxxxxx``.                              |
|             |                                                                |
|             | **MUST BE IN SINGLE QUOTES** ``''``.                           |
+-------------+----------------------------------------------------------------+
| ``name``    | Friendly name for the device.                                  |
|             |                                                                |
|             | Substitutions:                                                 |
|             |                                                                |
|             | ``{device_id}`` will be replaced with the device definition    |
|             | section name.                                                  |
|             |                                                                |
|             | ``{device_type}`` will be replaced with the device type        |
|             | (ex. ``DS18B20``).                                             |
|             |                                                                |
|             | ``{address}`` will be replaced with the device's **FULL 8 BYTE |
|             | ADDRESS**.                                                     |
|             |                                                                |
|             | *Optional, default* ``{device_id}``.                           |
+-------------+----------------------------------------------------------------+


Multiple Device Definition
--------------------------

It is also possible to define settings for several devices at the same time.
Settings from single device definitions apply here also, except for those
shown below.

+-----------------+---------------------------------------------------------------+
|     Option      |                          Description                          |
+=================+===============================================================+
| ``address``     | Instead of a single address you can specify a list            |
|                 | of addresses.                                                 |
+-----------------+---------------------------------------------------------------+
| ``name``        | For multiple device definitions, name can be a single name or |
|                 | a list of names the same length as the list of addresses.     |
|                 |                                                               |
|                 | An additional substitution ``{index}`` is available when      |
|                 | a list of pin numbers is given. It corresponds to the pin's   |
|                 | index in the list plus *first index*.                         |
|                 |                                                               |
|                 | If a single name is given and the substitution ``{index}``    |
|                 | is not present, the name will have the index                  |
|                 | appended to the end like ``{name} {index}``.                  |
|                 |                                                               |
|                 | *Optional, default* ``{device_name}``.                        |
+-----------------+---------------------------------------------------------------+
| ``first index`` | Will be added to device's index in the list of                |
|                 | addresses when subsituting ``{index}`` in topics.             |
|                 |                                                               |
|                 | *Optional, default* ``0``.                                    |
+-----------------+---------------------------------------------------------------+
