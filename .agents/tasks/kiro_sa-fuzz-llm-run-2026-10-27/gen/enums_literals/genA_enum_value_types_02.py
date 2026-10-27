from typing import reveal_type  # noqa

from enum import Enum, IntEnum, StrEnum, Flag, auto


class S(StrEnum):
    A = auto()
    B = "bee"


class N(IntEnum):
    ONE = 1
    TWO = 2


class F(Flag):
    R = auto()
    W = auto()


class T(Enum):
    X = (1, "x")
    Y = (2, "y")


def go() -> None:
    reveal_type(S.A.value)
    reveal_type(S.B.value)
    reveal_type(N.ONE + 1)
    reveal_type(N.TWO.value)
    reveal_type(F.R | F.W)
    reveal_type(T.X.value)
    reveal_type(T.X.name)
    reveal_type(S.A.upper())
    reveal_type(N.ONE < N.TWO)
    print(S.A, N.ONE, F.R | F.W, T.Y)


go()
