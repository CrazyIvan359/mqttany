"""
**************
LED Animations
**************

:Author: Michael Murton
"""
# Copyright (c) 2019-2022 MQTTany contributors
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

__all__ = ["load_animations"]

import importlib.util
import inspect
import os
import threading
import time
import typing as t
from collections import Sequence

import logger
from logger import log_traceback

from .array.base import baseArray
from .common import CONF_KEY_ANIM_DIR, CONFIG, Color, log

log = logger.get_logger("led.anim")

DEFAULT_PATH = "/etc/mqttany/led-anim"


def load_animations() -> t.Dict[str, t.Callable[[baseArray, threading.Event], None]]:
    """
    Loads custom animations and returns a dictionary of them and the built-ins.
    """
    anims: t.Dict[
        str, t.Callable[[baseArray, threading.Event], None]
    ] = {  # built-in animations
        "on": anim_on,
        "off": anim_off,
        "set.brightness": anim_set_brightness,
        "set.array": anim_set_array,
        "set.pixel": anim_set_pixel,
        "fade.on": anim_fade_on,
        "fade.off": anim_fade_off,
        "fade.brightness": anim_fade_brightness,
        "fade.array": anim_fade_array,
        "fade.pixel": anim_fade_pixel,
        "test.order": anim_testorder,
        "test.array": anim_testarray,
    }
    utils: t.List[t.Callable[[baseArray, *t.Any], t.Any]] = [  # utility functions
        parse_color,
        parse_pixel,
    ]

    log.debug("Loading animations")

    animpaths: t.List[str] = [DEFAULT_PATH] if os.path.isdir(DEFAULT_PATH) else []
    animpaths += (
        CONFIG[CONF_KEY_ANIM_DIR]
        if isinstance(CONFIG[CONF_KEY_ANIM_DIR], list)
        else [CONFIG[CONF_KEY_ANIM_DIR]]
    )
    for animpath in animpaths:
        if os.path.isdir(animpath):
            log.debug("Checking for animation files in '%s'", animpath)
            for filename in os.listdir(animpath):
                if (
                    os.path.splitext(filename)[-1] == ".py"
                    and filename != "__init__.py"
                ):
                    log.trace(
                        "Attempting to import animation file '%s'",
                        os.path.join(animpath, filename),
                    )
                    mod_name = os.path.splitext(filename)[0]
                    mod_anims = []

                    try:
                        spec = importlib.util.spec_from_file_location("*", filename)
                        if spec is not None:
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)  # type:ignore
                        else:
                            raise ImportError()
                    except:
                        log.error(
                            "An error occured while importing animation file '%s'",
                            filename,
                        )
                        log_traceback(log)
                        log.error("Animation file '%s' was not loaded", filename)
                    else:
                        log.trace("Animation file '%s' imported successfully", mod_name)

                        # get all functions in module that start with "anim_" and don't have a conflicting name
                        mod_anims = dict(inspect.getmembers(module, inspect.isfunction))
                        for func_name in [key for key in mod_anims]:
                            if not func_name.startswith("anim_"):
                                mod_anims.pop(func_name, None)
                                log.trace(
                                    "Ignoring function '%s' in '%s' as it does not start with 'anim_",
                                    func_name,
                                    os.path.join(animpath, filename),
                                )
                            elif not callable(mod_anims[func_name]):
                                # TODO check function signatures
                                mod_anims.pop(func_name, None)
                                log.warn(
                                    "Ignoring animation '%s.%s' in '%s' as it is not callable",
                                    mod_name,
                                    func_name[5:],
                                    os.path.join(animpath, filename),
                                )
                            elif f"{mod_name}.{func_name[5:]}" in mod_anims:
                                mod_anims.pop(func_name, None)
                                log.warn(
                                    "Duplicate animation '%s.%s' in '%s' is being ignored",
                                    mod_name,
                                    func_name[5:],
                                    os.path.join(animpath, filename),
                                )

                        # add all functions to main anim list, names are "module.funcname" with "anim_" prefix removed
                        for func_name in mod_anims:
                            anims[f"{mod_name}.{func_name[5:]}"] = mod_anims[func_name]
                            log.trace(
                                "Animation '%s.%s' added",
                                mod_name,
                                func_name[5:],
                            )

                        log.debug(
                            "Loaded %d animations from '%s'",
                            len(mod_anims),
                            os.path.join(animpath, filename),
                        )

                else:
                    log.trace("Skipping file '%s'", os.path.join(animpath, filename))
        else:
            log.warn("Animation path '%s' is not a directory", animpath)

    # add utils to anims
    for func_name in anims:
        func_globals = t.cast(t.Dict[str, t.Any], anims[func_name].__globals__)  # type: ignore
        func_globals["log"] = logger.get_logger(f"led.anim.{func_name}")
        func_globals["Color"] = Color
        for util in utils:
            func_globals[util.__name__] = util

    return anims


