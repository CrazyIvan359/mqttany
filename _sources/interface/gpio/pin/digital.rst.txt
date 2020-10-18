###########
Digital Pin
###########


Digital pins are simple ON/OFF pins. They allow you to read an input or write
to an output.


Paths
=====

The state of a digital pin is available on the path ``gpio/{pin-id}`` and, for
output pins, commands can be sent to ``gpio/{pin-id}/set``. Values for pin
states are ``ON`` or ``OFF``.

+---------------------------+----------------------------------------------+
|           Path            |                 Description                  |
+===========================+==============================================+
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

The following additional options are added to the configuration. Optional
settings are commented out with default values shown.

.. code-block:: yaml

    gpio:

      #debounce: 50

      pin-id:
        #pin mode: 'input'
        #resistor: 'off'

        digital:
          #interrupt: 'none'
          #invert: false
          #initial state: OFF

      batch-id:
        #pin mode: 'input'
        #resistor: 'off'

        digital:
          #interrupt: 'none'
          #invert: false
          #initial state: OFF


Module Settings
---------------

+----------------------+-----------------------------------------------------+
|        Option        |                    Description                      |
+======================+=====================================================+
| ``debounce``         | Pin change interrupt debounce time in milliseconds. |
|                      |                                                     |
|                      | *Optional, default* ``50``.                         |
+----------------------+-----------------------------------------------------+


Single and Multiple Pin Definitions
-----------------------------------

Pin configuration section names must be unique as they are used as property IDs.
Property IDs can only contain lowercase letters ``a-z``, numbers ``0-9``, and
hyphens ``-``. The following settings apply to both single and multiple pin
definitions:

+-------------------+-------------------------------------------------------+
|      Option       |                      Description                      |
+===================+=======================================================+
| ``pin mode``      | Pin mode, can be ``input`` or ``output``.             |
|                   |                                                       |
|                   | *Optional, default* ``input``.                        |
+-------------------+-------------------------------------------------------+
| ``resistor``      | Pin pull resistor for inputs, can be ``pullup``,      |
|                   | ``pulldown`` (if supported), or ``off``.              |
|                   |                                                       |
|                   | *Optional, default* ``off``.                          |
+-------------------+-------------------------------------------------------+
| ``interrupt``     | Pin change interrupt, can be ``rising``, ``falling``, |
|                   | ``both``, or ``none``.                                |
|                   |                                                       |
|                   | *Optional, default* ``none``.                         |
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
