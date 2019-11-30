##########
Animations
##########

.. toctree::
    :maxdepth: 1
    :hidden:

    animations/built-in
    animations/custom


Because of the real-time nature of controlling WS281x and similar LEDs, this
module does not provide direct control of them over MQTT. Instead it controls
them with special Python functions called *animations* that are triggered via
MQTT. There are a handful of built-in animations, and you can write any number
of custom animations for your application.


Triggering
==========

Animations can be triggered by sending an MQTT message to any of 3 topics. The
message may be blank, depending on which topic you send it to, or contain some
parameters to modify the queuing and behavoir of the animation.

Message Content
---------------

If the message is not blank, it must be JSON data.

.. code-block:: python

    {
        "array": "ARRAY_NAME",      # required for messages to module topic
        "anim": "ANIMATION_NAME",   # required for messages to module or array topic
        "priority": 1,
        "repeat": 1,
        "arg": "value"              # any additional arguments for animation
    }

+----------------------+------------------------------------------------------+
| ``array``            | The name of the array to trigger the animation for.  |
|                      | Used only for messages to the module topic.          |
+----------------------+------------------------------------------------------+
| ``anim``             | The name of the animation (*Ex.* ``"test.array"``)   |
|                      | to trigger. Used for messages to the module topic or |
|                      | array topic.                                         |
+----------------------+------------------------------------------------------+
| ``priority``         | The priority with which to process the animation.    |
|                      |                                                      |
|                      | * ``2`` run immediately, cancelling running animation|
|                      |   and skipping all queued animations                 |
|                      | * ``1`` add to queue and cancel only infinite-loop   |
|                      |   (``repeat: 0``) animations                         |
|                      | * ``0`` add to queue and wait until all animations   |
|                      |   ahead of this one have finished. Note that priority|
|                      |   ``0`` animations sent to an array following an     |
|                      |   animation with ``repeat: 0`` will never be run.    |
|                      |                                                      |
|                      | *Optional, default* ``1``.                           |
+----------------------+------------------------------------------------------+
| ``repeat``           | How many times to repeat the animation, can be any   |
|                      | positive integer, ``0`` means repeat infinitely      |
|                      | until cancelled.                                     |
|                      |                                                      |
|                      | *Optional, default* ``1``.                           |
+----------------------+------------------------------------------------------+
| ``arg``              | Any other values will be passed to the animation     |
|                      | function when called.                                |
+----------------------+------------------------------------------------------+


Module Topic
------------

You can send a JSON message to the module topic to trigger an animation, it
must contain the `array` and `anim` fields.

.. code-block:: text

    topic: hostname/led


.. code-block:: python

    {
        "array": "my_array",
        "anim": "test.array",
        "repeat": 2
    }

Will trigger the ``test.array`` animation for the array ``my_array`` with
priority ``1`` and repeat twice.


Array Topic
-----------

You can send a JSON message to the array's topic, it must contain the ``anim``
field. Example:

.. code-block:: text

    topic: hostname/led/my_array

.. code-block:: python

    {
        "anim": "off",
        "priority": 2
    }

The above message will trigger the ``off`` animation for the array ``my_array``
and cancel any running or queued animations ahead of it.


Array + Animation Topic
-----------------------

You can also send a message to the array's topic plus the name of the
animation. This is the only time the message may be empty, if there are no
arguments and default options are desired. Example:

.. code-block:: text

    topic: hostname/led/my_array/test.order

.. code-block:: python

    {

    }

Will trigger the ``test.order`` animation for the array ``my_array`` with the
defaults priority ``1`` and repeat ``1``.
