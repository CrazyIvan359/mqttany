###########
Counter Pin
###########


Counter pins allow you to count pulses in various ways. You can simply count
the number of pulses in a given period, apply a function to the pulses, or
output the raw intervals. There is the option to scale the results up if you
are using a clock divider on the input. You can also specify the time unit to
use when returning intervals.

.. note::

    Counter pins **do not** publish their initial states or when the polling
    interval timer fires. They publish only when the ``interval`` timer fires
    due to the precise timing nature of pulse counting.


Paths
=====

The report of a counter pin is available on the path ``gpio/{pin-id}``.

+-------------------+----------------------------------------------+
|       Path        |                 Description                  |
+===================+==============================================+
| ``gpio/{pin-id}`` | Counter event report will be published here, |
|                   | see the Functions section for more details.  |
+-------------------+----------------------------------------------+


Configuration
=============

The following additional options are added to the configuration. Optional
settings are commented out with default values shown.

.. code-block:: yaml

    gpio:

      #debounce: 50

      pin-id:
        #pin mode: 'counter'
        #resistor: 'off'

        counter:
          #interval: 60
          #interrupt: 'rising'
          #function: 'count'
          #unit: 'ms'
          #divider: 1

      batch-id:
        #pin mode: 'counter'
        #resistor: 'off'

        counter:
          #interval: 60
          #interrupt: 'rising'
          #function: 'count'
          #unit: 'ms'
          #divider: 1


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

+---------------+---------------------------------------------------------------+
|    Option     |                          Description                          |
+===============+===============================================================+
| ``pin mode``  | Pin mode, must be ``counter``.                                |
+---------------+---------------------------------------------------------------+
| ``resistor``  | Pin pull resistor, can be ``pullup``, ``pulldown``            |
|               | (if supported), or ``off``.                                   |
|               |                                                               |
|               | *Optional, default* ``off``.                                  |
+---------------+---------------------------------------------------------------+
| ``interval``  | Pin report interval in whole seconds. Events will be cached   |
|               | during this period and a report will be published at the end. |
|               |                                                               |
|               | *Optional, default* ``60``.                                   |
+---------------+---------------------------------------------------------------+
| ``interrupt`` | Pin change interrupt, can be ``rising``, ``falling``,         |
|               | or ``both``.                                                  |
|               |                                                               |
|               | *Optional, default* ``rising``.                               |
+---------------+---------------------------------------------------------------+
| ``function``  | Counter report function, see below for details. Available     |
|               | options are ``raw``, ``count``, ``average``, ``median``,      |
|               | ``min``, ``max``, ``frequency``, ``frequency min``, and       |
|               | ``frequency max``.                                            |
|               |                                                               |
|               | *Optional, default* ``count``.                                |
+---------------+---------------------------------------------------------------+
| ``unit``      | Time unit to report in for functions that return intervals.   |
|               | Available options are ``s``, ``ms``, and ``ns``.              |
|               |                                                               |
|               | *Optional, default* ``ms``.                                   |
+---------------+---------------------------------------------------------------+
| ``divider``   | Clock divider factor used on the input. The report will       |
|               | be multiplied by this amount before publishing.               |
|               |                                                               |
|               | *Optional, default* ``1``.                                    |
+---------------+---------------------------------------------------------------+


Functions
=========

``raw``
-------

The raw function will publish a JSON payload containing an array of all of
the intervals in ``unit``
s between events during the last ``interval``. This function ignores the
``divider`` option.

The first interval will be the time between the last event before this
interval and the first event in the current interval. The first recorded
event after the pin is setup may have strange values due to lack of a
previous event to measure from.

.. code-block:: JSON

    {
        "pulses": []
    }

``count``
---------

The count function is the simplest and will publish an integer representing the
number of pulses recorded during the last interval. The count will be multiplied
by the ``divider`` factor.

``average``
-----------

The average function will calculate the average time in integer ``unit``
s of all events during the last interval. The result will be multiplied by
``divider`` and then published.

``median``
----------

The median function will calculate the mathmatical median of all times in
integer ``unit``
s of all events during the last interval. The result will be multiplied by
``divider`` and then published.

``min`` and ``max``
-------------------

The min and max functions will select the lowest or highest time and convert it
to integer ``unit``
s. The result will be multiplied by ``divider`` and published.

``frequency``
-------------

The average will be taken of all events in the last interval and the frequency
will be calculated from this in hertz. The result will be multiplied by
``divider``, rounded to 3 decimal places and published.

``frequency min`` and ``frequency max``
---------------------------------------

These functions work like ``frequency`` but will select the lowest or highest
time between events for the calculation.
