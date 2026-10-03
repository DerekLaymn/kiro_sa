# area: enums_literals
# hypothesis: enum member/value types, auto(), nonmember/member, and exhaustive narrowing on enums.
# spec: typing spec, enums.html.
from enum import Enum, IntEnum, auto, member, nonmember
from typing import Literal, assert_never, reveal_type


class Color(Enum):
    RED = 1
    GREEN = "g"
    BLUE = 3
    helper = nonmember(42)

    @member
    def shade(self) -> str:  # a method wrapped by member() becomes a member
        return "shade"


class Level(IntEnum):
    LOW = auto()
    HIGH = auto()


def name(c: Literal[Color.RED, Color.GREEN]) -> str:
    if c is Color.RED:
        return "red"
    elif c is Color.GREEN:
        return "green"
    else:
        assert_never(c)


reveal_type(Color.RED.value)  # int
reveal_type(Color.GREEN.value)  # str
reveal_type(Color.helper)  # int (nonmember)
reveal_type(Level.HIGH + 1)  # int
print(name(Color.RED), Color.helper, len(Color), Level.HIGH + 1)
