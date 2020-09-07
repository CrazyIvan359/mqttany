"""
**************
LED Animations
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

__all__ = ["load_animations"]

import time
import os
import inspect
import importlib.util

import logger
from logger import log_traceback

from modules.led.common import log, CONFIG, CONF_KEY_ANIM_DIR, CONF_KEY_ANIM_FPS

log = logger.get_module_logger("led.anim")

DEFAULT_PATH = "/etc/mqttany/led-anim"


def load_animations():
    """
    Loads custom animations and returns a dictionary of them and the built-ins.
    """
    anims = {  # built-in animations
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
    utils = [parse_color, parse_pixel]  # utility functions

    log.debug("Loading animations")

    animpaths = [DEFAULT_PATH] if os.path.isdir(DEFAULT_PATH) else []
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
                    mod_anims = []

                    try:
                        spec = importlib.util.spec_from_file_location("*", filename)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                    except:
                        log.error(
                            "An error occured while importing animation file '%s'",
                            filename,
                        )
                        log_traceback(log)
                        log.error("Animation file '%s' was not loaded", filename)
                    else:
                        log.trace(
                            "Animation file '%s' imported successfully", module.__name__
                        )

                    # get all functions in module that start with "anim_" and don't have a conflicting name
                    mod_anims = dict(inspect.getmembers(module, inspect.isfunction))
                    for func in [key for key in mod_anims]:
                        if not func.startswith("anim_"):
                            mod_anims.pop(func, None)
                            log.trace(
                                "Ignoring function '%s' in '%s' as it does not start with 'anim_",
                                func,
                                os.path.join(animpath, filename),
                            )
                        elif not callable(func):
                            mod_anims.pop(func, None)
                            log.warn(
                                "Ignoring animation '%s.%s' in '%s' as it is not callable",
                                module.__name__,
                                func[5:],
                                os.path.join(animpath, filename),
                            )
                        elif f"{module.__name__}.{func[5:]}" in mod_anims:
                            mod_anims.pop(func, None)
                            log.warn(
                                "Duplicate animation '%s.%s' in '%s' is being ignored",
                                module.__name__,
                                func[5:],
                                os.path.join(animpath, filename),
                            )

                    # add all functions to main anim list, names are "module.funcname" with "anim_" prefix removed
                    for func in mod_anims:
                        anims[f"{module.__name__}.{func[5:]}"] = mod_anims[func]
                        log.trace("Animation '%s.%s' added", module.__name__, func[5:])

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
    for func in anims:
        anims[func].__globals__["FRAME_MS"] = round(1.0 / CONFIG[CONF_KEY_ANIM_FPS], 5)
        anims[func].__globals__["log"] = logger.get_module_logger(f"led.anim.{func}")
        for util in utils:
            anims[func].__globals__[util.__name__] = util

    return anims


##### Utility functions #####


def parse_color(array, c=None, r=-1, g=-1, b=-1, w=-1, pixel=None):
    """
    Returns 24/32-bit color value

    Accepts
    - a color:
        c: can be ``[r, g, b, w]`` or ``#WWRRGGBB`` or ``0xWWRRGGBB``
    - component values
        r: red 0-255
        g: green
        b: blue
        w: white
    - pixel to get current color from:
        pixel: pixel index

    Returns:
        - 24/32-bit color value if ``c`` can be parsed or sufficient components
          are provided for the channel count of the array, otherwise ``None``.
          If ``pixel`` is provided, any values of ``-1`` will use the current
          channel level for that pixel, otherwise ``0``.
    """
    color = None
    pixel_color = 0

    if pixel is not None:
        pixel_color = array.getPixelColor(pixel)

    if c is not None:
        # check if we got a list
        if isinstance(c, list):
            if len(c) >= array.colors:
                r = c[0]
                g = c[1]
                b = c[2]
                w = c[3] if array.colors == 4 else 0
        # check if we got hex '#WWRRGGBB' or '0xWWRRGGBB'
        elif isinstance(c, str):
            c = c.strip("#")
            if c.startswith("0x"):
                c = c[2:]
            c = c.rjust(8, "0")[-8:]
            try:
                c = int.from_bytes(bytearray.fromhex(c), byteorder="big")
            except:
                log.warn("Could not parse hex 'color' value 0x%04x", c)
            else:
                # fmt: off
                r =  (c >> 16) & 255
                g =  (c >>  8) & 255
                b =   c        & 255
                w = ((c >> 24) & 255) if array.colors == 4 else 0
                # fmt: on
        # unrecognized
        else:
            log.warn("Unrecognized 'color' value '%s'", c)

    if r > -1 or g > -1 or b > -1 or (array.colors == 4 and w > -1):
        # fmt: off
        color  = ((r if r > -1 else (pixel_color >> 16)) & 255) << 16
        color += ((g if g > -1 else (pixel_color >>  8)) & 255) <<  8
        color +=  (b if b > -1 else (pixel_color      )) & 255
        color += ((w if w > -1 else (pixel_color >> 24)) & 255) << 24
        # fmt: on
    else:
        log.warn(
            "Must provide 'color' or at least one of 'red', 'green', 'blue', or 'white'"
        )

    return color


def parse_pixel(array, p):
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
    pixels = []
    if isinstance(p, (int, str, list)):
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
                        parts[0] = int(parts[0])
                        parts[1] = int(parts[1])
                    except:
                        log.warn("Invalid pixel range '%s'", v)
                        continue  # skip on invalid range
                    pixels.extend([i for i in range(parts[0], parts[1] + 1)])
            # list of (index, count)
            elif isinstance(v, list) and len(v) == 2:
                try:
                    v[0] = int(v[0])
                    v[1] = int(v[1])
                except:
                    log.warn("Invalid pixel range %s", v)
                    continue  # skip on invalid values
                pixels.extend([i for i in range(v[0], v[0] + v[1])])
            # unrecognized
            else:
                log.warn("Unrecognized pixel reference '%s'", v)

    # remove any out-of-range indices
    if pixels:
        for i in range(len(pixels) - 1, -1, -1):
            if not array.count > pixels[i] >= 0:
                log.warn("Ignoring out of range pixel '%d'", pixels[i])
                pixels.pop(i)

    return pixels


##### Built-in Animations #####


def anim_on(array, cancel, **kwargs):
    """
    Turns on the array
    """
    for i in range(array.count):
        array.setPixelColor(i, 0xFFFFFFFF)
    array.show()


def anim_off(array, cancel, **kwargs):
    """
    Turns off the array
    """
    for i in range(array.count):
        array.setPixelColor(i, 0)
    array.show()


def anim_set_brightness(array, cancel, **kwargs):
    """
    Sets the array brightness
    """
    brightness = kwargs.get("brightness", None)

    if brightness is None:
        log.warn("Missing argument 'brightness'")
        return

    array.setBrightness(int(brightness))
    array.show()


def anim_set_array(array, cancel, **kwargs):
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


def anim_set_pixel(array, cancel, **kwargs):
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

    # make sure we have pixels and a valid color
    if pixels and parse_color(array, c, r, g, b, w) is not None:
        for pixel in pixels:
            array.setPixelColor(pixel, parse_color(array, c, r, g, b, w, pixel))

        array.show()


def anim_fade_on(array, cancel, **kwargs):
    """
    Fades on the array
    """
    array.anims["fade.pixel"](
        array,
        cancel,
        **{
            "pixel": [[0, array.count]],
            "color": "0xFFFFFFFF",
            "duration": kwargs.get("duration", 0),
        },
    )


def anim_fade_off(array, cancel, **kwargs):
    """
    Fades off the array
    """
    array.anims["fade.pixel"](
        array,
        cancel,
        **{
            "pixel": [[0, array.count]],
            "color": "0x0",
            "duration": kwargs.get("duration", 0),
        },
    )


def anim_fade_brightness(array, cancel, **kwargs):
    """
    Fades the array brightness
    """
    bri_current = float(array.brightness)
    bri_end = float(int(kwargs.get("brightness", -1)))
    duration = float(kwargs.get("duration", 0))
    frame_time = FRAME_MS  # frame time, default minimum 16.7ms = ~60fps
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
            FRAME_MS if duration < FRAME_MS else duration
        )  # enforce minimum 1 frame duration
        frame_time = duration / frame_count
        # get frame time above minimum
        while frame_time < FRAME_MS:
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
        array.brightness = bri_current
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
        array.brightness = bri_end
        array.show()


def anim_fade_array(array, cancel, **kwargs):
    """
    Fades the entire array color
    """
    kwargs["pixel"] = [[0, array.count]]
    array.anims["fade.pixel"](array, cancel, **kwargs)


def anim_fade_pixel(array, cancel, **kwargs):
    """
    Fades a pixel or range of pixels
    """
    p = kwargs.get("pixel", None)
    c = kwargs.get("color", None)
    r = kwargs.get("red", -1)
    g = kwargs.get("green", -1)
    b = kwargs.get("blue", -1)
    w = kwargs.get("white", -1)
    duration = float(kwargs.get("duration", 0))
    frame_time = FRAME_MS  # frame time, default minimum 16.7ms = ~60fps
    frame_overrun = 0.0
    pixels = {}

    # make sure we got a new color
    color = parse_color(array, c, r, g, b, w)
    if color is None:
        return

    # build pixels dicts
    for pixel in parse_pixel(array, p):
        pixel_color = array.getPixelColor(pixel)
        pixels[pixel] = {
            # fmt: off
            "r_curr": float(pixel_color >> 16 & 255),
            "g_curr": float(pixel_color >>  8 & 255),
            "b_curr": float(pixel_color       & 255),
            "w_curr": float(pixel_color >> 24 & 255),
            "r_end": float(color >> 16 & 255),
            "g_end": float(color >>  8 & 255),
            "b_end": float(color       & 255),
            "w_end": float(color >> 24 & 255),
            # fmt: on
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
            FRAME_MS if duration < FRAME_MS else duration
        )  # enforce minimum 1 frame duration
        frame_time = duration / frame_count
        # get frame time above minimum
        while frame_time < FRAME_MS:
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
                pixels[pixel]["r_curr"],
                pixels[pixel]["g_curr"],
                pixels[pixel]["b_curr"],
                pixels[pixel]["w_curr"],
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


def anim_testorder(array, cancel, **kwargs):
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


def anim_testarray(array, cancel, **kwargs):
    """
    Draw a rainbow that uniformly distributes itself across all pixels then
    fade white channel up then down.
    """

    def wheel(pos):
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
