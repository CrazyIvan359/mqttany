######
Custom
######

Custom animations are just Python functions, but they allow you to do
limitless things with your LEDs.

File Location
=============

The default location for custom animation files is ``/etc/mqttany/led-anim/``,
but you can specify multiple other locations using the ``anim dir`` option in
the config file.


Function Naming
===============

Only functions with names starting with ``anim_`` will be imported as
animations. They will be added to the animation dictionary as
``filename.func_name``, ``func_name`` will have the ``anim_`` prefix removed.

*Ex.* An animation function called ``anim_blink`` in a file named
``example.py`` will be known as ``example.blink`` when triggering via MQTT or
from other animations.


Looping
=======

Animation functions should not loop to repeat the same action themselves, this
is done by the animation manager for the array based on the ``repeat``
parameter. Animation functions should **NEVER** run an infinite loop, always
use ``repeat: 0`` to accomplish this.


Function Signature
==================

Your animation function must have the following signature for it to work
reliably:

.. code-block:: python

    def anim_blink(array, cancel, **kwargs):

+--------------+----------------------------------------------------------------+
|  Parameter   |                          Description                           |
+==============+================================================================+
| ``array``    | This is the LED array object subclassed from                   |
|              | ``led.array.baseLED``. All operations to change the LEDs are   |
|              | done using this object. See                                    |
|              | :ref:`interface/led/animations/custom:\`\`array\`\` Object`    |
|              | for details.                                                   |
+--------------+----------------------------------------------------------------+
| ``cancel``   | This is a ``threading.Event`` object that is used to signal    |
|              | to a running animation that it should stop what it is doing    |
|              | and return as soon as possible.                                |
+--------------+----------------------------------------------------------------+
| ``**kwargs`` | You should always use ``**kwargs`` instead of specific keyword |
|              | arguments because no introspection is done by the LED module   |
|              | to see if all arguments have been provided.                    |
|              |                                                                |
|              | Arguments can be pulled from ``kwargs`` without errors if they |
|              | don't exist using ``get(key, default)``. You can provide       |
|              | defaults or later check if all required arguments have been    |
|              | provided.                                                      |
|              |                                                                |
|              | .. code-block:: python                                         |
|              |                                                                |
|              |     # sets 'value' to None if 'key' is not in 'kwargs'         |
|              |     value = kwargs.get("key", None)                            |
+--------------+----------------------------------------------------------------+


``array`` Object
================

The ``array`` object provides methods to get information about the array and
set LED colors. The ``array`` object received will be subclassed from
``modules.led.array.baseArray``.

+----------------------------------------+------------------------------------------------------+
|           Method / Property            |                     Description                      |
+========================================+======================================================+
| ``show()``                             | Outputs the current state of LEDs in memory.         |
|                                        | This should be called when you are done setting LEDs |
|                                        | and want to display those changes on the physical    |
|                                        | array.                                               |
+----------------------------------------+------------------------------------------------------+
| ``setPixelColorRGB``                   | Sets the specified ``pixel`` to the provided         |
| ``(pixel, red, green, blue, white=0)`` | ``red``, ``green``, ``blue``, and ``white`` values.  |
+----------------------------------------+------------------------------------------------------+
| ``getPixelColorRGB(pixel)``            | Returns an object with ``red``, ``green``, ``blue``, |
|                                        | and ``white`` properties representing the pixel      |
|                                        | color.                                               |
+----------------------------------------+------------------------------------------------------+
| ``setPixelColor(pixel, color)``        | Sets the specified ``pixel`` to a 24-bit ``RRGGBB``  |
|                                        | or 32-bit ``WWRRGGBB`` value.                        |
+----------------------------------------+------------------------------------------------------+
| ``getPixelColor(pixel)``               | Returns a 24-bit ``RRGGBB`` or 32-bit ``WWRRGGBB``   |
|                                        | value representing the pixel color.                  |
+----------------------------------------+------------------------------------------------------+
| ``setBrightness(brightness)``          | Sets the brightness for the array. Also available    |
|                                        | as the property ``brightness``.                      |
+----------------------------------------+------------------------------------------------------+
| ``getBrightness()``                    | Returns the current brightness for the array. Also   |
|                                        | available as the property ``brightness``.            |
+----------------------------------------+------------------------------------------------------+
| ``numPixels()``                        | Returns the number of pixels in the array. Also      |
|                                        | available as the property ``count``.                 |
+----------------------------------------+------------------------------------------------------+
| ``numColors()``                        | Returns the number of color channels (3 for RGB or   |
|                                        | 4 for RGBW). Also available as the property          |
|                                        | ``colors``.                                          |
+----------------------------------------+------------------------------------------------------+
| ``brightness``                         | Can be use to get or set the array brightness.       |
+----------------------------------------+------------------------------------------------------+
| ``count``                              | Returns the number of pixels in the array.           |
+----------------------------------------+------------------------------------------------------+
| ``colors``                             | Returns the number of color channels.                |
+----------------------------------------+------------------------------------------------------+
| ``anims``                              | Is a dictionary containing all known animations. You |
|                                        | can use this to run other animations by name from    |
|                                        | within your animation function. For example setting  |
|                                        | the array off after your animation finishes:         |
|                                        |                                                      |
|                                        | .. code-block:: python                               |
|                                        |                                                      |
|                                        |     array.anims["off"](array, cancel)                |
+----------------------------------------+------------------------------------------------------+


