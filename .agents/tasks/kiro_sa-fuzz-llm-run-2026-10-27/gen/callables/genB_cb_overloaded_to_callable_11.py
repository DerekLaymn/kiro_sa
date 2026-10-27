from collections.abc import Callable
from typing import overload, reveal_type


@overload
def f(x: int) -> int: ...
@overload
def f(x: str) -> str: ...
def f(x: int | str) -> int | str:
    return x


a: Callable[[int], int] = f  # OK
b: Callable[[int], str] = f  # error
c: Callable[[int | str], int | str] = f  # error (no overload takes union)
reveal_type(a)
print(a(1), b if False else 0, c if False else 0)
