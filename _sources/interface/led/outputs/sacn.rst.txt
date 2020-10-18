#############
Streaming ACN
#############


Lights can be controlled via ESTA E1.31, also known as sACN, over your local
network.


.. admonition:: Don't forget to install the requirements

    .. code-block:: shell

        pip3 install -r requirements/led-sacn.txt


.. warning::

    It is recommended you reduce ``anim fps`` to 24fps or even lower depending
    on your network conditions. sACN receivers may have trouble keeping up otherwise.

    Setting this value will limit the frame rate for the animations running on
    MQTTany, but there is no guarantee that the receiver will be able to keep
    up.


Paths
=====

Some additional statistics are published when using this output mode.

+-------------------------+-------------------------------------------------+
|          Path           |                   Description                   |
+=========================+=================================================+
| ``{array-id}/universe`` | The universe or range of universes used by this |
|                         | array will be published here with               |
|                         | ``retained = True`` when the array is started.  |
+-------------------------+-------------------------------------------------+
| ``{array-id}/mode``     | The network transmission mode, unicast or       |
|                         | multicast, will be published here with          |
|                         | ``retained = True`` when the array is started.  |
+-------------------------+-------------------------------------------------+
| ``{array-id}/address``  | If using unicast the target address will be     |
|                         | published here with ``retained = True`` when    |
|                         | the array is started.                           |
+-------------------------+-------------------------------------------------+
| ``{array-id}/sync``     | If a sync universe was specified it will be     |
|                         | published here with ``retained = True`` when    |
|                         | the array is started.                           |
+-------------------------+-------------------------------------------------+


Configuration
=============

.. code-block:: yaml

    led:

      array_name:
        sacn:
          universe:
          #address: ''
          #sync universe:


Array Definition
----------------

The following additional options are added to array definitions when using
this interface.

+-------------------+-----------------------------------------------------+
|      Option       |                     Description                     |
+===================+=====================================================+
| ``universe``      | Universe number, more universes may be controlled   |
|                   | depending on the number of LEDs and channels in the |
|                   | array.                                              |
+-------------------+-----------------------------------------------------+
| ``address``       | Unicast address or hostname. If not provided then   |
|                   | multicast will be used                              |
+-------------------+-----------------------------------------------------+
| ``sync universe`` | Universe to send sync packets to. If not provided   |
|                   | data packets will be sent immediately and no sync   |
|                   | packets will be sent.                               |
|                   |                                                     |
|                   | .. caution::                                        |
|                   |     Using sync results in a **LOT** more network    |
|                   |     traffic. Use with care.                         |
|                   |                                                     |
|                   | *This has not yet been tested*                      |
+-------------------+-----------------------------------------------------+
