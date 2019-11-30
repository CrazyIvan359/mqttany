#########
Launching
#########

The simplest way to launch MQTTany is from the command line:

.. code-block:: shell

    cd /opt/mqttany
    python3 mqttany/mqttany.py

But this has some obvious drawbacks. You have to run it manually, and must
keep the terminal session open.

Most of the time you will want MQTTany to run in the background at startup.
The following instructions will guide you through setting that up on Debian
Linux (including Raspbian).

#.  Included with MQTTany is a ``.service`` file that tells Debian what it is
    and how to run it. We need to put that file in the right place:

    .. code-block:: shell

        cd /opt/mqttany
        sudo cp mqttany.service /etc/systemd/system/mqttany.service

#.  We need to specify the user that MQTTany should run as. Edit the file:

    .. code-block:: shell

        sudo nano /etc/systemd/system/mqttany.service

    and add the username and group that MQTTany should run as:

    .. code-block:: shell

        User=
        Group=

#.  Next week need to tell ``system.d`` about our new file:

    .. code-block:: shell

        sudo systemctl daemon-reload

#.  And lastly we enabled our service to start on boot, and start it:

    .. code-block:: shell

        sudo systemctl enable mqttany
        sudo systemctl start mqttany

#.  Verify that MQTTany started correctly by running:

    .. code-block:: shell

        sudo systemctl status mqttany
