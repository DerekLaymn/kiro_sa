# area: typevartuple_unpack
# explores: TypeVarTuple in a generic class, prepending a dimension, *Ts in Callable parameters
from collections.abc import Callable
from typing import reveal_type


class Array[*Shape]:
    def __init__(self, *dims: *Shape) -> None:
        self.dims = dims

    def add_batch(self) -> "Array[int, *Shape]":
        return Array(1, *self.dims)


def call_with[*Ts, R](f: Callable[[*Ts], R], *args: *Ts) -> R:
    return f(*args)


def area(w: int, h: float) -> float:
    return w * h


a = Array(3, "x")
reveal_type(a)  # Array[int, str]
reveal_type(a.add_batch())  # Array[int, int, str]
reveal_type(call_with(area, 2, 1.5))  # float
print(a.dims, call_with(area, 2, 1.5))
try:
    call_with(area, "2", 1.5)  # expect-error: str is not int
except TypeError as exc:
    print("runtime:", exc)
