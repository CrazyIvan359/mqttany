########
MCP230xx
########


This device module supports the MCP23008 and MCP23017 I/O expander chips.


Substitutions
=============

The following additional substitutions are available for pin topics only:

+----------------------+------------------------------------------------------+
| ``{pin}``            | will be replaced with the pin number.                |
+----------------------+------------------------------------------------------+
| ``{pin:02d}``        | is the same as above, but will left pad the pin      |
|                      | number with 0's.                                     |
+----------------------+------------------------------------------------------+
| ``{pin_name}``       | will be replaced with the pin definition section     |
|                      | name.                                                |
+----------------------+------------------------------------------------------+
| ``{index}``          | will be replaced with the pin's index in the list of |
|                      | pin numbers, plus *first index*. For single pin      |
|                      | definitions this will be blank.                      |
+----------------------+------------------------------------------------------+


Configuration
=============

The following additional options are added to the configuration. Optional
settings are commented out, default values are shown.

.. code-block:: yaml

    i2c:

      #topic set: 'set'
      #topic pulse: 'pulse'
      #payload on: 'ON'
      #payload off: 'OFF'

      example_device:
        mcp230xx:
          pin:
          #topic: '{pin}'
          #direction: 'input'
          #resistor: 'off'
          #invert: false
          #initial state: '{payload_off}'
          #first index: 0


Module Settings
---------------

The following additional options can be used in the module configuration
section:

+----------------------+------------------------------------------------------+
| ``topic set``        | Commands to set pins configured as outputs should be |
|                      | sent to the pin topic plus this topic. Default       |
|                      | topics result in                                     |
|                      | ``{root_topic}/{module_topic}/{device_topic}/{pin}/  |
|                      | set``.                                               |
|                      |                                                      |
|                      | *Optional, default* ``set``.                         |
+----------------------+------------------------------------------------------+
| ``topic pulse``      | Messages received on a pin topic plus this topic     |
|                      | allow you to *pulse* a pin for a specified period of |
|                      | time. Any messages to *pulse* or *set* for the pin   |
|                      | will cancel a running pulse timer.                   |
|                      |                                                      |
|                      | Message payload must be one of the following:        |
|                      |                                                      |
|                      | * An integer representing the time in milliseconds to|
|                      |   pulse the pin. The pin will be set to the opposite |
|                      |   of it's current state for the delay, then back to  |
|                      |   it's original state.                               |
|                      | * A comma separated time and state, to allow         |
|                      |   specifying the state. State should be either       |
|                      |   *payload on* or *payload off*. *Ex.* ``500, ON``   |
|                      | * A JSON string with the time and optionally the     |
|                      |   state. State should be either *payload on* or      |
|                      |   *payload off*.                                     |
|                      |   *Ex.* ``{"time": 500, "state": "ON"}``.            |
|                      |                                                      |
|                      | *Optional, default* ``pulse``.                       |
+----------------------+------------------------------------------------------+
| ``payload on``       | Message content to consider as *On* (case sensitive).|
|                      |                                                      |
|                      | *Optional, default* ``ON``.                          |
+----------------------+------------------------------------------------------+
| ``payload off``      | Message content to consider as *Off* (case           |
|                      | sensitive).                                          |
|                      |                                                      |
|                      | *Optional, default* ``OFF``.                         |
+----------------------+------------------------------------------------------+


Single Pin Definition
---------------------

Pin configuration section names must be unique and are used only in logging and
for the ``{pin_name}`` substitution in topics. The following settings are for
single pin definitions:

+----------------------+------------------------------------------------------+
| ``pin``              | pin number.                                          |
+----------------------+------------------------------------------------------+
| ``topic``            | Topic for the pin.                                   |
|                      |                                                      |
|                      | *Optional, default* ``{pin}``.                       |
+----------------------+------------------------------------------------------+
| ``direction``        | Pin direction, can be ``input`` or ``output``.       |
|                      |                                                      |
|                      | *Optional, default* ``input``.                       |
+----------------------+------------------------------------------------------+
| ``resistor``         | Pin pull resistor for inputs, can be ``pullup``      |
|                      | or ``off``.                                          |
|                      |                                                      |
|                      | *Optional, default* ``off``.                         |
+----------------------+------------------------------------------------------+
| ``invert``           | Logic invert flag, can be ``true`` or ``false``.     |
|                      | Setting to ``true`` means that logic *LOW = ON*.     |
|                      |                                                      |
|                      | *Optional, default* ``false``.                       |
+----------------------+------------------------------------------------------+
| ``initial state``    | Initial state to set the pin to, must be one of      |
|                      | *payload on* or *payload off*.                       |
|                      |                                                      |
|                      | *Optional, default* ``{payload_off}``.               |
+----------------------+------------------------------------------------------+


Multiple Pin Definition
-----------------------

It is also possible to define settings for several pins at the same time.
Settings from single pin definitions apply here also, except those shown below.

+----------------------+------------------------------------------------------+
| ``pin``              | Instead of a single pin number you can specify a     |
|                      | list of pins.                                        |
+----------------------+------------------------------------------------------+
| ``topic``            | For multiple pin definitions, topic can be a single  |
|                      | topic or a list of topics the same length as the     |
|                      | list of pins. An additional substitution ``{index}`` |
|                      | is available when a list of pin numbers is given. It |
|                      | corresponds to the pin's index in the list plus      |
|                      | *first index*.                                       |
|                      |                                                      |
|                      | *Optional, default* ``{pin}``.                       |
+----------------------+------------------------------------------------------+
| ``first index``      | Will be added to pin number's index in the list of   |
|                      | pins when subsituting ``{index}`` in topics. *Ex.*   |
|                      | to start numbering at 1, set this to 1.              |
|                      |                                                      |
|                      | *Optional, default* ``0``.                           |
+----------------------+------------------------------------------------------+
