class PixelStrip(object):
    def __init__(
        self,
        num: int,
        pin: int,
        freq_hz: int = ...,
        dma: int = ...,
        invert: bool = ...,
        brightness: int = ...,
        channel: int = ...,
        strip_type: int = ...,
        gamma: int = ...,
    ) -> None:
        ...

    def begin(self) -> None:
        ...

    def show(self) -> None:
        ...

    def setPixelColor(self, n: int, color: int) -> None:
        ...

    def setPixelColorRGB(
        self, n: int, red: int, green: int, blue: int, white: int = ...
    ) -> None:
        ...

    def getBrightness(self) -> int:
        ...

    def setBrightness(self, brightness: int) -> None:
        ...

    def getPixelColor(self, n: int) -> int:
        ...