##### Utility functions #####


def parse_color(
    array: baseArray,
    color: t.Optional[t.Union[t.Sequence[int], str, int]] = None,
    r: int = -1,
    g: int = -1,
    b: int = -1,
    w: int = -1,
    pixel: t.Optional[int] = None,
) -> t.Union[Color, None]:
    """
    Returns 24/32-bit color value

    Accepts
    - a color:
        color: can be ``[r, g, b, w]`` or ``#WWRRGGBB`` or ``0xWWRRGGBB``
    - component values
        r: red 0-255
        g: green
        b: blue
        w: white
    - pixel to get current color from:
        pixel: pixel index

    Returns:
        - ``Color`` instance if ``c`` can be parsed or sufficient components
          are provided for the channel count of the array, otherwise ``None``.
          If ``pixel`` is provided, any values of ``-1`` will use the current
          channel level for that pixel, otherwise ``0``.
    """
    pixel_color = Color(0, 0, 0, 0)

    if pixel is not None:
        pixel_color = array.getPixelColor(pixel)
    if pixel_color is None:
        return None

    if color is not None:
        # check if we got hex '#WWRRGGBB' or '0xWWRRGGBB'
        if isinstance(color, str):
            cs = color.strip("#")
            if cs.startswith("0x"):
                cs = cs[2:]
            cs = cs.rjust(8, "0")[-8:]
            try:
                ci = int.from_bytes(bytearray.fromhex(cs), byteorder="big")
            except:
                log.warn("Could not parse hex 'color' value 0x%04x", cs)
            else:
                # fmt: off
                r =  (ci >> 16) & 255
                g =  (ci >>  8) & 255
                b =   ci        & 255
                w = ((ci >> 24) & 255) if array.colors == 4 else 0
                # fmt: on
        # check if we got a list
        elif isinstance(color, Sequence):
            if len(color) >= array.colors:
                r = color[0]
                g = color[1]
                b = color[2]
                w = color[3] if array.colors == 4 else 0
        # unrecognized
        else:
            log.warn("Unrecognized 'color' value '%s'", color)

    if r > -1 or g > -1 or b > -1 or (array.colors == 4 and w > -1):
        return Color(
            r if r > -1 else pixel_color.r,
            g if g > -1 else pixel_color.g,
            b if b > -1 else pixel_color.b,
            w if w > -1 else pixel_color.w,
        )
    else:
        log.warn(
            "Must provide 'color' or at least one of 'red', 'green', 'blue', or 'white'"
        )

    return None


def parse_pixel(
    array: baseArray,
    p: t.Union[int, str, t.List[t.Union[int, str, t.Sequence[int]]], None],
) -> t.List[int]:
    """
    Parses ``p`` into a list of pixel indices, returns ``[]`` if unable.

    Accepts
        int: single pixel index
        str: string range of pixels. ex ``"2-7"``
        list:
            int: single pixel index
            str: string range of pixels. ex ``"2-7"``
            list: of ``[start, count]``
            Can mix and match any of the above in the list

    """
    pixels: t.List[int] = []
    if p is None:
        return pixels
    if isinstance(p, (int, str)):
        p = [p]

    for v in p:
        # singleton
        if isinstance(v, int):
            pixels.append(v)
        # range (str)
        elif isinstance(v, str):
            parts = v.split("-")
            if len(parts) == 2:
                try:
                    start = int(parts[0])
                    end = int(parts[1])
                except:
                    log.warn("Invalid pixel range '%s'", v)
                    continue  # skip on invalid range
                pixels.extend([i for i in range(start, end + 1)])
        # sequence of (index, count)
        elif isinstance(v, (list, tuple)) and len(t.cast(t.Sequence[int], v)) == 2:
            v = t.cast(t.Sequence[int], v)
            try:
                start = int(v[0])
                end = int(v[1])
            except:
                log.warn("Invalid pixel range %s", v)
                continue  # skip on invalid values
            pixels.extend([i for i in range(start, start + end)])
        # unrecognized
        else:
            log.warn("Unrecognized pixel reference '%s'", t.cast(t.Any, v))

    # remove any out-of-range indices
    if pixels:
        for i in range(len(pixels) - 1, -1, -1):
            if not array.count > pixels[i] >= 0:
                log.warn("Ignoring out of range pixel '%d'", pixels[i])
                pixels.pop(i)

    return pixels


