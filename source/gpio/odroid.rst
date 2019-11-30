######
Odroid
######

Support for several Odroid boards has been added to the GPIO module.

* :ref:`Odroid C1 <gpio/odroid:odroid c1/c1+>` *(untested)*
* :ref:`Odroid C1+ <gpio/odroid:odroid c1/c1+>` *(untested)*
* :ref:`gpio/odroid:odroid c2`
* :ref:`Odroid XU3 <gpio/odroid:odroid xu3/xu4>` *(untested)*
* :ref:`Odroid XU4 <gpio/odroid:odroid xu3/xu4>` *(untested)*
* :ref:`gpio/odroid:odroid n2` *(untested)*

If you encounter any problems or errors, please open a new issue and post your
logs.

.. admonition:: Don't forget to install the requirements

    .. code-block:: shell

        pip3 install -r requirements/gpio-odroid.txt


.. warning::
    Pin change interrupts will not be registered when using ``SOC`` pin
    numbering because there is a bug in HardKernel's wiringpi-python port.
    You can use interrupts in ``BOARD`` or ``WIRINGPI`` numbering schemes
    without issue.


Install WiringPi
================

Installing Odroid WiringPi requires cloning and building manually:

.. code-block:: shell

    cd /opt
    git clone https://github.com/hardkernel/wiringPi
    cd wiringPi
    ./build
    cd /opt/mqttany


Odroid C1/C1+
=============

.. image:: /_static/gpio/odroid-c1-40.png
    :alt: Odroid C1/C1+ 40-pin Header

.. image:: /_static/gpio/odroid-c1p-j7.png
    :alt: Odroid C1+ J7 Header


Odroid C2
=========

.. image:: /_static/gpio/odroid-c2-40.png
    :alt: Odroid C2 40-pin Header


Odroid XU3/XU4
==============

.. warning::
    Without an XU3 to test I cannot identify whether you have an XU3 or XU4
    board. The XU3 model does not have the CON11 header. You must not attempt
    to use any of the GPIO pins on that header if you have an XU3.

.. note::
    The ``BOARD`` pin numbering for the XU3 and XU4 is based on the Shifter
    Shield 40-pin connector and not the CON10 and CON11 headers.

.. image:: /_static/gpio/odroid-xu-40.png
    :alt: Odroid XU3/XU4 Shifter Shield 40-pin Header

.. image:: /_static/gpio/odroid-xu-c10.png
    :alt: Odroid XU3/XU4 CON10 Header

.. image:: /_static/gpio/odroid-xu4-c11.png
    :alt: Odroid XU4 CON11 Header


Odroid N2
=========

.. image:: /_static/gpio/odroid-n2-40.png
    :alt: Odroid N2 40-pin Header
