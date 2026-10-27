from collections.abc import Callable
from typing import reveal_type


def f(x: int, y: int = 1) -> int:
    return x + y


a: Callable[[int], int] = f
b: Callable[[int, int], int] = f
c: Callable[[], int] = f  # error
reveal_type(a)
print(a(1), b(1, 2), c if False else 0)