##### Built-in Animations #####


def anim_on(array: baseArray, cancel: threading.Event, **kwargs: t.Any) -> None:
    """
    Turns on the array
    """
    for i in range(array.count):
        array.setPixel(i, 0xFFFFFFFF)
    array.show()


def anim_off(array: baseArray, cancel: threading.Event, **kwargs: t.Any) -> None:
    """
    Turns off the array
    """
    for i in range(array.count):
        array.setPixel(i, 0)
    array.show()


def anim_set_brightness(
    array: baseArray, cancel: threading.Event, **kwargs: t.Any
) -> None:
    """
    Sets the array brightness
    """
    brightness = kwargs.get("brightness", None)

    if brightness is None:
        log.warn("Missing argument 'brightness'")
        return

    array.setBrightness(int(brightness))
    array.show()


def anim_set_array(array: baseArray, cancel: threading.Event, **kwargs: t.Any) -> None:
    """
    Set the entire array color
    """
    c = kwargs.get("color", None)
    r = kwargs.get("red", -1)
    g = kwargs.get("green", -1)
    b = kwargs.get("blue", -1)
    w = kwargs.get("white", -1)

    color = parse_color(array, c, r, g, b, w)

    if color is not None:
        for i in range(array.count):
            array.setPixelColor(i, color)
        array.show()


def anim_set_pixel(array: baseArray, cancel: threading.Event, **kwargs: t.Any) -> None:
    """
    Set a pixel or range of pixels
    """
    p = kwargs.get("pixel", None)
    c = kwargs.get("color", None)
    r = kwargs.get("red", -1)
    g = kwargs.get("green", -1)
    b = kwargs.get("blue", -1)
    w = kwargs.get("white", -1)

    pixels = parse_pixel(array, p)

    for pixel in pixels:
        color = parse_color(array, c, r, g, b, w, pixel)
        if color is not None:
            array.setPixelColor(pixel, color)

    if pixels:
        array.show()


def anim_fade_on(array: baseArray, cancel: threading.Event, **kwargs: t.Any) -> None:
    """
    Fades on the array
    """
    array.anims["fade.pixel"](
        array,
        cancel,
        **{
            "pixel": [[0, array.count]],
            "color": 0xFFFFFFFF,
            "duration": kwargs.get("duration", 0),
        },
    )


def anim_fade_off(array: baseArray, cancel: threading.Event, **kwargs: t.Any) -> None:
    """
    Fades off the array
    """
    array.anims["fade.pixel"](
        array,
        cancel,
        **{
            "pixel": [[0, array.count]],
            "color": 0x0,
            "duration": kwargs.get("duration", 0),
        },
    )


