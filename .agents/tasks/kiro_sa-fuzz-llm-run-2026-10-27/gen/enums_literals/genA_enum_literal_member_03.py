from typing import reveal_type  # noqa

from enum import Enum
from typing import Literal


class Mode(Enum):
    R = "r"
    W = "w"
    A = "a"


RW = Literal[Mode.R, Mode.W]


def only_rw(m: RW) -> str:
    return m.value


def go(m: Mode, lit: Literal["r", "w"]) -> None:
    only_rw(Mode.R)
    only_rw(m)
    if m in (Mode.R, Mode.W):
        reveal_type(m)
        only_rw(m)
    if m is not Mode.A:
        reveal_type(m)
    reveal_type(Mode(lit))
    reveal_type(Mode["R"])
    print(m)


go(Mode.A, "r")
