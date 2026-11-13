# area: enums_literals
# hypothesis: IntEnum TRUE = True after ONE = 1 is an alias of ONE at runtime (same object); mypy and pyright keep Literal[Integer.TRUE], ty reveals Literal[Integer.ONE]. Vary: StrEnum duplicate values, match/assert_never over an aliased enum.
# origin: runs/day3/gen/enums_literals/d3p_enums_literals_intenum_true_aliases_one__mut1_2f2cf71e.py (seed-0de4710c02b5); campaign/day3-report.md section 5 item 5
# features: intenum, enum_alias, duplicate_value, literal_bool, runtime_identity
from enum import IntEnum, StrEnum
from typing import reveal_type


class Integer(IntEnum):
    ONE = 1
    TRUE = True
    TWO = 2


class Color(StrEnum):
    RED = "red"
    CRIMSON = "red"


reveal_type(Integer.TRUE)
print(Integer.TRUE is Integer.ONE, Integer.TRUE.value, list(Integer))
print(Color.CRIMSON is Color.RED, list(Color))
