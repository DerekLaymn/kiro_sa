# area: tuples_unpacking
# explores: generic NamedTuple (3.11+), unpacking, _replace, solving T from mixed arguments
from typing import Generic, NamedTuple, TypeVar, reveal_type

T = TypeVar("T")


class Pair(NamedTuple, Generic[T]):
    first: T
    second: T

    def swap(self) -> "Pair[T]":
        return Pair(self.second, self.first)


p = Pair(1, 2)
reveal_type(p)  # Pair[int]
reveal_type(p.swap().first)  # int
a, b = p
reveal_type(a)  # int
reveal_type(p._replace(first=5))  # Pair[int]
mixed = Pair(1, "y")
reveal_type(mixed)  # Pair[int | str] (or Pair[object])
print(p, p.swap(), mixed[1], p._replace(first=5))
