####
GPIO
####


The GPIO module provides access to the GPIO pins of single board computers.
See below for a list of supported boards that this module can be used with.

.. admonition:: Don't forget to install the requirements

    .. code-block:: shell

        pip3 install -r requirements/gpio.txt

    **You will also need to install requirements for the board you are using.**


Permissions
===========

A ``udev`` rule file is provided to simplify access permissions for GPIO pins.

First add the ``gpio`` group if it does not exist:

.. code-block:: shell

    sudo addgroup --system gpio

Then install the ``udev`` rule, add the user running MQTTany to the ``gpio``
group, and reboot:

.. code-block:: shell

    sudo cp udev/98-gpio.rules /etc/udev/rules.d/
    sudo usermod -aG gpio mqttany
    sudo reboot now


Supported Boards
================

.. toctree::
    :maxdepth: 1
    :hidden:

    raspi
    odroid

.. rubric:: :doc:`Raspberry Pi <raspi>`

* All up to 3B+ should work, but not all have been tested.

.. rubric:: :doc:`Odroid <odroid>`

* :ref:`Odroid C1 <interface/gpio/odroid:odroid c1/c1+>` *(untested)*
* :ref:`Odroid C1+ <interface/gpio/odroid:odroid c1/c1+>` *(untested)*
* :ref:`interface/gpio/odroid:odroid c2`
* :ref:`Odroid XU3 <interface/gpio/odroid:odroid xu3/xu4>` *(untested)*
* :ref:`Odroid XU4 <interface/gpio/odroid:odroid xu3/xu4>` *(untested)*
* :ref:`interface/gpio/odroid:odroid n2` *(untested)*


Paths
=====

All pins configured in this module are available as properties of the node ``gpio``.
The value of a pin is available on the path ``gpio/{pin-id}`` and, for pins that
accept them, commands can be sent to ``gpio/{pin-id}/set``. Values for pin states are
``ON`` or ``OFF``.

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
| ``gpio/pulse/set``        | If you need more precise timing, this allows |
|                           | you to specify a time and, optionally        |
|                           | a state, to toggle a pin for. If another     |
|                           | command is sent while a pin is being pulsed, |
|                           | the pulse will be cancelled. The message     |
|                           | should be a JSON string with the following   |
|                           | elements:                                    |
|                           |                                              |
|                           | ``pin`` the id of the pin to pulse.          |
|                           |                                              |
|                           | ``time`` time in milliseconds to set the     |
|                           | pin's state for.                             |
|                           |                                              |
|                           | ``state`` to set the pin to, if omitted the  |
|                           | pin will be toggled.                         |
+---------------------------+----------------------------------------------+
| ``gpio/{pin-id}``         | Pin state will be published here as ``ON``   |
|                           | or ``OFF``.                                  |
+---------------------------+----------------------------------------------+
| ``gpio/{pin-id}/set``     | Send ``ON`` or ``OFF`` here to set the       |
|                           | state of a pin that is configured as an      |
|                           | output.                                      |
+---------------------------+----------------------------------------------+
| ``gpio/{pin-id}/pulse``   | See pulse above, ``pin`` element is not      |
|                           | required in the JSON here.                   |
+---------------------------+----------------------------------------------+


Configuration
=============

Optional settings are commented out with default values shown.

.. code-block:: yaml

    gpio:

      #mode: 'SOC'
      #polling interval: 60
      #debounce: 50

      pin-id:
        pin:
        #name: '{pin_id}'
        #direction: 'input'
        #interrupt: 'none'
        #resistor: 'off'
        #invert: false
        #initial state: OFF

      batch-id:
        pin: [  ]
        #name: '{pin_id}'
        #name: [  ]    # can also provide a matching list of names
        #first index: 0
        #direction: 'input'
        #interrupt: 'none'
        #resistor: 'off'
        #invert: false
        #initial state: OFF


Module Settings
---------------

+----------------------+----------------------------------------------------+
|        Option        |                    Description                     |
+======================+====================================================+
| ``mode``             | GPIO numbering scheme, can be ``SOC`` (BCM),       |
|                      | ``BOARD``, or ``WIRINGPI``. See the                |
|                      | :ref:`interface/gpio/index:supported boards` pages |
|                      | above for available pins and their number in each  |
|                      | mode.                                              |
|                      |                                                    |
|                      | *Optional, default* ``SOC``.                       |
+----------------------+----------------------------------------------------+
| ``polling interval`` | Interval in seconds to publish all pin states.     |
|                      |                                                    |
|                      | *Optional, default* ``60``.                        |
+----------------------+----------------------------------------------------+
| ``debounce``         | Digital Pin change interrupt debounce time in      |
|                      | milliseconds.                                      |
|                      |                                                    |
|                      | *Optional, default* ``50``.                        |
+----------------------+----------------------------------------------------+


Single Pin Definition
---------------------

Pin configuration section names must be unique as they are used as property IDs.
Property IDs can only contain lowercase letters ``a-z``, numbers ``0-9``, and
hyphens ``-``. The following settings are for single GPIO pin definitions:

+-------------------+-------------------------------------------------------+
|      Option       |                      Description                      |
+===================+=======================================================+
| ``name``          | Friendly name for the pin.                            |
|                   |                                                       |
|                   | Substitutions:                                        |
|                   |                                                       |
|                   | ``{pin}`` will be replaced with the pin number        |
|                   |                                                       |
|                   | ``{pin:02d}`` same as above, but will left pad        |
|                   | the pin number with 0's                               |
|                   |                                                       |
|                   | ``{pin_id}`` will be replaced with the pin definition |
|                   | section name.                                         |
|                   |                                                       |
|                   | *Optional, default* ``{pin_id}``.                     |
+-------------------+-------------------------------------------------------+
| ``pin``           | GPIO pin number.                                      |
+-------------------+-------------------------------------------------------+
| ``direction``     | Pin direction, can be ``input`` or ``output``.        |
|                   |                                                       |
|                   | *Optional, default* ``input``.                        |
+-------------------+-------------------------------------------------------+
| ``interrupt``     | Pin change interrupt, can be ``rising``, ``falling``, |
|                   | ``both``, or ``none``.                                |
|                   |                                                       |
|                   | *Optional, default* ``none``.                         |
+-------------------+-------------------------------------------------------+
| ``resistor``      | Pin pull resistor for inputs, can be ``pullup``,      |
|                   | ``pulldown`` (if supported), or ``off``.              |
|                   |                                                       |
|                   | *Optional, default* ``off``.                          |
+-------------------+-------------------------------------------------------+
| ``invert``        | Logic invert flag, can be ``true`` or ``false``.      |
|                   | Setting to ``true`` means that logic *LOW = ON*.      |
|                   |                                                       |
|                   | *Optional, default* ``false``.                        |
+-------------------+-------------------------------------------------------+
| ``initial state`` | Initial state to set the pin to, must be one of       |
|                   | ``ON`` or ``OFF``.                                    |
|                   |                                                       |
|                   | *Optional, default* ``OFF``.                          |
+-------------------+-------------------------------------------------------+


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
