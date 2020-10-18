####
XSET
####


Allows ``xset`` commands to be executed to set screensaver and display power
options.

This can, for example, be used to wake the display when motion is detected in
front of it.


Paths
=====

+----------------------+----------------------------------------------------+
|         Path         |                    Description                     |
+======================+====================================================+
| ``xset/command/set`` | Commands should be sent here as a JSON string. The |
|                      | ``command`` should contain everything that would   |
|                      | follow ``xset`` if you were using it on the        |
|                      | command line. ``display`` is optional.             |
|                      |                                                    |
|                      | .. code-block: python                              |
|                      |     {                                              |
|                      |         "command": "s off",                        |
|                      |         "display": ":0"                            |
|                      |     }                                              |
+----------------------+----------------------------------------------------+
| ``xset/command``     | The full command will be published here when run.  |
+----------------------+----------------------------------------------------+
| ``xset/stdout``      | The output from ``stdout`` will be published here. |
+----------------------+----------------------------------------------------+
| ``xset/stderr``      | The output from ``stderr`` will be published here. |
+----------------------+----------------------------------------------------+


Configuration
=============

Optional settings are commented out with default values shown.

.. code-block:: yaml

    xset:

      #default display: None
      startup commands: []


Module Settings
---------------

+----------------------+------------------------------------------------------+
|        Option        |                     Description                      |
+======================+======================================================+
| ``default display``  | Value for the ``-display`` option of the ``xset``    |
|                      | command to use when commands do not provide one.     |
|                      | This can be used to simplify commands if all         |
|                      | commands are to be sent to the same display (*Ex.*   |
|                      | ``:0`` is the first display).                        |
|                      |                                                      |
|                      | *Optional, default* ``None``.                        |
+----------------------+------------------------------------------------------+
| ``startup commands`` | A list of commands to run when the module is loaded. |
|                      | These commands use the same format as commands sent  |
|                      | via MQTT, see the section below on commands for      |
|                      | details.                                             |
|                      |                                                      |
|                      | This option is required because the ``xset`` config  |
|                      | section cannot be blank. If no commands are desired  |
|                      | use an empty list (``[]``) as the value.             |
+----------------------+------------------------------------------------------+


Useful ``xset`` Commands
========================

+--------------------+-----------------------------------------------------+
|      Command       |                     Description                     |
+====================+=====================================================+
| ``s off``          | Disable screensaver                                 |
| ``s 0``            |                                                     |
+--------------------+-----------------------------------------------------+
| ``s 300``          | Set screensaver idle time to 5 minutes. Time units  |
|                    | may vary by distro                                  |
+--------------------+-----------------------------------------------------+
| ``dpms force off`` | Force display to turn off                           |
+--------------------+-----------------------------------------------------+
| ``dpms force on``  | Force display to turn on                            |
+--------------------+-----------------------------------------------------+
| ``dpms 0 0 600``   | Set display off idle time to 10 minutes. Time units |
|                    | may vary by distro.                                 |
+--------------------+-----------------------------------------------------+
