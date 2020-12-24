import typing as t

class mproperty(object):
    __slots__ = "fget", "fset", "fdel", "doc"
    def __init__(
        self,
        fget: t.Optional[t.Callable[[object], t.Any]] = ...,
        fset: t.Optional[t.Callable[[object, t.Any], None]] = ...,
        fdel: t.Optional[t.Callable[[object], None]] = ...,
        doc: t.Optional[t.Callable[[object], None]] = ...,
    ) -> None: ...
    def getter(self, get: t.Callable[[object], t.Any]) -> mproperty: ...
    def setter(self, set: t.Callable[[object, t.Any], None]) -> mproperty: ...
    def deleter(self, delete: t.Callable[[object], None]) -> mproperty: ...
