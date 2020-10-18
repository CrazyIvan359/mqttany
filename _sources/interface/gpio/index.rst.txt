####
GPIO
####


The GPIO module provides access to the GPIO pins of single board computers.
See below for a list of supported boards that this module can be used with.


Permissions
===========

A ``udev`` rule file is provided to simplify access permissions for GPIO pins.

First add the ``gpio`` group if it does not exist, then add the user running
MQTTany to the ``gpio`` group:

.. code-block:: shell

    sudo addgroup --system gpio
    sudo usermod -aG gpio mqttany

Then install the ``udev`` rule and reboot:

.. code-block:: shell

    sudo cp udev/98-gpio.rules /etc/udev/rules.d/
    sudo reboot now


Paths
=====

All pins configured in this module are available as properties of the node ``gpio``.
The state of a pin is available on the path ``gpio/{pin-id}``.

+---------------------------+----------------------------------------------+
|           Path            |                 Description                  |
+===========================+==============================================+
| ``gpio/polling-interval`` | The polling interval will be published       |
|                           | here when the module starts, with            |
|                           | ``retained = True``.                         |
+---------------------------+----------------------------------------------+
| ``gpio/poll-all/set``     | Sending any message (even blank) here will   |
|                           | poll all configured pins and publish their   |
|                           | states to their respective topics.           |
+---------------------------+----------------------------------------------+
| ``gpio/{pin-id}``         | Pin state will be published here.            |
+---------------------------+----------------------------------------------+


Configuration
=============

Optional settings are commented out with default values shown.

.. code-block:: yaml

    gpio:

      #mode: 'SOC'
      #polling interval: 60

      pin-id:
        pin:
        #name: '{pin_id}'
        #pin mode: 'input'
        #resistor: 'off'

      batch-id:
        pin: [  ]
        #name: '{pin_id}'
        #name: [  ]    # can also provide a matching list of names
        #first index: 0
        #pin mode: 'input'
        #resistor: 'off'


Module Settings
---------------

+----------------------+----------------------------------------------------+
|        Option        |                    Description                     |
+======================+====================================================+
| ``mode``             | GPIO numbering scheme, can be ``SOC`` (BCM),       |
|                      | ``BOARD``, or ``WIRINGPI``. See the                |
|                      | :ref:`interface/gpio/index:supported boards` pages |
|                      | below for available pins and their number in each  |
|                      | mode.                                              |
|                      |                                                    |
|                      | *Optional, default* ``SOC``.                       |
+----------------------+----------------------------------------------------+
| ``polling interval`` | Interval in seconds to publish all pin states.     |
|                      |                                                    |
|                      | *Optional, default* ``60``.                        |
+----------------------+----------------------------------------------------+


Single Pin Definition
---------------------

Pin configuration section names must be unique as they are used as property IDs.
Property IDs can only contain lowercase letters ``a-z``, numbers ``0-9``, and
hyphens ``-``. The following settings are for single GPIO pin definitions:

+--------------+-------------------------------------------------------+
|    Option    |                      Description                      |
+==============+=======================================================+
| ``name``     | Friendly name for the pin.                            |
|              |                                                       |
|              | Substitutions:                                        |
|              |                                                       |
|              | ``{pin}`` will be replaced with the pin number        |
|              |                                                       |
|              | ``{pin:02d}`` same as above, but will left pad        |
|              | the pin number with 0's                               |
|              |                                                       |
|              | ``{pin_id}`` will be replaced with the pin definition |
|              | section name.                                         |
|              |                                                       |
|              | *Optional, default* ``{pin_id}``.                     |
+--------------+-------------------------------------------------------+
| ``pin``      | GPIO pin number.                                      |
+--------------+-------------------------------------------------------+
| ``pin mode`` | Pin mode, see available pins for options.             |
|              |                                                       |
|              | *Optional, default* ``input``.                        |
+--------------+-------------------------------------------------------+
| ``resistor`` | Pin pull resistor for inputs, can be ``pullup``,      |
|              | ``pulldown`` (if supported), or ``off``.              |
|              |                                                       |
|              | *Optional, default* ``off``.                          |
+--------------+-------------------------------------------------------+


Multiple Pin Definition
-----------------------

It is also possible to define settings for several GPIO pins at the same time.
Settings from single pin definitions apply here also, except those shown below.

+-----------------+-------------------------------------------------------------+
|     Option      |                         Description                         |
+=================+=============================================================+
| ``pin``         | Instead of a single GPIO pin number you can specify         |
|                 | a list of pins.                                             |
+-----------------+-------------------------------------------------------------+
| ``name``        | For multiple pin definitions, name can be a single name or  |
|                 | a list of names the same length as the list of pins.        |
|                 |                                                             |
|                 | An additional substitution ``{index}`` is available when    |
|                 | a list of pin numbers is given. It corresponds to the pin's |
|                 | index in the list plus *first index*.                       |
|                 |                                                             |
|                 | If a single name is given and the substitution ``{index}``  |
|                 | is not present, the name will have the index                |
|                 | appended to the end like ``{name} {index}``.                |
|                 |                                                             |
|                 | *Optional, default* ``{pin_id}``.                           |
+-----------------+-------------------------------------------------------------+
| ``first index`` | Will be added to pin number's index in the list of          |
|                 | pins when subsituting ``{index}`` in names. *Ex.*           |
|                 | to start numbering at 1, set this to 1.                     |
|                 |                                                             |
|                 | *Optional, default* ``0``.                                  |
+-----------------+-------------------------------------------------------------+


Supported Boards
================

.. toctree::
    :maxdepth: 1
    :hidden:

    board/raspi
    board/odroid
    board/orangepi

.. rubric:: :doc:`Raspberry Pi <board/raspi>`

* All up to 3B+ should work, but not all have been tested.

.. rubric:: :doc:`Odroid <board/odroid>`

* :ref:`Odroid C1 <interface/gpio/board/odroid:odroid c1/c1+>` *(untested)*
* :ref:`Odroid C1+ <interface/gpio/board/odroid:odroid c1/c1+>` *(untested)*
* :ref:`interface/gpio/board/odroid:odroid c2`
* :ref:`Odroid XU3 <interface/gpio/board/odroid:odroid xu3/xu4>` *(untested)*
* :ref:`Odroid XU4 <interface/gpio/board/odroid:odroid xu3/xu4>` *(untested)*
* :ref:`interface/gpio/board/odroid:odroid n2` *(untested)*

.. rubric:: :doc:`Orange Pi <board/orangepi>`

* :ref:`Orange Pi Zero <interface/gpio/board/orangepi:zero>`


Supported Pin Types
===================

.. toctree::
    :maxdepth: 1
    :hidden:

    pin/digital
    pin/counter

* :doc:`Digital I/O <pin/digital>`
* :doc:`Pulse Counter <pin/counter>`
