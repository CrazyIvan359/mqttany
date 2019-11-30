###
LED
###

.. toctree::
    :maxdepth: 1
    :hidden:

    animations


The LED module provides an interface to control WS2812 and similar LEDs
using custom :doc:`animations`.

.. admonition:: Don't forget to install the requirements

    .. code-block:: shell

        pip3 install -r requirements/led.txt

    You will also need to install requirements for the interface you are using.


Supported Interfaces
====================

.. toctree::
    :maxdepth: 1
    :glob:

    interfaces/*


Substitutions
=============

The following additional substitutions are available for array topics:

+----------------------+------------------------------------------------------+
| ``{array_name}``     | will be replaced with the array definition section   |
|                      | name.                                                |
+----------------------+------------------------------------------------------+


Configuration
=============

Optional settings are commented out with default values shown.

.. code-block:: yaml

    led:

      #topic: '{module_name}'
      #anim dir: []
      #anim startup: 'test.array'
      #anim fps: 60

      array_name:
        output: ''
        #topic: '{array_name}'
        count:
        #leds per pixel: 1
        #brightness: 255
        #color order: '{default}'


Module Settings
---------------

+----------------------+------------------------------------------------------+
| ``topic``            | Module topic to use for relative topics.             |
|                      |                                                      |
|                      | *Optional, default* ``{module_name}``.               |
+----------------------+------------------------------------------------------+
| ``anim dir``         | A directory or list of directories to look for       |
|                      | custom animations in. These will be searched for     |
|                      | animations as well as the default directory          |
|                      | ``/etc/mqttany/led-anim/``.                          |
|                      |                                                      |
|                      | *Optional*.                                          |
+----------------------+------------------------------------------------------+
| ``anim startup``     | The name of an animation to play when MQTTany loads. |
|                      | By default it will play the array test animation,    |
|                      | for production you will probably want to change this |
|                      | to ``off``.                                          |
|                      |                                                      |
|                      | *Optional, default* ``test.array``.                  |
+----------------------+------------------------------------------------------+
| ``anim fps``         | Frame rate used by the built-in animations. You may  |
|                      | need to reduce this value if you see log entries     |
|                      | indicating frames were skipped.                      |
|                      |                                                      |
|                      | This is made available to animations as the global   |
|                      | variable ``FRAME_MIN`` which is length of each frame |
|                      | in fractional seconds (*Ex.* 60fps means ``FRAME_MIN |
|                      | = 0.01667``).                                        |
|                      |                                                      |
|                      | *Optional, default* ``60``.                          |
+----------------------+------------------------------------------------------+


Array Definition
----------------

Array configuration section names must be unique and are used only in logging,
for the ``{array_name}`` substitution in topics, and when sending animation
commands via the module topic.

+----------------------+------------------------------------------------------+
| ``output``           | Output interface to send LED data with. Available    |
|                      | options are ``rpi`` or ``sacn``.                     |
+----------------------+------------------------------------------------------+
| ``topic``            | Topic for the array.                                 |
|                      |                                                      |
|                      | *Optional, default* ``{array_name}``.                |
+----------------------+------------------------------------------------------+
| ``count``            | Number of pixels in the array.                       |
+----------------------+------------------------------------------------------+
| ``leds per pixel``   | How many LED chips make up each 'pixel'. This allows |
|                      | you to have an array with multiple LEDs being        |
|                      | treated as a single pixel, *Ex.* a bulb with several |
|                      | LEDs that you want to address as a single pixel.     |
|                      |                                                      |
|                      | An example: You have 10 bulbs with 3 LEDs each, set  |
|                      | ``count: 10`` and ``leds per pixel: 3``. Animations  |
|                      | will see an array of 10 LEDs, but MQTTany will send  |
|                      | out 30 LEDs worth of data.                           |
|                      |                                                      |
|                      | *Optional, default* ``1``.                           |
+----------------------+------------------------------------------------------+
| ``brightness``       | Initial brightness for the array, can be in the      |
|                      | range 0-255.                                         |
|                      |                                                      |
|                      | *Optional, default* ``255``.                         |
+----------------------+------------------------------------------------------+
| ``color order``      | The order in which color information should be sent  |
|                      | to the LEDs. If you aren't sure what your color      |
|                      | order is and the default is incorrect, see the       |
|                      | :ref:`led/animations/built-in:\`\`test.order\`\``    |
|                      | animation for how to determine the correct order for |
|                      | your LEDs.                                           |
|                      |                                                      |
|                      | *Optional, default* ``{default}``.                   |
+----------------------+------------------------------------------------------+
