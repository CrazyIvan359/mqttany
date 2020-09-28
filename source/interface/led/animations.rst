##########
Animations
##########

.. toctree::
    :maxdepth: 1
    :hidden:

    animations/built-in
    animations/custom


Because of the real-time nature of controlling WS281x and similar LEDs, this
module does not provide direct control of them. Instead it controls them with
special Python functions called *animations* that are triggered by sending commands
to MQTTany. There are a handful of built-in animations, and you can write any
number of custom animations for your application.


Triggering
==========

Animations can be triggered by sending a command to the array on the path
``{array-id}/animation/set``. The command must be a JSON string containing
some parameters that can modify the behavoir of the animation. The animation
name will be published to ``{array-id}/animation`` when it is started, when
an animation ends a blank message is published.

Commands
--------

Commands must be JSON strings with the following elements:

.. code-block:: python

    {
        "anim": "ANIMATION_NAME",   # required
        "priority": 1,              # optional
        "repeat": 1,                # optional
        "arg": "value"              # any additional arguments for animation
    }

+--------------+------------------------------------------------------+
|  Parameter   |                     Description                      |
+==============+======================================================+
| ``anim``     | The name of the animation (*Ex.* ``"test.array"``)   |
|              | to trigger.                                          |
+--------------+------------------------------------------------------+
| ``priority`` | The priority with which to process the animation.    |
|              |                                                      |
|              | ``2`` run immediately, cancelling running animation  |
|              | and skipping all queued animations.                  |
|              |                                                      |
|              |                                                      |
|              | ``1`` add to queue and cancel only infinite-loop     |
|              | (``repeat: 0``) animations.                          |
|              |                                                      |
|              | ``0`` add to queue and wait until all animations     |
|              | ahead of this one have finished. Note that priority. |
|              | ``0`` animations sent to an array following an       |
|              | animation with ``repeat: 0`` will never be run.      |
|              |                                                      |
|              | *Optional, default* ``1``.                           |
+--------------+------------------------------------------------------+
| ``repeat``   | How many times to repeat the animation, can be any   |
|              | positive integer, ``0`` means repeat infinitely      |
|              | until cancelled.                                     |
|              |                                                      |
|              | *Optional, default* ``1``.                           |
+--------------+------------------------------------------------------+
| ``arg``      | Any other values will be passed to the animation     |
|              | function as keyword arguments when called.           |
+--------------+------------------------------------------------------+

