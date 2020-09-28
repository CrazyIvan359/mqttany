############
Raspberry Pi
############


You can connect an array to a limited selection of pins on most Raspberry Pi
boards. This support is provided by the ``rpi_ws281x`` library, see it on
`GitHub <https://github.com/jgarff/rpi_ws281x>`_ for details.

The LEDs supported by this interface usually run at 5V, but the Pi only
outputs a maximum of 3.3V. While this may be enough to drive a small number of
LEDs, it is highly recommended that you use some kind of buffer or level
shifter when connecting them to GPIO pins.

.. admonition:: Don't forget to install the requirements

    .. code-block:: shell

        pip3 install -r requirements/led-rpi.txt


Paths
=====

Some additional statistics are published when using this output mode.

+--------------------------+-------------------------------------------------+
|           Path           |                   Description                   |
+==========================+=================================================+
| ``{array-id}/gpio``      | The GPIO being used will be published here with |
|                          | ``retained = True`` when the array is started.  |
+--------------------------+-------------------------------------------------+
| ``{array-id}/chip``      | The LED chip type will be published here with   |
|                          | ``retained = True`` when the array is started.  |
+--------------------------+-------------------------------------------------+
| ``{array-id}/frequency`` | The transmission frequency will be published    |
|                          | here with ``retained = True`` when the array    |
|                          | is started.                                     |
+--------------------------+-------------------------------------------------+
| ``{array-id}/invert``    | The invert state will be published here with    |
|                          | ``retained = True`` when the array is started.  |
+--------------------------+-------------------------------------------------+

Configuration
=============

.. code-block:: yaml

    led:

      array_name:
        rpi:
          gpio:
          #chip: 'WS2812B'
          #frequency: 800
          #invert: false


Array Definition
----------------

The following additional options are added to array definitions when using
this interface.

+---------------+-------------------------------------------------------+
|    Option     |                      Description                      |
+===============+=======================================================+
| ``gpio``      | GPIO pin number.                                      |
|               |                                                       |
|               | **ONLY BCM/SOC NUMBERING IS SUPPORTED**               |
+---------------+-------------------------------------------------------+
| ``chip``      | LED type, can be ``WS2811``, ``WS2812``, ``WS2812B``, |
|               | ``SK6812``, or ``SK6812W``.                           |
|               |                                                       |
|               | *Optional, default* ``WS2812B``.                      |
+---------------+-------------------------------------------------------+
| ``frequency`` | **DO NOT CHANGE THIS UNLESS YOU KNOW WHAT YOU ARE     |
|               | DOING**                                               |
|               |                                                       |
|               | The clock frequency in kHz for transmitting data to   |
|               | the LEDs.                                             |
|               |                                                       |
|               | *Optional, default* ``800``.                          |
+---------------+-------------------------------------------------------+
| ``invert``    | Invert the data signal to the LEDs, this is useful    |
|               | if you are using an inverting buffer.                 |
|               |                                                       |
|               | *Optional, default* ``false``.                        |
+---------------+-------------------------------------------------------+


Output Selection
================

.. note::
    The documentation for ``rpi_ws281x`` is not clear on this and I have not
    tested it, but it may be possible to use multiple interfaces at once.

SPI
---

The SPI interface is the safest way to control your LEDs using a Pi and the
only one available on all models. Connect them to ``SPI0-MOSI`` (GPIO10) using
a level shifter. When using the SPI interface to control your LEDs you cannot
use it for anything else. Using SPI leaves the digital audio (I2S/PCM) and
analog/PWM audio available.

To use SPI, the user running MQTTany needs to be a member of the ``gpio``
group.

You also need to increase the size of the SPI buffer and change the GPU
core frequency. Add the following lines to ``/boot/config.txt`` and restart to
apply these changes:

.. code-block:: text

    spidev.bufsiz=32768
    core_freq=250

PWM
---

The hardware PWM on the Pi is the only interface with 2 outputs. In order to
achieve the required timing it uses DMA and requires root privileges.

* ``PWM0`` is available on GPIO12 or GPIO18 and MQTTany uses DMA channel 10.
  It is present on the B+, 2B, 3B, and 3B+.
* ``PWM1`` is available on GPIO13 and MQTTany uses DMA channel 11.
  It is present on the B+, 2B, 3B, 3B+, and Zero.

The on board/analog audio also uses the PWM hardware, so you need to blacklist
it by adding the following to ``/etc/modprobe.d/snd-blacklist.conf``:

.. code-block:: text

    blacklist snd_bcm2835

On headless systems you may need to force the audio device to be the HDMI out.
Add the following to ``/boot/config.txt`` and restart:

.. code-block:: text

    hdmi_force_hotplug=1
    hdmi_force_edid_audio=1

PCM
---

The hardware PCM can also be used to control a single array of LEDs. It also
uses DMA and requires root privileges.

* ``PCM_DOUT`` is on GPIO21 and MQTTany uses DMA channel 13.
  It is present on the B+, 2B, 3B, 3B+, and Zero.

When using PCM you will not be able to use any digital/I2S audio devices,
analog/PWM audio and the SPI interface are free for use though.
