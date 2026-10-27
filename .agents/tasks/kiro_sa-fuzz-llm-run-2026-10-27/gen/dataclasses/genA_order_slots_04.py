from typing import reveal_type  # noqa

from dataclasses import dataclass


@dataclass(order=True, slots=True)
class V:
    major: int
    minor: int = 0


def cmp(a: V, b: V) -> bool:
    return a < b


@dataclass(order=False)
class W:
    n: int


def try_w(a: W, b: W) -> bool:
    return a < b  # no __lt__


v = V(1, 2)
reveal_type(v.__slots__)
reveal_type(cmp(v, V(2)))
try:
    print(try_w(W(1), W(2)))
except TypeError:
    print("TypeError")
