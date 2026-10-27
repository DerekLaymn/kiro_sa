from dataclasses import dataclass, field
from typing import reveal_type


@dataclass
class P:
    x: int
    y: int = 0
    tag: str = field(default="", kw_only=True)


@dataclass
class Q:
    a: P | None
    b: list[int]


def f(o: P | Q | int) -> int:
    match o:
        case P(x, y):
            reveal_type(x)
            reveal_type(y)
            return x + y
        case Q(P(x=xx), [first, *rest]):
            reveal_type(xx)
            reveal_type(first)
            reveal_type(rest)
            return xx + first
        case Q(None, _):
            reveal_type(o)
            return -1
        case _:
            reveal_type(o)
            return 0


print(f(P(1, 2)), f(Q(P(5), [1, 2])), f(Q(None, [])), f(Q(P(1), [])), f(3))
