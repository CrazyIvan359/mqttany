###############
Getting Started
###############

This page gives you an introduction to the concepts in MQTTany and walks you through
getting a simple configuration up and running.


Modules
=======

MQTTany is made up of modules, each with a specific function. *Communication Modules*
provide a means to send states and receive commands from a controller, such as your
home automation solution. *Interface Modules* connect to the hardware, such as GPIO
pins or I2C devices, they provide states, and process commands. Details for each
module can be found on their pages which you can find in the categories in the
navigation bar to left. Most modules have additional requirements, make sure you
install them before using the module.


Paths
=====

The concept of paths was introduced in version 0.12.0 in order to allow a generic
form of messaging between MQTTany modules. It is important to understand how paths are
composed so that you know where to find states and send commands to. Paths are similar
to topics in MQTT, and indeed are used to form the topics used in the MQTT module.

Interface modules will provide a map of the paths they provide data and receive
commands on, which communication modules can use to make a tree describing your MQTTany
configuration and provide to controllers. This map is composed of 1 or more *nodes*,
with each node having 1 or more *properties*.

As you will see in the example below, internally paths are composed of
``{node-id}/{property-id}``, but communication modules may preface them. Communication
modules, however, will not add anything to the end of a path. Commands can always
be sent to ``{node-id}/{property-id}/set`` for properties that support receiving
commands, but some interface modules support additional command paths.

While this does seem to limit the paths available, some communication modules will pass
all messages received that match the node and property the interface module has
advertised. Interface modules may also publish to paths made up of more than a node
and property that they advertise, but not all communication modules support this.

Paths are an internal concept to MQTTany, but are used to compose the externally
exposed data structure. For example a GPIO pin with an ID of ``my-pin`` would have a
path of ``gpio/my-pin`` for its state, where ``gpio`` is the node provided by the GPIO
module and ``my-pin`` is the property. The MQTT module requires a root topic be
specified, let's use ``my-host`` in our example. Our pin would have it's state
publishud by the MQTT module on the topic ``my-host/gpio/my-pin``. In order to change
this pin you would add ``set`` to the path, resulting in the MQTT topic
``my-host/gpio/my-pin/set`` to send your command to.


IDs
===

Paths contain node and property IDs which must conform to certain criteria. They may
only contain lowercase letters ``a-z``, numbers ``0-9``, or a hyphen ``-``. IDs must
not start or end with a hyphen.


Configuration
=============

MQTTany uses a YAML configuration file. The default location it looks for this file
in is ``/etc/mqttany/mqttany.yml`` but you can specify another location when launching.
There is an example configuration file included with MQTTany that has all the options
from every module along with a short description of each one, full documentation on
these options can be found on the module pages.

The configuration for our example from above would look like this:

.. code-block:: yaml

    mqtt:
      host: 'localhost'
      root topic: 'my-host'

    gpio:
      my-pin:
        pin: 13
        direction: 'output'


Installation
============

There is no installation script at this time, so you will need to clone the
GitHub repository. The recommended location to clone the repo to is
``/opt/mqttany``, the following instructions will assume this location.


#.  We need to make sure Python |pyversion| and PIP are installed.

    .. code-block:: shell

        sudo apt-get update
        sudo apt-get install python3 python3-pip
        python3 --version

    Make sure the version that was installed is at least Python |pyversion|. If it is
    less you will need to install a newer version manually,
    `this document <https://docs.python.org/3/using/unix.html#getting-and-installing-the-latest-version-of-python>`_
    from the Python documentation provides instructions.

#.  Now we will change to the download directory and clone the repo. Replace
    ``VERSION`` with the version you want to download (ex |mqttanyversioncode|).

    .. code-block:: shell

        cd /opt
        git clone -b VERSION https://github.com/CrazyIvan359/mqttany.git
        cd mqttany

    It may be necessary to use ``sudo`` to clone the repo into ``/opt``, you can use
    the commands below to give yourself access to the new ``mqttany`` directory without
    using `sudo` for all operations.

    .. code-block:: shell

        sudo chown :$USER /opt/mqttany
        sudo chmod -R g+rw /opt/mqttany

#.  Next we need to make sure all of the requirements to run MQTTany are met.

    .. code-block:: shell

        pip3 install -r requirements/mqttany.txt

#.  Lastly we need to copy the configuration file to where MQTTany expects it.
    You can also specify a configuration file when launching MQTTany if you
    want, run ``python3 mqttany/mqttany.py -h`` for more information.

    .. code-block:: shell

        sudo mkdir /etc/mqttany
        sudo cp /opt/mqttany/mqttany/config/mqttany.yml /etc/mqttany/mqttany.yml
