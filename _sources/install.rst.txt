############
Installation
############

There is no installation script at this time, so you will need to clone the
GitHub repository. The recommended location to clone the repo to is
``/opt/mqttany``, these instructions will assume this location.


#.  We need to make sure Python 3 and PIP are installed.

    .. code-block:: shell

        sudo apt-get install python3 python3-pip

#.  Now we will change to the download directory and clone the repo. Replace
    ``VERSION`` with the version you want to download (ex ``v0.10.0``).

    .. code-block:: shell

        cd /opt
        git clone -b VERSION https://github.com/CrazyIvan359/mqttany.git
        cd mqttany

#.  Next we need to make sure all of the requirements to run MQTTany are met.

    .. code-block:: shell

        pip3 install -r requirements/mqttany.txt

#.  Lastly we need to copy the configuration file to where MQTTany expects it.
    You can also specify a configuration file when launching MQTTany if you
    want, run ``python3 mqttany/mqttany.py -h`` for more information.

    .. code-block:: shell

        sudo mkdir /etc/mqttany
        sudo cp mqttany/config/mqttany.yml /etc/mqttany/mqttany.yml

Check out the module pages for details about the settings for each module.
Only modules with a section in the configuration file will be loaded.
