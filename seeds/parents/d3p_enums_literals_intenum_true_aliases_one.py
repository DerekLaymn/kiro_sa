# area: enums_literals
# hypothesis: In an IntEnum, `TRUE = True` after `ONE = 1` is an alias of ONE at runtime (Integer.TRUE is Integer.ONE, value 1); mypy and pyright keep TRUE as a separate member with value Literal[True], ty collapses it. Vary: auto() and an explicit duplicate value, StrEnum duplicates, Flag aliases, `1.0` as a value.
# origin: runs/day2/out3 seed-0aa2461b8e0e (ruff mdtest enums.md block 1; reveal mismatch contradicted by runtime value)
from enum import IntEnum
from typing import reveal_type


class Integer(IntEnum):
    ONE = 1
    TRUE = True
    TWO = 2


reveal_type(Integer.TRUE.value)
reveal_type(Integer.TRUE)
print(Integer.TRUE is Integer.ONE, repr(Integer.TRUE.value))
