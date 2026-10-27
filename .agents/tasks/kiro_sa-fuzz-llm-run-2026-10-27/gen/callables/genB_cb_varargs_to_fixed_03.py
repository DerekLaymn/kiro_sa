from collections.abc import Callable
from typing import reveal_type


def v(*args: int) -> int:
    return sum(args)


def two(a: int, b: int) -> int:
    return a + b


x: Callable[[int, int], int] = v
y: Callable[[int, int, int], int] = two  # error
z: Callable[..., int] = two
reveal_type(x)
print(x(1, 2), z(1, 2), y if False else 0)
