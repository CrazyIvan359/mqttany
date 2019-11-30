#######
OneWire
#######


The OneWire module provides access to Dallas/Maxim OneWire devices using the
``w1`` kernel module. Support for OWFS is planned

**You need to have wire-1 installed and configured for this module to work.**


.. admonition:: Don't forget to install the requirements

    .. code-block:: shell

        pip3 install -r requirements/onewire.txt


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
| ``{device_type}``    | will be replaced with the device type                |
|                      | (*Ex.* ``DS18B20``).                                 |
+----------------------+------------------------------------------------------+
| ``{address}``        | will be replaced with the device's                   |
|                      | **FULL 8 BYTE ADDRESS**                              |
|                      | (not the xx-xxxxxxxxxxxx format used by ``w1``).     |
+----------------------+------------------------------------------------------+
| ``{index}``          | will be replaced with the device's index in the list |
|                      | of addresses.                                        |
+----------------------+------------------------------------------------------+


Configuration
=============

Optional settings are commented out, default values are shown.

.. code-block:: yaml

    onewire:

      #bus: 'w1'
      #topic: '{module_name}'
      #topic get: 'poll'
      #polling interval: 0.0
      #bus scan: false

      single_device:
        address: ''
        #topic: '{device_name}'

      multiple_device:
        address: ['', '']
        #topic: '{device_name}'
        #topic: [  ]    # can also provide a matching list of topics
        #first index: 0


Module Settings
---------------

+----------------------+------------------------------------------------------+
| ``bus``              | OneWire bus interface, currently only ``w1`` is      |
|                      | supported. OWFS support is planned.                  |
|                      |                                                      |
|                      | *Optional, default* ``w1``.                          |
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
| ``bus scan``         | Set to ``true`` to have the OneWire module scan the  |
|                      | bus for any devices that are not defined in the      |
|                      | configuration file. Any devices found will be added  |
|                      | with default options and their device topic set to   |
|                      | ``{address}``.                                       |
|                      |                                                      |
|                      | *Optional, default* ``false``.                       |
+----------------------+------------------------------------------------------+


Single Device Definition
------------------------

Device configuration section names must be unique and are used only in logging
and for the `{device_name}` substitution in topics. The following settings are
for single device definitions:

+----------------------+------------------------------------------------------+
| ``address``          | The device's address, can be 7 or 8 bytes, can use   |
|                      | ``w1`` style ``xx-xxxxxxxxxxxx``.                    |
|                      |                                                      |
|                      | **MUST BE IN SINGLE QUOTES** ``''``.                 |
+----------------------+------------------------------------------------------+
| ``topic``            | Topic for the device.                                |
|                      |                                                      |
|                      | *Optional, default* ``{device_name}``.               |
+----------------------+------------------------------------------------------+


Multiple Device Definition
--------------------------

It is also possible to define settings for several devices at the same time.
Settings from single device definitions apply here also, except for those
shown below.

+----------------------+------------------------------------------------------+
| ``address``          | Instead of a single address you can specify a list   |
|                      | of addresses.                                        |
+----------------------+------------------------------------------------------+
| ``topic``            | For multiple device definitions, topic can be a      |
|                      | single topic or a list of topics the same length as  |
|                      | the list of addresses. An additional substitution    |
|                      | ``{index}`` is available when a list of addresses is |
|                      | given. It corresponds to the device's index in the   |
|                      | list plus *first index*.                             |
|                      |                                                      |
|                      | *Optional, default* ``{device_name}``.               |
+----------------------+------------------------------------------------------+
| ``first index``      | Will be added to device's index in the list of       |
|                      | addresses when subsituting ``{index}`` in topics.    |
|                      |                                                      |
|                      | *Optional, default* ``0``.                           |
+----------------------+------------------------------------------------------+
