"""
****************
LED Array Common
****************

:Author: Michael Murton
"""
# Copyright (c) 2019-2020 MQTTany contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import threading, queue, time

import logger
from logger import log_traceback
from common import POISON_PILL

from modules.mqtt import resolve_topic
from modules.led.common import config, TEXT_PACKAGE_NAME, CONF_KEY_TOPIC
from modules.led.common import ANIM_KEY_NAME, ANIM_KEY_REPEAT, ANIM_KEY_PRIORITY

TEXT_NAME = ".".join(__name__.split(".")[-3:3])  # gives led.array

log = logger.get_module_logger(module=TEXT_NAME)

__all__ = ["baseArray"]


class baseArray:
    def __init__(self, name, topic, count, leds_per_pixel, color_order):
        """
        **SUBCLASSES MUST SUPER() THIS METHOD**
        """
        self._setup = False
        self._array = None
        self._name = name
        self._topic = resolve_topic(
            topic,
            subtopics=["{module_topic}"],
            substitutions={
                "module_topic": config[CONF_KEY_TOPIC],
                "module_name": TEXT_PACKAGE_NAME,
                "array_name": name,
            },
        )
        self._count = count
        self._per_pixel = leds_per_pixel
        self._order = color_order
        self.anims = {}
        self._anim_thread = None
        self._anim_cancel = None
        self._anim_soft_cancel = None
        self._anim_queue = None
        self._anim_manager = None

    def begin(self):
        """
        Setup the LED array
        **SUBCLASSES MUST SUPER() THIS METHOD**
        """
        self._anim_cancel = threading.Event()
        self._anim_soft_cancel = threading.Event()
        self._anim_queue = queue.Queue()
        self._anim_manager = threading.Thread(
            name="manager_{}".format(self._name),
            target=self._anim_queue_manager,
            daemon=False,
        )
        self._anim_manager.start()

    def cleanup(self):
        """
        Cleanup actions when stopping
        **SUBCLASSES MUST SUPER() THIS METHOD**
        """
        if self._anim_manager.is_alive():
            self._anim_queue.put_nowait(POISON_PILL)
            self._anim_manager.join()
        self._setup = False
        self._array = None

    def show(self):
        """Update the LED strip"""
        raise NotImplementedError

    def setPixelColor(self, pixel, color):
        """Set LED to 24/32-bit color value (``WWRRGGBB`` or ``RRGGBB``)"""
        raise NotImplementedError

    def setPixelColorRGB(self, pixel, red, green, blue, white=0):
        """Set LED to RGB(W) values provided"""
        raise NotImplementedError

    def getBrightness(self):
        """Get LED strip brightness"""
        raise NotImplementedError

    def setBrightness(self, brightness):
        """Set LED strip brightness"""
        raise NotImplementedError

    def numPixels(self):
        """Return the number of pixels in the strip"""
        return self._count

    def getPixelColor(self, pixel):
        """Return the 24/32-bit LED color (``RRGGBB`` or ``WWRRGGBB``)"""
        raise NotImplementedError

    def getPixelColorRGB(self, pixel):
        """Return an object with RGB(W) attributes"""
        raise NotImplementedError

    def numColors(self):
        """Return the number of color channels (3 or 4)"""
        return len(self._order)

    @property
    def name(self):
        return self._name

    @property
    def topic(self):
        return self._topic

    @property
    def count(self):
        return self._count

    @property
    def colors(self):
        return self.numColors()

    @property
    def brightness(self):
        return self.getBrightness()

    @brightness.setter
    def brightness(self, value):
        self.setBrightness(value)

    def runAnimation(self, anim, repeat=1, priority=1, anim_args={}):
        """
        **DO NOT OVERRIDE THIS METHOD**
        Run animation function in a separate thread.
        Will block while aborting a running animation.
        """
        if not self._setup:
            return

        log.trace(
            "Array '{array}' received animation '{anim}' with arguments {args}".format(
                anim=anim, array=self._name, args=anim_args
            )
        )
        self._anim_queue.put_nowait(
            {
                ANIM_KEY_NAME: anim,
                ANIM_KEY_REPEAT: repeat,
                ANIM_KEY_PRIORITY: priority,
                "args": anim_args,
            }
        )

    def _anim_queue_manager(self):
        """
        **DO NOT OVERRIDE THIS METHOD**
        Internal animation queue manager
        """
        log.trace(
            "Animation Queue Manager for '{array}' started".format(array=self._name)
        )
        anim_queue = []
        while True:
            try:
                message = self._anim_queue.get_nowait()
            except queue.Empty:
                pass
            else:
                if message == POISON_PILL:
                    log.trace(
                        "Animation Queue Manager for '{array}' received poison pill".format(
                            array=self._name
                        )
                    )
                    if self._anim_thread is not None and self._anim_thread.is_alive():
                        log.trace(
                            "Cancelling running animation for array '{array}'".format(
                                array=self._name
                            )
                        )
                        self._anim_cancel.set()
                        self._anim_thread.join()
                    break
                else:
                    if (
                        message[ANIM_KEY_PRIORITY] == 2
                    ):  # cancels all running and queued anims
                        log.trace(
                            "Queue Manager for array '{array}' received animation '{anim}' with priority {priority}, running it now".format(
                                array=self._name,
                                anim=message[ANIM_KEY_NAME],
                                priority=message[ANIM_KEY_PRIORITY],
                            )
                        )
                        anim_queue = [message]  # dump any queued anims
                        if (
                            self._anim_thread is not None
                            and self._anim_thread.is_alive()
                        ):
                            log.trace(
                                "Cancelling running animation for array '{array}'".format(
                                    array=self._name
                                )
                            )
                            self._anim_cancel.set()
                            self._anim_thread.join()
                    else:
                        log.trace(
                            "Queue Manager for array '{array}' received animation '{anim}' with priority {priority}, adding it to the queue".format(
                                array=self._name,
                                anim=message[ANIM_KEY_NAME],
                                priority=message[ANIM_KEY_PRIORITY],
                            )
                        )
                        anim_queue.append(message)

            if anim_queue:
                if self._anim_thread is None or not self._anim_thread.is_alive():
                    log.debug(
                        "Starting animation '{anim}' for array '{array}' with arguments {args}".format(
                            anim=anim_queue[0][ANIM_KEY_NAME],
                            array=self._name,
                            args=anim_queue[0]["args"],
                        )
                    )
                    self._anim_cancel.clear()
                    self._anim_soft_cancel.clear()
                    self._anim_thread = threading.Thread(
                        name="anim_{}".format(self._name),
                        target=self._anim_loop,
                        args=[
                            anim_queue[0][ANIM_KEY_NAME],
                            anim_queue[0][ANIM_KEY_REPEAT],
                            anim_queue[0]["args"],
                        ],
                        daemon=False,
                    )
                    anim_queue.pop(0)
                    self._anim_thread.start()

                elif (
                    anim_queue[0][ANIM_KEY_PRIORITY] == 1
                ):  # waits for running anim to finish or for current step of infinite to finish
                    if (
                        self._anim_thread is not None
                        and self._anim_thread.is_alive()
                        and not self._anim_soft_cancel.is_set()
                    ):
                        log.trace(
                            "Waiting for running animation to finish for array '{array}'".format(
                                array=self._name
                            )
                        )
                        self._anim_soft_cancel.set()

            time.sleep(0.025)  # 25ms

    def _anim_loop(self, anim, repeat, anim_args):
        """
        **DO NOT OVERRIDE THIS METHOD**
        Internal animation thread loop method
        """
        remain = repeat or 1
        error_count = 0

        while remain > 0 and not self._anim_cancel.is_set():
            if self._anim_soft_cancel.is_set():
                break
            try:
                self.anims[anim](self, self._anim_cancel, **anim_args)
            except:
                log.debug(
                    "An error occurred while running animation '{anim}' for array '{array}'".format(
                        anim=anim, array=self._name
                    )
                )
                error_count += 1
                if error_count > 2:
                    log.error(
                        "Animation '{anim}' for '{array}' errored 3 times, aborting".format(
                            anim=anim, array=self._name
                        )
                    )
                    log_traceback(log)
                    break
            else:
                remain -= 1 if repeat else 0

        if self._anim_cancel.is_set() or (
            not repeat and self._anim_soft_cancel.is_set()
        ):
            log.debug(
                "Cancelled animation '{anim}' for array '{array}'".format(
                    anim=anim, array=self._name
                )
            )
        else:
            log.debug(
                "Finished animation '{anim}' for array '{array}'".format(
                    anim=anim, array=self._name
                )
            )
