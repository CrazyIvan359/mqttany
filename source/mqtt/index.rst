####
MQTT
####

The MQTT module wraps the Paho MQTT Client library and provides a pub/sub
interface for other modules. This module should always be the first section in
the configuration file, otherwise MQTTany will not do anything useful.


Topics
======

MQTTany offers two ways to define topic settings, relative and absolute.

Relative
--------

Relative topics will have the *root topic* and module *topic* prepended to the
topic (*Ex.* ``{root_topic}/{module_topic}/example_topic``).

Absolute
--------

Topics starting with a ``/`` will be treated as absolute topics and will not
have anything prepended to them. The leading ``/`` will be removed before
publishing.


Substitutions
=============

All topics will have the following substitutions applied. Modules can also add
other subtitutions.

+--------------------+--------------------------------------------------------+
| ``{hostname}``     | will be replaced with the computer's hostname.         |
+--------------------+--------------------------------------------------------+
| ``{client_id}``    | will be replaced with the MQTT Client ID.              |
+--------------------+--------------------------------------------------------+
| ``{root_topic}``   | will be replaced with the root topic.                  |
+--------------------+--------------------------------------------------------+
| ``{module_name}``  | will be replaced with the name of the module.          |
+--------------------+--------------------------------------------------------+
| ``{module_topic}`` | will be replaced with the module topic.                |
+--------------------+--------------------------------------------------------+


Configuration
=============

Optional settings are commented out, default values are shown.

.. code-block:: yaml

    mqtt:

      host:
      #port: 1883

      #client id: '{hostname}'
      #username: ''
      #password: ''

      #qos: 0
      #retain: false

      #root topic: '{client_id}'
      #lwt topic: 'lwt'

      #heartbeat interval: 300


+----------------+------------------------------------------------------------+
| ``host``       | The address or hostname of your MQTT broker.               |
+----------------+------------------------------------------------------------+
| ``port``       | The port your MQTT broker is running on.                   |
|                |                                                            |
|                | *Optional, default* ``1883``.                              |
+----------------+------------------------------------------------------------+
| ``client id``  | MQTT Client ID used when connecting to the broker.         |
|                |                                                            |
|                | *Optional, default* ``{hostname}``.                        |
+----------------+------------------------------------------------------------+
| ``username``   | Username to use when authenticating with the MQTT broker.  |
|                |                                                            |
|                | *Optional*.                                                |
+----------------+------------------------------------------------------------+
| ``password``   | Password to use when authenticating with the MQTT broker.  |
|                |                                                            |
|                | *Optional*.                                                |
+----------------+------------------------------------------------------------+
| ``qos``        | Quality of Service setting to use when publishing to MQTT. |
|                | *Modules can specify a QoS when publishing.*               |
|                |                                                            |
|                | *Optional, default* ``0``.                                 |
+----------------+------------------------------------------------------------+
| ``retain``     | Retain flag to use when publishing to MQTT.                |
|                | *Modules can specify the retain flag when publishing.*     |
|                |                                                            |
|                | *Optional, default* ``false``.                             |
+----------------+------------------------------------------------------------+
| ``root topic`` | The root topic to use when composing relative topics.      |
|                | See the :ref:`mqtt/index:topics` section for more          |
|                | information.                                               |
|                |                                                            |
|                | *Optional, default* ``{client_id}``.                       |
+----------------+------------------------------------------------------------+
| ``lwt topic``  | Last Will topic to publish online/offline messages.        |
|                |                                                            |
|                | *Optional, default* ``lwt``.                               |
+----------------+------------------------------------------------------------+
| ``heartbeat    | Interval in seconds to publish status messages             |
| interval``     |                                                            |
+----------------+------------------------------------------------------------+
