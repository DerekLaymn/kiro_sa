from typing import reveal_type  # noqa

from dataclasses import dataclass, fields, asdict, astuple


@dataclass(match_args=False)
class A:
    x: int
    y: int


@dataclass
class B:
    x: int
    y: int


def m(o: A | B) -> int:
    match o:
        case B(x, y):
            return x + y
        case A(x=x):
            return x


def go() -> None:
    reveal_type(B.__match_args__)
    reveal_type(asdict(B(1, 2)))
    reveal_type(astuple(B(1, 2)))
    reveal_type(fields(B))
    print(m(A(1, 2)), m(B(1, 2)))


go()
