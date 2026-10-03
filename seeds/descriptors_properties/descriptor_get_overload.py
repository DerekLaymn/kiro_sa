# area: descriptors_properties
# hypothesis: descriptor __get__ overloaded on instance=None (class access) vs instance access,
# and __set__ value type checked on assignment, including through a subclass.
# spec: typing spec doesn't define descriptors fully; data model + both checkers' docs are the reference.
from typing import Any, Self, overload, reveal_type


class Field[T]:
    def __init__(self, default: T) -> None:
        self.default = default
        self.name = ""

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = "_" + name

    @overload
    def __get__(self, obj: None, owner: type) -> Self: ...
    @overload
    def __get__(self, obj: object, owner: type) -> T: ...
    def __get__(self, obj: object | None, owner: type) -> Any:
        if obj is None:
            return self
        return getattr(obj, self.name, self.default)

    def __set__(self, obj: object, value: T) -> None:
        setattr(obj, self.name, value)


class Config:
    port = Field(8080)
    host = Field("localhost")


class SubConfig(Config):
    pass


c = SubConfig()
reveal_type(Config.port)  # Field[int]
reveal_type(c.port)  # int
c.port = 9000
print(c.port, c.host, Config.port.name)
c.port = "9000"  # expect-error: __set__ expects int