def anim_fade_brightness(
    array: baseArray, cancel: threading.Event, **kwargs: t.Any
) -> None:
    """
    Fades the array brightness
    """
    bri_current = float(array.brightness)
    bri_end = float(int(kwargs.get("brightness", -1)))
    duration = float(kwargs.get("duration", 0))
    frame_time: float = t.cast(float, FRAME_MS)  # type: ignore - frame time, default minimum 16.7ms = ~60fps
    frame_overrun = 0.0
    frame_count = int(abs(bri_end - bri_current))

    if bri_end < 0:
        log.warn("Missing argument 'brightness'")
        return

    # constrain new brightness
    bri_end = 255.0 if bri_end > 255 else 0.0 if bri_end < 0 else bri_end

    # make sure we actually have something to do
    if frame_count == 0:
        return

    # calculate duration and step
    if duration <= 0:
        duration = round(frame_time * float(frame_count), 6)
        bri_step = 1.0 if bri_end - bri_current > 0 else -1.0
    # calculate step and frame
    else:
        duration = (
            t.cast(float, FRAME_MS) if duration < FRAME_MS else duration  # type: ignore
        )  # enforce minimum 1 frame duration
        frame_time = duration / frame_count
        # get frame time above minimum
        while frame_time < FRAME_MS:  # type:ignore
            frame_count -= 1
            frame_time = duration / frame_count

        duration = frame_time * frame_count
        frame_time = round(frame_time, 6)
        bri_step = round((bri_end - bri_current) / frame_count, 6)

    log.trace(
        "Calculated %d frames at %0.6f brightness per step with frame length %0.6fms "
        "(%0.2ffps) and duration %0.3fs",
        frame_count,
        bri_step,
        frame_time * 1000.0,
        1.0 / frame_time,
        duration,
    )

    # run interruptable fade loop
    while not cancel.is_set() and frame_count > 0:
        frame_start = time.perf_counter()
        bri_current += bri_step
        array.brightness = int(bri_current)
        array.show()
        frame_count -= 1
        frame_delta = time.perf_counter() - frame_start

        if frame_delta > frame_time:
            log.debug("Frame overrun of %0.2fms!", (frame_delta - frame_time) * 1000)
            frame_overrun += frame_delta - frame_time
            if frame_overrun > frame_time:
                frame_count -= 1
                bri_step = round((bri_end - bri_current) / frame_count, 6)
                frame_overrun -= frame_time
                log.warn("Animation is running too slowly, skipping 1 frame!")
                log.debug(
                    "Skipping 1 frame and adjusting brightness step to %0.6f to make up lost time!",
                    bri_step,
                )
        else:
            time.sleep(frame_time - frame_delta)

    # set end state if anim finished
    if frame_count <= 0:
        array.brightness = int(bri_end)
        array.show()


def anim_fade_array(array: baseArray, cancel: threading.Event, **kwargs: t.Any) -> None:
    """
    Fades the entire array color
    """
    kwargs["pixel"] = [[0, array.count]]
    array.anims["fade.pixel"](array, cancel, **kwargs)


def anim_fade_pixel(array: baseArray, cancel: threading.Event, **kwargs: t.Any) -> None:
    """
    Fades a pixel or range of pixels
    """
    p = kwargs.get("pixel", [])
    c = kwargs.get("color", None)
    r = kwargs.get("red", -1)
    g = kwargs.get("green", -1)
    b = kwargs.get("blue", -1)
    w = kwargs.get("white", -1)
    duration = float(kwargs.get("duration", 0))
    frame_time = t.cast(float, FRAME_MS)  # type: ignore - frame time, default minimum 16.7ms = ~60fps
    frame_overrun = 0.0
    pixels: t.Dict[int, t.Dict[str, float]] = {}

    # make sure we got a new color
    color = parse_color(array, c, r, g, b, w)
    if color is None:
        return

    # build pixels dicts
    for pixel in parse_pixel(array, p):
        pixel_color = array.getPixelColor(pixel)
        if pixel_color is not None:
            pixels[pixel] = {
                "r_curr": float(pixel_color.r),
                "g_curr": float(pixel_color.g),
                "b_curr": float(pixel_color.b),
                "w_curr": float(pixel_color.w),
                "r_end": float(color.r),
                "g_end": float(color.g),
                "b_end": float(color.b),
                "w_end": float(color.w),
            }
    if not pixels:
        return

    # get the biggest delta for every channel as starting frame_step
    frame_count = int(
        max(
            [abs(pixels[pixel]["r_end"] - pixels[pixel]["r_curr"]) for pixel in pixels]
            + [
                abs(pixels[pixel]["g_end"] - pixels[pixel]["g_curr"])
                for pixel in pixels
            ]
            + [
                abs(pixels[pixel]["b_end"] - pixels[pixel]["b_curr"])
                for pixel in pixels
            ]
            + [
                abs(pixels[pixel]["w_end"] - pixels[pixel]["w_curr"])
                for pixel in pixels
            ]
        )
    )

    # make sure we actually have something to do
    if frame_count == 0:
        return

    # calculate duration
    if duration <= 0:
        duration = round(frame_time * float(frame_count), 6)
    # calculate frame count and frame
    else:
        duration = (
            t.cast(float, FRAME_MS) if duration < FRAME_MS else duration  # type: ignore
        )  # enforce minimum 1 frame duration
        frame_time = duration / frame_count
        # get frame time above minimum
        while frame_time < FRAME_MS:  # type: ignore
            frame_count -= 1
            frame_time = duration / frame_count

        duration = frame_time * frame_count
        frame_time = round(frame_time, 6)

    # calculate step for each channel for each pixel
    for pixel in pixels:
        for channel in ["r", "g", "b", "w"]:
            pixels[pixel][f"{channel}_step"] = round(
                (pixels[pixel][f"{channel}_end"] - pixels[pixel][f"{channel}_curr"])
                / frame_count,
                6,
            )

    log.trace(
        "Calculated %d frames with frame length %0.6fms (%0.2ffps) and duration %0.3fs",
        frame_count,
        frame_time * 1000.0,
        1.0 / frame_time,
        duration,
    )

    # run interruptable fade loop
    while not cancel.is_set() and frame_count > 0:
        frame_start = time.perf_counter()
        for pixel in pixels:
            for channel in ["r", "g", "b", "w"]:
                pixels[pixel][f"{channel}_curr"] += pixels[pixel][f"{channel}_step"]
            array.setPixelColorRGB(
                pixel,
                int(pixels[pixel]["r_curr"]),
                int(pixels[pixel]["g_curr"]),
                int(pixels[pixel]["b_curr"]),
                int(pixels[pixel]["w_curr"]),
            )
        array.show()
        frame_count -= 1
        frame_delta = time.perf_counter() - frame_start

        if frame_delta > frame_time:
            log.debug("Frame overrun of %0.2fms!", (frame_delta - frame_time) * 1000)
            frame_overrun += frame_delta - frame_time
            if frame_overrun > frame_time:
                frame_count -= 1
                frame_overrun -= frame_time
                log.warn("Animation is running too slowly, skipping 1 frame!")
                log.debug(
                    "Skipping 1 frame and adjusting step values to make up lost time!"
                )
                # recalculate steps
                for pixel in pixels:
                    for channel in ["r", "g", "b", "w"]:
                        pixels[pixel][f"{channel}_step"] = round(
                            (
                                pixels[pixel][f"{channel}_end"]
                                - pixels[pixel][f"{channel}_curr"]
                            )
                            / frame_count,
                            6,
                        )
        else:
            time.sleep(frame_time - frame_delta)

    # set end state if anim finished
    if frame_count <= 0:
        for pixel in pixels:
            array.setPixelColor(pixel, color)
        array.show()


