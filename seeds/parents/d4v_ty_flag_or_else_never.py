# area: enums_literals
# hypothesis: ty infers Literal[F.R, F.W] for F.R | F.W on an enum.Flag, so an is-chain over the members makes the final else Never although the runtime value <F.R|W: 3> reaches it (ty#876, spec exempts Flag from literal expansion). Vary: &, ^, ~, IntFlag (ty gives Literal[I.A] for I.A | I.B), match statement.
# origin: campaign/day4/verify-v2.md candidate 'Flag combination Never' (duplicate of ty#876, instructive)
import enum
from typing import Literal, reveal_type


class F(enum.Flag):
    R = 1
    W = 2


def only_r(x: Literal[F.R]) -> int:
    return 1


c = F.R | F.W
reveal_type(c)
only_r(c)  # expect-error
if c is F.R:
    print("R")
elif c is F.W:
    print("W")
else:
    reveal_type(c)
    print("both")
