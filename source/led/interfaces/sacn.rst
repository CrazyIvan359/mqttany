#############
Streaming ACN
#############


Lights can be controlled via ESTA E1.31, also known as sACN, over your local
network.


.. admonition:: Don't forget to install the requirements

    .. code-block:: shell

        pip3 install -r requirements/led-sacn.txt


.. warning::

    It is recommended you increase ``anim frame min`` to ``0.042`` (24fps) or
    even higher depending on your network conditions. sACN receivers may have
    trouble keeping up otherwise.

    Setting this value will limit the frame rate for the animations running on
    MQTTany, but there is no guarantee that the receiver will be able to keep
    up.


Configuration
=============

.. code-block:: yaml

    led:

      array_name:
        sacn universe:
        #sacn address: ''
        #sacn sync universe:


Array Definition
----------------

The following additional options are added to array definitions when using
this interface.

+----------------------+------------------------------------------------------+
| ``sacn universe``    | Universe number, more universes may be controlled    |
|                      | depending on the number of LEDs and channels in the  |
|                      | array.                                               |
+----------------------+------------------------------------------------------+
| ``sacn address``     | Unicast address or hostname. If not provided then    |
|                      | multicast will be used                               |
+----------------------+------------------------------------------------------+
| ``sacn sync          | Universe to send sync packets to. If not provided    |
| universe``           | data packets will be sent immediately and no sync    |
|                      | packets will be sent.                                |
|                      |                                                      |
|                      | .. caution::                                         |
|                      |   Using sync results in a **LOT** more network       |
|                      |   traffic. Use with care.                            |
|                      |                                                      |
|                      | *This has not yet been tested*                       |
+----------------------+------------------------------------------------------+