def anim_testorder(array: baseArray, cancel: threading.Event, **kwargs: t.Any) -> None:
    """
    Set color order to RGB(W) and run this animation.
    If you see 1 red, 2 green, and 3 blue is RGB, otherwise the number of LEDs
    of a particular color are the position of that colour in the order.
    """
    array.setPixelColorRGB(0, 255, 0, 0, 0)
    array.setPixelColorRGB(1, 0, 255, 0, 0)
    array.setPixelColorRGB(2, 0, 255, 0, 0)
    array.setPixelColorRGB(3, 0, 0, 255, 0)
    array.setPixelColorRGB(4, 0, 0, 255, 0)
    array.setPixelColorRGB(5, 0, 0, 255, 0)
    array.setPixelColorRGB(6, 0, 0, 0, 255)
    array.setPixelColorRGB(7, 0, 0, 0, 255)
    array.setPixelColorRGB(8, 0, 0, 0, 255)
    array.setPixelColorRGB(9, 0, 0, 0, 255)
    array.show()


def anim_testarray(array: baseArray, cancel: threading.Event, **kwargs: t.Any) -> None:
    """
    Draw a rainbow that uniformly distributes itself across all pixels then
    fade white channel up then down.
    """

    def wheel(pos: int) -> t.Tuple[int, int, int]:
        """Generate rainbow colors across 0-255 positions."""
        if pos < 85:
            return (pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return (255 - pos * 3, 0, pos * 3)
        else:
            pos -= 170
            return (0, pos * 3, 255 - pos * 3)

    # save initial brightness
    init_brightness = array.brightness

    # rainbow spinner/slider
    j = 0
    while not cancel.is_set() and j < 256:
        array.brightness = (j * 8) if j < 64 else (2048 - j * 8)
        for i in range(array.count):
            array.setPixelColorRGB(i, *wheel((int(i * 256 / array.count) + j) & 255))
        array.show()
        time.sleep(0.01)
        j += 1

    # fade white up then down
    j, step = 1, 1
    array.brightness = 255
    while not cancel.is_set() and j > 0:
        for i in range(array.count):
            array.setPixelColorRGB(i, 0, 0, 0, j)
        array.show()
        time.sleep(0.01)
        j += step
        if j > 32:
            step = -1

    array.anims["off"](array, cancel)
    array.brightness = init_brightness
