"""
*********
Core GPIO
*********

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

__all__ = [
    "init",
    "board",
    "board_ids",
    "Mode",
    "PinMode",
    "PinBias",
    "PinEdge",
    "PinAlternate",
]

import os
import adafruit_platformdetect
from adafruit_platformdetect.constants import boards as board_ids

from . import common
from .common import log, Mode, PinMode, PinBias, PinEdge, PinAlternate
from .boards import get_board, Unknown

board = get_board()
common.cdev = os.access(
    f"/dev/gpiochip{board.chips[0]}", os.F_OK | os.R_OK | os.W_OK, effective_ids=True
)
common.sysfs = os.access(
    "/sys/class/gpio/export", os.F_OK | os.W_OK, effective_ids=True
)


def init() -> None:
    if isinstance(board, Unknown):
        log.error("Unsupported board: %s", adafruit_platformdetect.Detector().board.id)
    elif board.id == board_ids.GENERIC_LINUX_PC:
        log.info("Detected board: %s", board.id)
        log.warn("This device does not support GPIO pins")
    else:
        log.info("Detected board: %s", board.id)

        if common.cdev:
            log.debug("Detected GPIO character device")
        elif os.access(f"/dev/gpiochip{board.chips[0]}", os.F_OK, effective_ids=True):
            log.warn(
                "Detected GPIO character device but this account (%s) does not have R/W "
                "permissions",
                os.getlogin(),
            )
            log.warn(
                "Read/Write access is required on the following files: %s",
                [f"/dev/gpiochip{chip}" for chip in board.chips],
            )
            log.warn("Attempting to fall back to sysfs")
            if common.sysfs:
                log.debug("Falling back to sysfs")
            elif os.access("/sys/class/gpio/export", os.F_OK, effective_ids=True):
                log.warn(
                    "Detected sysfs GPIO but this account (%s) does not have R/W "
                    "permissions",
                    os.getlogin(),
                )
                log.warn(
                    "Read/Write access is required on the following directory: "
                    "'/sys/class/gpio/export'"
                )

        else:
            if common.sysfs:
                log.debug("Detected sysfs GPIO interface")
            elif os.access("/sys/class/gpio/export", os.F_OK, effective_ids=True):
                log.warn(
                    "Detected sysfs GPIO but this account (%s) does not have R/W "
                    "permissions",
                    os.getlogin(),
                )
                log.warn(
                    "Read/Write access is required on the following directory: "
                    "'/sys/class/gpio/export'"
                )

        if not common.cdev and not common.sysfs:
            log.warn("No GPIO interface is available, some features may not work")
