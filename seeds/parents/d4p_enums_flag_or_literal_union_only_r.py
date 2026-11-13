# area: enums_literals
# hypothesis: F.R | F.W on a Flag is a pseudo-member, not a Literal union; passing it to a Literal[F.R] parameter is an error for mypy while ty expands the Flag and treats the line as unreachable (Never). Vary: IntFlag, ^ and & operators, a local instead of a module variable.
# origin: runs/day3/gen/enums_literals/d3p_enums_flag_or_literal_union__mut0_41da72aa.py (seed-e4277cc03f53); results/days/day3-report.md section 5 item 2
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
