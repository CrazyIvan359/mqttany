import typing as t


class Output:
    multicast: bool
    destination: str

    @property
    def dmx_data(self) -> t.Sequence[int]:
        ...

    @dmx_data.setter
    def dmx_data(self, dmx_data: t.Sequence[int]) -> None:
        ...
