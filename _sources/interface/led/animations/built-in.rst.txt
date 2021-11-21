########
Built-in
########

Several animations are included in the module to cover some basic operations
and serve as examples to get you started writing your own animations.

``on``
======

This simply turns all channels on every LED to maximum.

.. code-block:: python

    def anim_on(array: baseArray, cancel: threading.Event, **kwargs: t.Any) -> None:
        """
        Turns on the array
        """
        for i in range(array.count):
            array.setPixel(i, 0xFFFFFFFF)
        array.show()

Here we are just iterating over all the LEDs in the array and setting their
RGBW values to maximum. ``array.count`` tells us how many pixels are in the
array.


``off``
=======

This does the same the operation as ``on`` but sets all channels to ``0`` on
each pixel.


``set.brightness``
==================

This sets the brightness value for the array and shows how to use an argument.

.. code-block:: python

    def anim_set_brightness(
        array: baseArray, cancel: threading.Event, **kwargs: t.Any
    ) -> None:
        """
        Sets the array brightness
        """
        brightness = kwargs.get("brightness", None)

        if brightness is None:
            log.warn("Missing argument 'brightness'")
            return

        array.setBrightness(int(brightness))
        array.show()

As you can see above we are verifying that we got the ``brightness`` argument.
No argument checking is done by the LED module when calling animations, you
must do this in the animation function.

Example message to trigger this animation:

.. code-block:: python

    {
        "anim": "set.brightness",
        "brightness": 128
    }


``set.array``
=============

Allows you to set the entire array to a specific color. Repeat values other
than ``1`` have no effect. Color values can be provided as a list, a hex color,
or the individual components.

.. code-block:: python

    # As list of components
        "color": [red, green, blue, white]

    # As hex string (prefix '#' or '0x')
        "color": "#RRGGBB" # or "#WWRRGGBB"

    # As color components, all optional with default 0
        "red": 255,
        "green": 255,
        "blue": 255,
        "white": 255


``set.pixel``
=============

Allows you to set a pixel or range of pixels to the specified color. Color
arguments are the same as :ref:`interface/led/animations/built-in:\`\`set.array\`\``,
the ``pixel`` argument may be a single pixel index, a range as string, or a
list of indices, ranges, 2-tuples of *[start, count]*, or any combination
thereof.

.. code-block:: python

    # single index
        "pixel": 2

    # range string
        "pixel": "4-6"

    # list
        "pixel": [
            2,      # pixel 2
            "4-6",  # pixels 4, 5 and 6
            [10, 5] # pixels 10, 11, 12, 13, and 14
        ]


``fade.on``
===========

Same as ``on`` animation, but fades each pixel from its current color to fully
on. By providing the optional argument ``duration`` you can specify the length
of the animation in fractional seconds, the step for each channel and frame
length will be adjusted to fit the animation into the specified amount of time.
If ``duration`` is not provided the animation will run with a frame count equal
to the largest difference for any color channel in the entire array and the
minimum frame length.


``fade.off``
============

Same as ``off`` animation but fades each pixel from its current color to fully
off. See the `duration` argument in ``fade.on``.


``fade.brightness``
===================

This animation is the same as ``set.brightness`` but will fade the brightness
to the new value. See the ``duration`` argument in ``fade.on``.


``fade.array``
==============

This sets a new color for the entire array, the same as ``set.array``, but will
fade each pixel from its current color to the new one. See the ``duration``
argument in ``fade.on``.


``fade.pixel``
==============

This sets a new color for the specified pixels, the same as ``set.pixel``, but
will fade each pixel from its current color to the new one. See the
``duration`` argument in ``fade.on``.


``test.order``
==============

This animation is used to help determine the byte order for the colors used by
your LEDs. To use it, set your ``color order`` to ``'RGBW'`` and trigger this
animation via MQTT. It will turn on 10 pixels, if the color order is actually
RGBW you will see one red, two green, three blue, and four white. If this is
not what you see, then the number of pixels of each color tell you where in
the color order that color goes.

Ex. If you have 1 green, 2 red, and 3 blue pixels on, then the color order is
GRB.


``test.array``
==============

This is an animation used to test the entire array. It draws a rainbow across
the entire array and slides the colors along the array. It then quickly fades
on then off the white channel, if present.

.. code-block:: python

        # fade white up then down
        j, step = 1, 1
        array.brightness = 255
        while not cancel.is_set() and j > 0:
            for i in range(array.count):
                array.setPixelColorRGB(i, 0, 0, 0, j)
            array.show()
            time.sleep(0.01)
            j += step
            if j > 32: step = -1

        array.anims["off"](array, cancel)

In the above excerpt we can see that each step is checking if
``cancel.is_set()``. If you have an animation that is not a single step like
the ``on`` or ``off`` animations, you need to check for it being cancelled. If
``cancel.is_set()`` returns ``True``, your animation should stop what it is
doing and return.
