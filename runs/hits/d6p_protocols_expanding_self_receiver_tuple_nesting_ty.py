# area: protocols
# hypothesis: ty overflows its stack when a plain class is assigned to a protocol whose method annotates self as Stream[tuple[Stream[T]]], because each receiver check needs a deeper receiver type, while mypy and pyright accept it.
# origin: runs/day6/parents/A_ty_crash/d4v_protocols_expanding_self_receiver.py
# area: protocols
# hypothesis: ty overflows its stack when a plain class is assigned to a protocol whose method annotates self as Stream[tuple[Stream[T]]], because each receiver check needs a deeper receiver type; mypy and pyright accept it.
# features: protocol, self_annotation, recursive_receiver, tuple_nesting, generic_impl
from typing import Protocol, reveal_type


class Stream[T](Protocol):
    def flatten(self: "Stream[tuple[Stream[T]]]") -> int: ...


class Impl[T]:
    def __init__(self, items: T) -> None:
        self.items = items

    def flatten(self) -> int:
        return 1


x: Stream[int] = Impl(3)
reveal_type(x)
print(Impl(3).flatten(), x is not None)
