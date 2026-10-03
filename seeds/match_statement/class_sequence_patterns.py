# area: match_statement
# hypothesis: class patterns with __match_args__, sequence patterns of different lengths,
# and exhaustiveness checked with assert_never.
# spec: typing spec doesn't cover match deeply, but PEP 634/636 semantics are deterministic and
# both checkers claim support; CPython is the oracle here.
from dataclasses import dataclass
from typing import assert_never, reveal_type


@dataclass
class Point:
    x: int
    y: int


@dataclass
class Circle:
    center: Point
    r: float


def describe(s: Point | Circle | tuple[int, int] | tuple[int, int, int]) -> str:
    match s:
        case Point(0, y):
            reveal_type(y)  # int
            return "on y axis"
        case Point(x=x):
            return f"point {x}"
        case Circle(Point(x, y), r):
            reveal_type(r)  # float
            return f"circle {x},{y} r={r}"
        case (a, b):
            reveal_type(s)  # tuple[int, int]
            return f"2-tuple {a + b}"
        case (a, b, c):
            return f"3-tuple {a + b + c}"
        case _:
            assert_never(s)


for v in [Point(0, 1), Point(2, 3), Circle(Point(0, 0), 1.5), (1, 2), (1, 2, 3)]:
    print(describe(v))
