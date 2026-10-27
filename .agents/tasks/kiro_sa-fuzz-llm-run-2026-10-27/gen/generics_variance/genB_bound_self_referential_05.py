import sys
from typing import Protocol, reveal_type


class Cmp(Protocol):
    def __lt__(self, other: "Cmp", /) -> bool: ...


def mx[T: Cmp](a: T, b: T) -> T:
    return b if a < b else a


reveal_type(mx(1, 2))
reveal_type(mx("a", "b"))
reveal_type(mx(1, 2.5))
print(mx(1, 2), mx("a", "b"), mx(1, 2.5))
if len("") > 99:
    mx(object(), object())  # error: bound violation (never executed)
