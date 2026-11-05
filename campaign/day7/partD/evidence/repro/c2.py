# area: descriptors_properties
# hypothesis: A generic descriptor whose __get__ is decorated by a body-level function without self keeps its type parameter through class-level access, so Box[int] and Box[str] should yield list[int] and list[str].
# origin: runs/day7/parents/P_pyright/d3p_descriptors_decorated_get.py
# area: descriptors_properties
# hypothesis: A generic descriptor whose __get__ is decorated by a body-level function without self keeps its type parameter through class-level access, so Box[int] and Box[str] should yield list[int] and list[str].
from typing import Generic, TypeVar, reveal_type

T = TypeVar('T')


class Box(Generic[T]):
    def keep(fn):
        return fn

    def __init__(self, item: T) -> None:
        self.item = item

    @keep
    def __get__(self, obj: object, owner: type | None = None) -> list[T]:
        return [self.item]


class Host:
    ints = Box(7)
    names = Box('n')


h = Host()
reveal_type(h.ints)  # list[int]
reveal_type(h.names)  # list[str]
reveal_type(Box.__get__(Box(1), None, Host))  # list[int]
print(h.ints, h.names, Box.__get__(Box(2.5), None, Host))
