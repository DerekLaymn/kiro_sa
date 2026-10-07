# area: overloads
# explores: overloaded __getitem__ (int vs slice) on a generic Sequence subclass; inherited mixin methods
from collections.abc import Iterator, Sequence
from typing import overload, reveal_type


class Ring[T](Sequence[T]):
    def __init__(self, *items: T) -> None:
        self._items = list(items)

    @overload
    def __getitem__(self, i: int) -> T: ...
    @overload
    def __getitem__(self, i: slice) -> "Ring[T]": ...
    def __getitem__(self, i: int | slice) -> "T | Ring[T]":
        if isinstance(i, slice):
            return Ring(*self._items[i])
        return self._items[i % len(self._items)]

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[T]:
        return iter(self._items)


r = Ring(1, 2, 3)
reveal_type(r[5])  # int
reveal_type(r[1:])  # Ring[int]
reveal_type(list(r))  # list[int]
reveal_type(r.index(2))  # int (from Sequence)
print(r[5], list(r[1:]), 2 in r, r.index(2))
try:
    r["x"]  # expect-error: no overload accepts str
except TypeError as exc:
    print("runtime:", exc)
