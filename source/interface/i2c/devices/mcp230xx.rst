########
MCP230xx
########


This device class supports the MCP23008 and MCP23017 I/O expander chips.


Paths
=====

All pins configured in this module are available as properties of the device node.
The value of a pin is available on the path ``{device id}/{pin id}`` and, for pins that
accept them, commands can be sent to ``{device id}/{pin id}/set``. Values for pin states
are ``ON`` or ``OFF``.

+----------------------------------+-------------------------------------------------+
|               Path               |                   Description                   |
+==================================+=================================================+
| ``{device-id}/poll-all``         | Sending any message (even blank) here will      |
|                                  | poll all configured pins and publish their      |
|                                  | states to their respective topics.              |
+----------------------------------+-------------------------------------------------+
| ``{device-id}/pulse``            | If you need more precise timing, this allows    |
|                                  | you to specify a time and, optionally,          |
|                                  | a state to toggle a pin for. If another         |
|                                  | command is sent while a pin is being pulsed,    |
|                                  | the pulse will be cancelled. The message        |
|                                  | should be a JSON string with the following      |
|                                  | elements:                                       |
|                                  |                                                 |
|                                  | ``pin`` the id of the pin to pulse.             |
|                                  |                                                 |
|                                  | ``time`` time in milliseconds to set the        |
|                                  | pin's state for.                                |
|                                  |                                                 |
|                                  | ``state`` to set the pin to, if omitted the     |
|                                  | pin will be toggled.                            |
+----------------------------------+-------------------------------------------------+
| ``{device-id}/{pin-id}``         | Pin state will be published here as ``ON``      |
|                                  | or ``OFF``.                                     |
+----------------------------------+-------------------------------------------------+
| ``{device-id}/{pin-id}/set``     | Send ``ON`` or ``OFF`` here to set the          |
|                                  | state of a pin that is configured as an output  |
+----------------------------------+-------------------------------------------------+
| ``{device-id}/{pin-id}/pulse``   | See pulse above, ``pin`` element is not         |
|                                  | required in the JSON here.                      |
+----------------------------------+-------------------------------------------------+


Configuration
=============

The following additional options are added to the configuration. Optional
settings are commented out with default values shown.

.. code-block:: yaml

    i2c:

      device-id:
        device: ''

        mcp230xx:
          pin-id:
            pin:
            #name: '{pin_id}'
            #direction: 'input'
            #resistor: 'off'
            #invert: false
            #initial state: false
            #first index: 0

          batch-id:
            pin: [  ]
            #name: '{pin_id}'
            #name: [  ]    # can also provide a matching list of names
            #direction: 'input'
            #resistor: 'off'
            #invert: false
            #initial state: false
            #first index: 0


Module Settings
---------------

+------------+------------------------------------------------------+
|   Option   |                     Description                      |
+============+======================================================+
| ``device`` | Available options are ``MCP23008`` and ``MCP23017``. |
+------------+------------------------------------------------------+


Single Pin Definition
---------------------


Pin configuration section names must be unique as they are used as property IDs.
Property IDs can only contain lowercase letters ``a-z``, numbers ``0-9``, and
hyphens ``-``. The following settings are for single pin definitions:

+-------------------+-------------------------------------------------------+
|      Option       |                      Description                      |
+===================+=======================================================+
| ``pin``           | MCP230xx pin number.                                  |
+-------------------+-------------------------------------------------------+
| ``name``          | Friendly name for the pin.                            |
|                   |                                                       |
|                   | Substitutions:                                        |
|                   |                                                       |
|                   | ``{pin}`` will be replaced with the pin number.       |
|                   |                                                       |
|                   | ``{pin:02d}`` same as above, but will left pad        |
|                   | the pin number with 0's.                              |
|                   |                                                       |
|                   | ``{pin_id}`` will be replaced with the pin definition |
|                   | section name.                                         |
|                   |                                                       |
|                   | *Optional, default* ``{pin_id}``.                     |
+-------------------+-------------------------------------------------------+
| ``direction``     | Pin direction, can be ``input`` or ``output``.        |
|                   |                                                       |
|                   | *Optional, default* ``input``.                        |
+-------------------+-------------------------------------------------------+
| ``resistor``      | Pin pull resistor for inputs, can be ``pullup``       |
|                   | or ``off``.                                           |
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

It is also possible to define settings for several pins at the same time.
Settings from single pin definitions apply here also, except those shown below.

+-----------------+----------------------------------------------------------------+
| ``pin``         | Instead of a single pin number you can specify a list of pins. |
+-----------------+----------------------------------------------------------------+
| ``name``        | For multiple pin definitions, name can be a single name or     |
|                 | a list of names the same length as the list of pins.           |
|                 |                                                                |
|                 | An additional substitution ``{index}`` is available when       |
|                 | a list of pin numbers is given. It corresponds to the pin's    |
|                 | index in the list plus *first index*.                          |
|                 |                                                                |
|                 | If a single name is given and the substitution ``{index}``     |
|                 | is not present, the name will have the index                   |
|                 | appended to the end like ``{name} {index}``.                   |
|                 |                                                                |
|                 | *Optional, default* ``{pin_id}``.                              |
+-----------------+----------------------------------------------------------------+
| ``first index`` | Will be added to pin number's index in the list of             |
|                 | pins when subsituting ``{index}`` in topics. *Ex.*             |
|                 | to start numbering at 1, set this to 1.                        |
|                 |                                                                |
|                 | *Optional, default* ``0``.                                     |
+-----------------+----------------------------------------------------------------+
