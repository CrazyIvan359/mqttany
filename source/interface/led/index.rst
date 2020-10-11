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

    **You will also need to install requirements for the output method you are using.**


Supported Outputs
=================

.. toctree::
    :maxdepth: 1
    :glob:

    outputs/*


Paths
=====

Array IDs are used as the nodes in this module, giving paths like
``{array-id}/{property-id}``.

+-------------------------------+-----------------------------------------------------+
|             Path              |                     Description                     |
+===============================+=====================================================+
| ``{array-id}/count``          | The number of pixels in the array will be published |
|                               | here  with ``retained = True`` when the array is    |
|                               | started.                                            |
+-------------------------------+-----------------------------------------------------+
| ``{array-id}/leds-per-pixel`` | The number of LED chips per pixel will be published |
|                               | here  with ``retained = True`` when the array is    |
|                               | started.                                            |
+-------------------------------+-----------------------------------------------------+
| ``{array-id}/animation``      | The name of the currently running animation will be |
|                               | published here. An empty message will be published  |
|                               | if no animation is running.                         |
+-------------------------------+-----------------------------------------------------+
| ``{array-id}/animation/set``  | See :ref:`interface/led/animations:triggering` for  |
|                               | details on running animations.                      |
+-------------------------------+-----------------------------------------------------+


Configuration
=============

Optional settings are commented out with default values shown.

.. code-block:: yaml

    led:

      #anim dir: []
      #anim startup: 'test.array'
      #anim fps: 60

      array-id:
        output: ''
        #name: '{array_id}'
        count:
        #leds per pixel: 1
        #brightness: 255
        #color order: '{default}'


Module Settings
---------------

+------------------+------------------------------------------------------+
|      Option      |                     Description                      |
+==================+======================================================+
| ``anim dir``     | A directory or list of directories to look for       |
|                  | custom animations in. These will be searched for     |
|                  | animations as well as the default directory          |
|                  | ``/etc/mqttany/led-anim/``.                          |
|                  |                                                      |
|                  | *Optional*.                                          |
+------------------+------------------------------------------------------+
| ``anim startup`` | The name of an animation to play when MQTTany loads. |
|                  | By default it will play the array test animation,    |
|                  | for production you will probably want to change this |
|                  | to ``off``.                                          |
|                  |                                                      |
|                  | *Optional, default* ``test.array``.                  |
+------------------+------------------------------------------------------+
| ``anim fps``     | Frame rate used by the built-in animations. You may  |
|                  | need to reduce this value if you see log entries     |
|                  | indicating frames were skipped.                      |
|                  |                                                      |
|                  | This is made available to animations as the global   |
|                  | variable ``FRAME_MIN`` which is length of each frame |
|                  | in fractional seconds (*Ex.* 60fps means ``FRAME_MIN |
|                  | = 0.01667``).                                        |
|                  |                                                      |
|                  | *Optional, default* ``60``.                          |
+------------------+------------------------------------------------------+


Array Definition
----------------

Array configuration section names must be unique throughout the config file as they
are used as node IDs. Node IDs can only contain lowercase letters ``a-z``, numbers
``0-9``, and hyphens ``-``. The following settings are for array definitions:

+--------------------+-------------------------------------------------------------+
|       Option       |                         Description                         |
+====================+=============================================================+
| ``output``         | Output method to send LED data with, see                    |
|                    | :ref:`interface/led/index:supported outputs`                |
|                    | for available options.                                      |
+--------------------+-------------------------------------------------------------+
| ``name``           | Friendly name for the array.                                |
|                    |                                                             |
|                    | ``{array_id}`` will be replaced with the array definition   |
|                    | section name.                                               |
|                    |                                                             |
|                    | *Optional, default* ``{array_id}``.                         |
+--------------------+-------------------------------------------------------------+
| ``count``          | Number of pixels in the array.                              |
+--------------------+-------------------------------------------------------------+
| ``leds per pixel`` | How many LED chips make up each 'pixel'. This allows        |
|                    | you to have an array with multiple LEDs being               |
|                    | treated as a single pixel, *Ex.* a bulb with several        |
|                    | LEDs that you want to address as a single pixel.            |
|                    |                                                             |
|                    | An example: You have 10 bulbs with 3 LEDs each, set         |
|                    | ``count: 10`` and ``leds per pixel: 3``. Animations         |
|                    | will see an array of 10 LEDs, but MQTTany will send         |
|                    | out 30 LEDs worth of data.                                  |
|                    |                                                             |
|                    | *Optional, default* ``1``.                                  |
+--------------------+-------------------------------------------------------------+
| ``brightness``     | Initial brightness for the array, can be in the             |
|                    | range 0-255.                                                |
|                    |                                                             |
|                    | *Optional, default* ``255``.                                |
+--------------------+-------------------------------------------------------------+
| ``color order``    | The order in which color information should be sent         |
|                    | to the LEDs. If you aren't sure what your color             |
|                    | order is and the default is incorrect, see the              |
|                    | :ref:`interface/led/animations/built-in:\`\`test.order\`\`` |
|                    | animation for how to determine the correct order for        |
|                    | your LEDs.                                                  |
|                    |                                                             |
|                    | *Optional, default* ``{default}``.                          |
+--------------------+-------------------------------------------------------------+
