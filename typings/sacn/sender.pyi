import typing as t

from sacn.sending.output import Output

class sACNsender:
    def __init__(
        self,
        bind_address: str = ...,
        bind_port: int = ...,
        source_name: str = ...,
        cid: t.Tuple[
            int,
            int,
            int,
            int,
            int,
            int,
            int,
            int,
            int,
            int,
            int,
            int,
            int,
            int,
            int,
            int,
        ] = ...,
        fps: int = ...,
        universeDiscovery: bool = ...,
        sync_universe: int = ...,
    ) -> None: ...
    @property
    def manual_flush(self) -> bool: ...
    @manual_flush.setter
    def manual_flush(self, manual_flush: bool) -> None: ...
    def flush(self, universes: t.List[int] = ...) -> None: ...
    def activate_output(self, universe: int) -> None: ...
    def deactivate_output(self, universe: int) -> None: ...
    def get_active_outputs(self) -> t.Tuple[int]: ...
    def __getitem__(self, item: int) -> Output: ...
    def start(
        self, bind_address: str = ..., bind_port: int = ..., fps: int = ...
    ) -> None: ...
    def stop(self) -> None: ...
