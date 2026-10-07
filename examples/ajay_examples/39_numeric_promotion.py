# area: gradual_any (special types)
# explores: int -> float -> complex promotion, isinstance(x, int) on a float parameter, builtin numeric
# return types (pow with negative exponent, round, divmod), list invariance despite promotion
import math
from typing import reveal_type


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs)


def describe(x: float) -> str:
    if isinstance(x, int):
        reveal_type(x)  # int: a `float` annotation also admits int
        return "int"
    reveal_type(x)  # float
    return "float"


def mag(z: complex) -> float:
    return abs(z)


reveal_type(1 + 2.0)  # float
reveal_type(2**-1)  # float
reveal_type(2**3)  # int
reveal_type(divmod(7, 2))  # tuple[int, int]
reveal_type(round(2.5))  # int
reveal_type(round(2.567, 1))  # float
reveal_type(math.floor(2.5))  # int
ints: list[int] = [1, 2]
print(mean([1.0, 2]), describe(3), describe(3.5), mag(3), 7 / 2, round(2.5))
print(mean(ints))  # expect-error: list[int] is not list[float] (invariance); works at runtime
