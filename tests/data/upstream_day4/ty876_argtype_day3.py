# area: enums_literals
# hypothesis: F.R | F.W on a Flag is a combined pseudo-member equal to neither F.R nor F.W, so identity checks against either member are False at runtime.
# origin: runs/hits/d3p_enums_flag_or_literal_union.py
# area: enums_literals
# hypothesis: F.R | F.W on a Flag is a combined pseudo-member equal to neither F.R nor F.W, so identity checks against either member are False at runtime.
import enum
from typing import Literal


class F(enum.Flag):
    R = 1
    W = 2


class I(enum.IntFlag):
    A = 1
    B = 2


def only_r(x: Literal[F.R]) -> int:
    return 1


combined = F.R | F.W
assert (combined is F.R) is False
assert (combined is F.W) is False
assert combined.value == 3
assert (F.R ^ F.W).value == 3
assert (combined & F.R) is F.R
assert (I.A | I.B).value == 3
assert combined == F.R | F.W
assert only_r(combined) == 1  # expect-error
