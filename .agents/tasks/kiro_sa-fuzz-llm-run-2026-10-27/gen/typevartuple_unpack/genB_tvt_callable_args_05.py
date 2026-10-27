import sys
from collections.abc import Callable
from typing import reveal_type


def call_with[*Ts, R](f: Callable[[*Ts], R], *args: *Ts) -> R:
    return f(*args)


def add(a: int, b: int) -> int:
    return a + b


reveal_type(call_with(add, 1, 2))
print(call_with(add, 1, 2))
if len("") > 99:
    call_with(add, 1, "x")  # error (never executed)
    call_with(add, 1)  # error (never executed)
