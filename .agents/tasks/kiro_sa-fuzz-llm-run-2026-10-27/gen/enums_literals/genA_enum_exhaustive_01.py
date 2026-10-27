from typing import reveal_type  # noqa

from enum import Enum, auto
from typing import assert_never


class Color(Enum):
    RED = auto()
    GREEN = auto()
    BLUE = auto()


def name(c: Color) -> str:
    if c is Color.RED:
        return "r"
    elif c is Color.GREEN:
        return "g"
    else:
        reveal_type(c)
        if c is Color.BLUE:
            return "b"
        assert_never(c)


def name2(c: Color) -> str:
    match c:
        case Color.RED | Color.GREEN:
            reveal_type(c)
            return "rg"
        case Color.BLUE:
            return "b"


print(name(Color.BLUE), name2(Color.RED))
