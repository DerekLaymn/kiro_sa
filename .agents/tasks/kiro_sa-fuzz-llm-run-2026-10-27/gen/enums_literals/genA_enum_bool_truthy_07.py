from typing import reveal_type  # noqa

from enum import Enum
from typing import Literal


class Bit(Enum):
    OFF = 0
    ON = 1


class Flagged(Enum):
    NO = False
    YES = True

    def __bool__(self) -> bool:
        return bool(self.value)


def go(b: Bit, f: Flagged, lit: Literal[0, 1]) -> None:
    if b:
        reveal_type(b)
    else:
        reveal_type(b)
    if f:
        reveal_type(f)
    else:
        reveal_type(f)
    if lit:
        reveal_type(lit)
    else:
        reveal_type(lit)
    print(b, f)


go(Bit.OFF, Flagged.NO, 1)
