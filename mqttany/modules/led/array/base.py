"""
**************
LED Array Base
**************

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

__all__ = ["baseArray"]

import threading, queue, time, json

from logger import log_traceback
from common import DataType, BusMessage, BusProperty, BusNode, POISON_PILL
from modules.led import common
from modules.led.common import ANIM_KEY_NAME, ANIM_KEY_REPEAT, ANIM_KEY_PRIORITY


class baseArray:
    def __init__(
        self,
        id: str,
        name: str,
        count: int,
        leds_per_pixel: int,
        color_order: str,
        fps: int,
    ):
        """
        **SUBCLASSES MUST SUPER() THIS METHOD**
        """
        self._id = id
        self._name = name.format(array_id=id)
        self._count = count
        self._per_pixel = leds_per_pixel
        self._order = color_order
        self._fps = fps
        self._frame_ms = round(1.0 / fps, 5)
        self._log = None  # subclasses must assign this
        self._setup = False
        self._array = None
        self.anims = {}
        self._anim_thread = None
        self._anim_cancel = None
        self._anim_soft_cancel = None
        self._anim_queue = None
        self._anim_manager = None

    def get_node(self) -> BusNode:
        """
        Returns a ``BusNode`` representing this array.
        """
        return BusNode(
            name=self._name,
            type="LED Array",
            properties={
                "animation": BusProperty(
                    name="Animation", settable=True, callback="anim_message"
                ),
                "count": BusProperty(name="LED Count", datatype=DataType.INT),
                "leds-per-pixel": BusProperty(
                    name="LEDs per Pixel", datatype=DataType.INT
                ),
                "fps": BusProperty(name="Frames per second", datatype=DataType.INT),
            },
        )

    def begin(self) -> bool:
        """
        Setup the LED array
        **SUBCLASSES MUST SUPER() THIS METHOD**
        """
        self._anim_cancel = threading.Event()
        self._anim_soft_cancel = threading.Event()
        self._anim_queue = queue.Queue()
        self._anim_manager = threading.Thread(
            name=f"manager_{self._name}",
            target=self._anim_queue_manager,
            daemon=False,
        )
        self._anim_manager.start()
        common.publish_queue.put_nowait(
            BusMessage(path=f"{self.id}/count", content=self._count, mqtt_retained=True)
        )
        common.publish_queue.put_nowait(
            BusMessage(
                path=f"{self.id}/leds-per-pixel",
                content=self._per_pixel,
                mqtt_retained=True,
            )
        )
        common.publish_queue.put_nowait(
            BusMessage(path=f"{self.id}/fps", content=self._fps, mqtt_retained=True)
        )
        return True

    def message_callback(self, message: BusMessage) -> BusMessage:
        """
        Handles any messages coming to the array.
        Base class method handles animations and brightness. If you need to handle
        additional messages on additional paths you will need to override this method
        and ``get_node``. You can ``super`` this method to handle the standard paths, it
        will return the ``BusMessage`` it was passed if it cannot match it to a path it
        knows, if it finds a match it will return ``None``.
        """
        if self._setup:
            path = "/".join(message.path.strip("/").split("/")[1:])
            if len(path.split("/")) > 2:
                self._log.debug("Received message on unregistered path: %s", message)

            elif path == "animation/set":
                try:
                    content_json = json.loads(message.content)
                except ValueError:
                    self._log.warn(
                        "Received unrecognized animation command: %s", message.content
                    )
                else:
                    anim = content_json.get(ANIM_KEY_NAME)
                    if anim:
                        if anim in self.anims:
                            self.run_animation(content_json)
                        else:
                            self._log.warn(
                                "Received animation command for unknown animation: %s",
                                anim,
                            )
                    else:
                        self._log.warn(
                            "Received animation command with no animation: %s",
                            content_json,
                        )

            else:
                # couldn't handle message here,
                # pass it on to caller in case they want to try
                return message
        return None

    def cleanup(self) -> None:
        """
        Cleanup actions when stopping
        **SUBCLASSES MUST SUPER() THIS METHOD**
        """
        if self._anim_manager and self._anim_manager.is_alive():
            self._anim_queue.put_nowait(POISON_PILL)
            self._anim_manager.join()
        self._setup = False
        self._array = None

    def show(self) -> None:
        """Update the LED strip"""
        raise NotImplementedError

    def setPixelColor(self, pixel: [int, str, list], color: int) -> None:
        """Set LED to 24/32-bit color value (``WWRRGGBB`` or ``RRGGBB``)"""
        raise NotImplementedError

    def setPixelColorRGB(
        self, pixel: [int, str, list], red: int, green: int, blue: int, white: int = 0
    ) -> None:
        """Set LED to RGB(W) values provided"""
        raise NotImplementedError

    def getPixelColor(self, pixel: int) -> int:
        """Return the 24/32-bit LED color (``RRGGBB`` or ``WWRRGGBB``)"""
        raise NotImplementedError

    def getPixelColorRGB(self, pixel: int):
        """Return an object with RGB(W) attributes"""
        raise NotImplementedError

    def getBrightness(self) -> int:
        """Get LED strip brightness"""
        raise NotImplementedError

    def setBrightness(self, brightness: int) -> None:
        """Set LED strip brightness"""
        raise NotImplementedError

    def numPixels(self) -> int:
        """Return the number of pixels in the strip"""
        return self._count

    def numColors(self) -> int:
        """Return the number of color channels (3 or 4)"""
        return len(self._order)

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def count(self) -> int:
        return self._count

    @property
    def colors(self) -> int:
        return self.numColors()

    @property
    def brightness(self) -> int:
        return self.getBrightness()

    @brightness.setter
    def brightness(self, value: int):
        self.setBrightness(value)

    def run_animation(self, anim_args: dict) -> None:
        """
        **DO NOT OVERRIDE THIS METHOD**
        Run animation function in a separate thread.
        Will block while aborting a running animation.
        """
        if not self._setup:
            return

        self._log.trace(
            "Queuing animation '%s' with args %s",
            anim_args[ANIM_KEY_NAME],
            anim_args,
        )
        self._anim_queue.put_nowait(anim_args)

    def _anim_queue_manager(self):
        """
        **DO NOT OVERRIDE THIS METHOD**
        Internal animation queue manager
        """
        self._log.trace("Animation Queue Manager for '%s' started", self._name)
        anim_queue = []
        while True:
            try:
                message = self._anim_queue.get_nowait()
            except queue.Empty:
                pass
            else:
                if message == POISON_PILL:
                    self._log.trace(
                        "Animation Queue Manager for '%s' received poison pill",
                        self._name,
                    )
                    if self._anim_thread is not None and self._anim_thread.is_alive():
                        self._log.trace(
                            "Cancelling running animation for array '%s'", self._name
                        )
                        self._anim_cancel.set()
                        self._anim_thread.join()
                    break
                else:
                    message[ANIM_KEY_PRIORITY] = message.get(ANIM_KEY_PRIORITY, 1)
                    message[ANIM_KEY_REPEAT] = message.get(ANIM_KEY_REPEAT, 1)
                    if message[ANIM_KEY_PRIORITY] == 2:
                        # cancels all running and queued anims
                        self._log.trace(
                            "Queue Manager for array '%s' received animation '%s' with "
                            "priority %d, running it now",
                            self._name,
                            message[ANIM_KEY_NAME],
                            message[ANIM_KEY_PRIORITY],
                        )
                        anim_queue = [message]  # dump any queued anims
                        if (
                            self._anim_thread is not None
                            and self._anim_thread.is_alive()
                        ):
                            self._log.trace(
                                "Cancelling running animation for array '%s'",
                                self._name,
                            )
                            self._anim_cancel.set()
                            self._anim_thread.join()
                    else:
                        self._log.trace(
                            "Queue Manager for array '%s' received animation '%s' with "
                            "priority %d, adding it to the queue",
                            self._name,
                            message[ANIM_KEY_NAME],
                            message[ANIM_KEY_PRIORITY],
                        )
                        anim_queue.append(message)

            if anim_queue:
                if self._anim_thread is None or not self._anim_thread.is_alive():
                    self._log.debug(
                        "Starting animation '%s' for array '%s' with arguments %s",
                        anim_queue[0][ANIM_KEY_NAME],
                        self._name,
                        anim_queue[0],
                    )
                    self._anim_cancel.clear()
                    self._anim_soft_cancel.clear()
                    anim_queue[0].pop(ANIM_KEY_PRIORITY)
                    self._anim_thread = threading.Thread(
                        name=f"anim_{self._name}",
                        target=self._anim_loop,
                        args=[
                            anim_queue[0],
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
                        self._log.trace(
                            "Waiting for running animation to finish for array '%s'",
                            self._name,
                        )
                        self._anim_soft_cancel.set()

            time.sleep(0.025)  # 25ms

    def _anim_loop(self, anim_args):
        """
        **DO NOT OVERRIDE THIS METHOD**
        Internal animation thread loop method
        """
        anim = anim_args[ANIM_KEY_NAME]
        repeat = anim_args[ANIM_KEY_REPEAT]
        remain = repeat or 1
        error_count = 0
        kwargs = {  # args to pass into anim function
            k: anim_args[k]
            for k in anim_args
            if k not in [ANIM_KEY_NAME, ANIM_KEY_PRIORITY, ANIM_KEY_REPEAT]
        }

        while remain > 0 and not self._anim_cancel.is_set():
            if self._anim_soft_cancel.is_set():
                break
            try:
                common.publish_queue.put_nowait(
                    BusMessage(path=f"{self.id}/animation", content=anim)
                )
                self.anims[anim].__globals__["FRAME_MS"] = self._frame_ms
                self.anims[anim](self, self._anim_cancel, **kwargs)
            except:
                self._log.debug(
                    "An error occurred while running animation '%s' for array '%s'",
                    anim,
                    self._name,
                )
                error_count += 1
                if error_count > 2:
                    self._log.error(
                        "Animation '%s' for '%s' errored 3 times, aborting",
                        anim,
                        self._name,
                    )
                    log_traceback(self._log)
                    break
            else:
                remain -= 1 if repeat else 0

        if self._anim_cancel.is_set() or (
            anim_args.get(ANIM_KEY_REPEAT, 1) > 1 and self._anim_soft_cancel.is_set()
        ):
            self._log.debug("Cancelled animation '%s' for array '%s'", anim, self._name)
        else:
            self._log.debug("Finished animation '%s' for array '%s'", anim, self._name)
        common.publish_queue.put_nowait(
            BusMessage(path=f"{self.id}/animation", content="")
        )
