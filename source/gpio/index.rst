####
GPIO
####


The GPIO module provides access to the GPIO pins of single board computers.
See below for a list of supported boards that this module can be used with.

.. admonition:: Don't forget to install the requirements

    .. code-block:: shell

        pip3 install -r requirements/gpio.txt

    You will also need to install requirements for the board you are using.


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

* :ref:`Odroid C1 <gpio/odroid:odroid c1/c1+>` *(untested)*
* :ref:`Odroid C1+ <gpio/odroid:odroid c1/c1+>` *(untested)*
* :ref:`gpio/odroid:odroid c2`
* :ref:`Odroid XU3 <gpio/odroid:odroid xu3/xu4>` *(untested)*
* :ref:`Odroid XU4 <gpio/odroid:odroid xu3/xu4>` *(untested)*
* :ref:`gpio/odroid:odroid n2` *(untested)*


Substitutions
=============

The following additional substitutions are available for pin topics:

+----------------+------------------------------------------------------------+
| ``{pin}``      |   will be replaced with the pin number                     |
+----------------+------------------------------------------------------------+
| ``{pin:02d}``  |   same as above, but will left pad the pin number with 0's |
+----------------+------------------------------------------------------------+
| ``{pin_name}`` |   will be replaced with the pin definition section name.   |
+----------------+------------------------------------------------------------+
| ``{index}``    |   will be replaced with the pin's index in the list of pin |
|                |   numbers, plus *first index*. For single pin definitions  |
|                |   this will be blank.                                      |
+----------------+------------------------------------------------------------+


Configuration
=============

Optional settings are commented out, default values are shown.

.. code-block:: yaml

    gpio:

      #mode: 'SOC'
      #topic: '{module_name}'
      #topic set: 'set'
      #topic get: 'poll'
      #topic pulse: 'pulse'
      #payload on: 'ON'
      #payload off: 'OFF'
      #polling interval: 0.0
      #debounce: 50

      single_pin:
        pin:
        #topic: '{pin}'
        #direction: 'input'
        #interrupt: 'none'
        #resistor: 'off'
        #invert: false
        #initial state: '{payload_off}'

      multiple_pins:
        pin: [  ]
        #topic: '{pin}'
        #topic: [  ]    # can also provide a matching list of topics
        #first index: 0
        #direction: 'input'
        #interrupt: 'none'
        #resistor: 'off'
        #invert: false
        #initial state: '{payload_off}'


Module Settings
---------------

+----------------------+------------------------------------------------------+
| ``mode``             | GPIO numbering scheme, can be ``SOC`` (BCM),         |
|                      | ``BOARD``, or ``WIRINGPI``. See the                  |
|                      | :ref:`gpio/index:supported boards` pages above for   |
|                      | available pins and their number in each mode.        |
|                      |                                                      |
|                      | *Optional, default* ``SOC``.                         |
+----------------------+------------------------------------------------------+
| ``topic``            | Module topic to use for relative topics.             |
|                      |                                                      |
|                      | *Optional, default* ``{module_name}``.               |
+----------------------+------------------------------------------------------+
| ``topic set``        | Commands to set pins configured as outputs should be |
|                      | sent to the pin topic plus this topic. Default       |
|                      | topics result in                                     |
|                      | ``{root_topic}/{module_topic}/{pin}/set``.           |
|                      |                                                      |
|                      | *Optional, default* ``set``.                         |
+----------------------+------------------------------------------------------+
| ``topic get``        | Any message received on a pin topic plus this topic  |
|                      | will result in the immediate publishing of the pin's |
|                      | state. Default topics result in                      |
|                      | ``{root_topic}/{module_topic}/poll`` for all pins and|
|                      | ``{root_topic}/{module_topic}/{pin}/poll`` for       |
|                      | individual pins.                                     |
|                      |                                                      |
|                      | *Optional, default* ``poll``.                        |
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
| ``polling interval`` | Interval in seconds to publish all pin states.       |
|                      |                                                      |
|                      | *Optional, default* ``0.0`` *(off)*.                 |
+----------------------+------------------------------------------------------+
| ``debounce``         | Pin change interrupt debounce time in milliseconds.  |
|                      |                                                      |
|                      | *Optional, default* ``50``.                          |
+----------------------+------------------------------------------------------+


Single Pin Definition
---------------------

Pin configuration section names must be unique and are used only in logging and
for the ``{pin_name}`` substitution in topics. The following settings are for
single GPIO pin definitions:

+----------------------+------------------------------------------------------+
| ``pin``              | GPIO pin number.                                     |
+----------------------+------------------------------------------------------+
| ``topic``            | Topic for the pin.                                   |
|                      |                                                      |
|                      | *Optional, default* ``{pin}``.                       |
+----------------------+------------------------------------------------------+
| ``direction``        | Pin direction, can be ``input`` or ``output``.       |
|                      |                                                      |
|                      | *Optional, default* ``input``.                       |
+----------------------+------------------------------------------------------+
| ``interrupt``        | Pin change interrupt, can be ``rising``, ``falling``,|
|                      | ``both``, or ``none``.                               |
|                      |                                                      |
|                      | *Optional, default* ``none``.                        |
+----------------------+------------------------------------------------------+
| ``resistor``         | Pin pull resistor for inputs, can be ``pullup``,     |
|                      | ``pulldown`` (if supported), or ``off``.             |
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

It is also possible to define settings for several GPIO pins at the same time.
Settings from single pin definitions apply here also, except those shown below.

+----------------------+------------------------------------------------------+
| ``pin``              | Instead of a single GPIO pin number you can specify  |
|                      | a list of pins.                                      |
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