Globals
=======

Some useful values and functions are inserted into the globals for all
animations and can be used as if they had been defined or imported in your
animation file.

+--------------------------------------+----------------------------------------------------------------+
|               Property               |                          Description                           |
+======================================+================================================================+
| ``log``                              | This gives you a logger that logs to                           |
|                                      | ``mqttany.led.anim.{anim name}`` for outputting log messages.  |
+--------------------------------------+----------------------------------------------------------------+
| ``FRAME_MIN``                        | The configuration value ``anim fps`` is used to calulate the   |
|                                      | duration of each frame in milliseconds and is made available   |
|                                      | as ``FRAME_MS`` to help with the frame timing of animations.   |
|                                      | See the built in fade animations to see how you might use this |
|                                      | value.                                                         |
+--------------------------------------+----------------------------------------------------------------+
| ``parse_color(array, c=None, r=-1,`` | This function can be used to determine a 24/32-bit color from  |
| ``g=-1, b=-1, w=-1, pixel=None)``    | the animation arguments ``color``, ``red``, ``green``,         |
|                                      | ``blue``, ``white`` as used in the                             |
|                                      | :ref:`interface/led/animations/built-in:\`\`set.array\`\``     |
|                                      | animation. If ``pixel`` is provided, any component with a      |
|                                      | value of ``-1`` (must provide at least 1 new value) will use   |
|                                      | the current channel value from the specified pixel. It will    |
|                                      | return ``None`` if it cannot determine a color from the values |
|                                      | provided.                                                      |
+--------------------------------------+----------------------------------------------------------------+
| ``parse_pixel(array, p)``            | This can be used to parse various pixel range arguments as     |
|                                      | used with the ``pixel`` argument for the                       |
|                                      | :ref:`interface/led/animations/built-in:\`\`set.pixel\`\``     |
|                                      | animation. It will return a list of all pixel indices          |
|                                      | specified or an empty list if it is unable to parse the input. |
|                                      |                                                                |
|                                      | Pixels may be specified in any of the following ways:          |
|                                      |                                                                |
|                                      | .. code-block:: python                                         |
|                                      |                                                                |
|                                      |     # single index                                             |
|                                      |         "pixel": 2                                             |
|                                      |                                                                |
|                                      |     # range string                                             |
|                                      |         "pixel": "4-6"                                         |
|                                      |                                                                |
|                                      |     # list                                                     |
|                                      |         "pixel": [                                             |
|                                      |             2,      # pixel 2                                  |
|                                      |             "4-6",  # pixels 4, 5 and 6                        |
|                                      |             [10, 5] # pixels 10, 11, 12, 13, and 14            |
|                                      |         ]                                                      |
+--------------------------------------+----------------------------------------------------------------+
