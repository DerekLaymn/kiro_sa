# area: enums_literals
# explores: enum.Flag combination, StrEnum values and comparison with plain str, iterating an enum
from enum import Flag, StrEnum, auto
from typing import reveal_type


class Perm(Flag):
    R = auto()
    W = auto()
    X = auto()


class Mode(StrEnum):
    FAST = auto()
    SLOW = auto()


def describe(m: Mode) -> str:
    if m == "fast":
        reveal_type(m)  # Mode (or Literal[Mode.FAST])
        return "f"
    return "s"


rw = Perm.R | Perm.W
reveal_type(rw)  # Perm
reveal_type(Perm.R in rw)  # bool
reveal_type(Mode.FAST.value)  # str
reveal_type([m for m in Mode])  # list[Mode]
print(rw, Perm.R in rw, Mode.FAST.value, describe(Mode.FAST), describe(Mode.SLOW))
