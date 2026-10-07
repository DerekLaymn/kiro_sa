# area: constructors_metaclasses
# explores: __init_subclass__ keyword arguments in class statements; custom __class_getitem__
from typing import ClassVar, reveal_type


class Plugin:
    registry: ClassVar[dict[object, type["Plugin"]]] = {}

    def __init_subclass__(cls, *, name: str, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        Plugin.registry[name] = cls


class Csv(Plugin, name="csv"):
    pass


class Weird(Plugin, name=3):  # expect-error: name must be str (fine at runtime)
    pass


try:
    class NoName(Plugin):  # expect-error: missing required keyword `name`
        pass
except TypeError as exc:
    print("runtime:", exc)


class Matrix:
    def __class_getitem__(cls, size: int) -> str:
        return f"Matrix of size {size}"


reveal_type(Plugin.registry)
reveal_type(Matrix[3])  # str
print(sorted(map(str, Plugin.registry)), Matrix[3])
