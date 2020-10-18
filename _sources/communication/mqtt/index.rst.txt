####
MQTT
####

The MQTT module wraps the Paho MQTT Client library and connects to a broker to
allow communication with home automation solutions or other controllers.


Paths
=====

MQTT topics are composed of the ``root topic`` plus the path. Ex.
``{root topic}/{node-id}/{property-id}``

The MQTT module subscribes to ``{root topic}/+/+/+/#`` and will pass any message matching
``{root topic}/{node-id}/{property-id}/+/#`` to the interface module that registered the
node, provided a callback was given.


Configuration
=============

The following options are available in the configuration file. Optional settings are
commented out with their default values shown.

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


+----------------+---------------------------------------------------------------+
|     Option     |                          Description                          |
+================+===============================================================+
| ``host``       | The IPv4 address or hostname of your MQTT broker.             |
+----------------+---------------------------------------------------------------+
| ``port``       | The port your MQTT broker is running on.                      |
|                |                                                               |
|                | *Optional, default* ``1883``.                                 |
+----------------+---------------------------------------------------------------+
| ``client id``  | MQTT Client ID used when connecting to the broker.            |
|                |                                                               |
|                | ``{hostname}`` will be replaced with the computer's hostname. |
|                |                                                               |
|                | *Optional, default* ``{hostname}``.                           |
+----------------+---------------------------------------------------------------+
| ``username``   | Username to use when authenticating with the MQTT broker.     |
|                |                                                               |
|                | *Optional*.                                                   |
+----------------+---------------------------------------------------------------+
| ``password``   | Password to use when authenticating with the MQTT broker.     |
|                |                                                               |
|                | *Optional*.                                                   |
+----------------+---------------------------------------------------------------+
| ``qos``        | Quality of Service setting to use when publishing to MQTT.    |
|                | *Modules can specify a QoS when publishing.*                  |
|                |                                                               |
|                | *Optional, default* ``0``.                                    |
+----------------+---------------------------------------------------------------+
| ``retain``     | Default retain flag to use when publishing to MQTT.           |
|                | *Modules can specify the retain flag when publishing.*        |
|                |                                                               |
|                | *Optional, default* ``false``.                                |
+----------------+---------------------------------------------------------------+
| ``root topic`` | The root topic to use for all other topics.                   |
|                |                                                               |
|                | Substitutions:                                                |
|                |                                                               |
|                | ``{hostname}`` will be replaced with the computer's hostname. |
|                |                                                               |
|                | ``{client_id}`` will be replaced with the MQTT Client ID.     |
|                |                                                               |
|                | *Optional, default* ``{client_id}``.                          |
+----------------+---------------------------------------------------------------+
| ``lwt topic``  | Last Will topic to publish online/offline messages. Full      |
|                | topic is ``{root topic}/{lwt topic}``.                        |
|                |                                                               |
|                | *Optional, default* ``lwt``.                                  |
+----------------+---------------------------------------------------------------+
| ``heartbeat    | Interval in seconds to publish status messages.               |
| interval``     |                                                               |
|                | *Optional, default* ``300``.                                  |
+----------------+---------------------------------------------------------------+
