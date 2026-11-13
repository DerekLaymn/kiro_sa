# area: enums_literals
# hypothesis: ty infers Literal[F.R, F.W] for F.R | F.W on an enum.Flag although the runtime value is neither member (spec exempts Flag from literal expansion). Vary: &, ^, ~, IntFlag, a flag with an alias member, passing the result to a function expecting Literal[F.R].
# origin: fuzz/llm-run-2026-10-27 bug-02 (ty Flag union, candidate)
import enum
from typing import reveal_type


class F(enum.Flag):
    R = 1
    W = 2


a = F.R | F.W
reveal_type(a)
print(repr(a), a is F.R, a is F.W)
