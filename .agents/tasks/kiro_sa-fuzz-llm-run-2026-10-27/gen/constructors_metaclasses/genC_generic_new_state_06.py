from typing import Generic, TypeVar, reveal_type

T = TypeVar("T")


class Interned(Generic[T]):
    _cache: dict[object, "Interned"] = {}

    def __new__(cls, value: T) -> "Interned[T]":
        key = (cls, value)
        if key not in cls._cache:
            inst = super().__new__(cls)
            inst.value = value
            cls._cache[key] = inst
        return cls._cache[key]

    def __init__(self, value: T) -> None:
        self.value = value


a = Interned(1)
b = Interned(1)
reveal_type(a)
reveal_type(a.value)
print(a is b, a.value)
c = Interned("s")
reveal_type(c)
