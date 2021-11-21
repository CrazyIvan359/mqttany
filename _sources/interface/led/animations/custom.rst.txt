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


File Header
===========

You will likely want to add the following to the top of each of your files to
get the best experience writing your own animations. This will provide type
hints and autocompletion while creating animations.

.. code-block:: python

    import typing as t

    if t.TYPE_CHECKING:
        import threading, sys

        sys.path.append("/opt/mqttany")
        from mqttany.modules.led.anim import parse_color, parse_pixel
        from mqttany.modules.led.array.base import baseArray
        from mqttany.modules.led.common import Color
        from mqttany.logger import mqttanyLogger

        log: mqttanyLogger
        FRAME_MS: float

If you did not install MQTTany in the default ``/opt/mqttany`` directory you
will need to modify the path in the above header or otherwise ensure that the
imports are available.


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

    def anim_blink(
        array,  # type: baseArray
        cancel,  # type: threading.Event
        **kwargs,  # type: t.Any
    ) -> None:

+--------------+----------------------------------------------------------------+
|  Parameter   |                          Description                           |
+==============+================================================================+
| ``array``    | This is the LED array object subclassed from                   |
|              | ``led.array.base.baseArray``. All operations to change the     |
|              | LEDs are done using this object. See                           |
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
``modules.led.array.base.baseArray``.

+----------------------------------------+------------------------------------------------------+
|           Method / Property            |                     Description                      |
+========================================+======================================================+
| ``show()``                             | Outputs the current state of LEDs in memory.         |
|                                        | This should be called when you are done setting LEDs |
|                                        | and want to display those changes on the physical    |
|                                        | array.                                               |
+----------------------------------------+------------------------------------------------------+
| ``setPixelColor(pixel, color: Color)`` | Sets the specified ``pixel`` value of the ``Color``  |
|                                        | instance passed.                                     |
+----------------------------------------+------------------------------------------------------+
| ``getPixelColor(pixel) -> Color``      | Returns a ``Color`` instance with ``r``, ``g``,      |
|                                        | ``b``, and ``w`` properties representing the pixel   |
|                                        | color.                                               |
+----------------------------------------+------------------------------------------------------+
| ``setPixelColorRGB                     | Sets the specified ``pixel`` to the provided         |
| (pixel, red, green, blue, white=0)``   | ``red``, ``green``, ``blue``, and ``white`` values.  |
+----------------------------------------+------------------------------------------------------+
| ``getPixelColorRGB(pixel) -> tuple``   | Returns a tuple of ``red``, ``green``, ``blue``,     |
|                                        | and ``white`` integers representing the pixel        |
|                                        | color.                                               |
+----------------------------------------+------------------------------------------------------+
| ``setPixel(pixel, color: int)``        | Sets the specified ``pixel`` to a 24-bit ``RRGGBB``  |
|                                        | or 32-bit ``WWRRGGBB`` value.                        |
+----------------------------------------+------------------------------------------------------+
| ``getPixel(pixel) -> int``             | Returns a 24-bit ``RRGGBB`` or 32-bit ``WWRRGGBB``   |
|                                        | value representing the pixel color.                  |
+----------------------------------------+------------------------------------------------------+
| ``setBrightness(brightness: int)``     | Sets the brightness for the array. Also available    |
|                                        | as the property ``brightness``.                      |
+----------------------------------------+------------------------------------------------------+
| ``getBrightness() -> int``             | Returns the current brightness for the array. Also   |
|                                        | available as the property ``brightness``.            |
+----------------------------------------+------------------------------------------------------+
| ``numPixels() -> int``                 | Returns the number of pixels in the array. Also      |
|                                        | available as the property ``count``.                 |
+----------------------------------------+------------------------------------------------------+
| ``numColors() -> int``                 | Returns the number of color channels (3 for RGB or   |
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
|                                      | It will be an instance of ``logger.mqttanyLogger``.            |
+--------------------------------------+----------------------------------------------------------------+
| ``FRAME_MIN``                        | The configuration value ``anim fps`` is used to calulate the   |
|                                      | duration of each frame in milliseconds and is made available   |
|                                      | as ``FRAME_MIN`` to help with the frame timing of animations.  |
|                                      | See the built in fade animations to see how you might use this |
|                                      | value.                                                         |
+--------------------------------------+----------------------------------------------------------------+
| .. code-block:: python               | The ``Color`` class is used by some of the ``baseArray``       |
|                                      | methods and the utility function ``parse_color``. It is also   |
|   class Color(t.NamedTuple):         | injected into each animation so you can make use of it as      |
|       r: int                         | well. It provides easy access to each of the color components  |
|       g: int                         | and can convert those components into a single integer         |
|       b: int                         | (``WWRRGGBB`` format). There is an alternate constructor to    |
|       w: int = 0                     | create a ``Color`` instance from a color stored as an integer  |
|                                      | (``fromInt``). There are also static methods to convert from   |
|       def asInt(self) -> int: ...    | components to single value and vice versa (``getIntFromRGB``   |
|                                      | and ``getRGBFromInt``).                                        |
|       @classmethod                   |                                                                |
|       def fromInt(                   |                                                                |
|           cls, color: int            |                                                                |
|       ) -> Color: ...                |                                                                |
|                                      |                                                                |
|       @staticmethod                  |                                                                |
|       def getIntFromRGB(             |                                                                |
|           r: int,                    |                                                                |
|           g: int,                    |                                                                |
|           b: int,                    |                                                                |
|           w: int = 0,                |                                                                |
|       ) -> int: ...                  |                                                                |
|                                      |                                                                |
|       @staticmethod                  |                                                                |
|       def getRGBFromInt(             |                                                                |
|           color: int,                |                                                                |
|       ) -> t.Tuple[                  |                                                                |
|           int, int, int, int         |                                                                |
|       ]: ...                         |                                                                |
|                                      |                                                                |
+--------------------------------------+----------------------------------------------------------------+
| .. code-block:: python               | This function can be used to get a ``Color`` instance from the |
|                                      | animation arguments ``color``, ``red``, ``green``, ``blue``,   |
|   parse_color(                       | and ``white`` as used in the                                   |
|       array,                         | :ref:`interface/led/animations/built-in:\`\`set.array\`\``     |
|       color = None,                  | animation. If ``pixel`` is provided, any component with a      |
|       r = -1,                        | value of ``-1`` (must provide at least 1 new value) will use   |
|       g = -1,                        | the current channel value from the specified pixel. It will    |
|       b = -1,                        | return ``None`` if it cannot determine a color from the values |
|       w = -1,                        | provided.                                                      |
|       pixel = None,                  |                                                                |
|   )                                  |                                                                |
|                                      |                                                                |
+--------------------------------------+----------------------------------------------------------------+
| .. code-block:: python               | This can be used to parse various pixel range arguments as     |
|                                      | used with the ``pixel`` argument for the                       |
|   parse_pixel(                       | :ref:`interface/led/animations/built-in:\`\`set.pixel\`\``     |
|       array,                         | animation. It will return a list of all pixel indices          |
|       p,                             | specified or an empty list if it is unable to parse the input. |
|   )                                  |                                                                |
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
