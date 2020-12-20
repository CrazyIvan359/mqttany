"""
****************
Core GPIO Boards
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

__all__ = ["get_board"]

import typing as t

from adafruit_platformdetect import Detector
from adafruit_platformdetect.constants.boards import GENERIC_LINUX_PC

from . import odroid, opi, rpi
from .base import Board


class Unknown(Board):
    def __init__(self) -> None:
        self._id = "UNRECOGNIZED"
        self._chips.append(999)  # dummy


class Generic(Board):
    def __init__(self) -> None:
        self._id = GENERIC_LINUX_PC
        self._chips.append(999)  # dummy


def get_board() -> Board:
    all_boards: t.Dict[str, t.Type[Board]] = {GENERIC_LINUX_PC: Generic}
    all_boards.update(rpi.SUPPORTED_BOARDS)
    all_boards.update(odroid.SUPPORTED_BOARDS)
    all_boards.update(opi.SUPPORTED_BOARDS)
    return all_boards.get(Detector().board.id, Unknown)()
