from collections.abc import Mapping, Sequence
from typing import reveal_type


def f(x: int | Sequence[int] | Mapping[str, int]) -> int:
    if isinstance(x, Mapping):
        reveal_type(x)
        return sum(x.values())
    if isinstance(x, Sequence):
        reveal_type(x)
        return sum(x)
    reveal_type(x)
    return x


def g(x: list[int] | str) -> int:
    if isinstance(x, Sequence):
        reveal_type(x)
        return len(x)
    reveal_type(x)
    return 0


def h(x: bytes | str | list[str]) -> int:
    if isinstance(x, (str, bytes)):
        reveal_type(x)
        return len(x)
    reveal_type(x)
    return len(x[0])


print(f(1), f([1, 2]), f({"a": 5}), g([1]), g("ab"), h(b"a"), h(["xy"]))
