# area: enums_literals
# hypothesis: F.R | F.W on an enum.Flag is a combined value at runtime (3), so an is-chain over the single members in a helper function reaches its else branch, and a checker that narrows the result to Literal[F.R, F.W] would wrongly make that branch Never.
# origin: runs/day10/parents/N_flow/d4v_ty_flag_or_else_never.py
# area: enums_literals
# hypothesis: F.R | F.W on an enum.Flag is a combined value at runtime (3), so an is-chain over the single members in a helper function reaches its else branch, and a checker that narrows the result to Literal[F.R, F.W] would wrongly make that branch Never.
import enum
from typing import reveal_type


class F(enum.Flag):
    R = 1
    W = 2


class I(enum.IntFlag):
    A = 1
    B = 2


def describe(c: F) -> str:
    if c is F.R:
        return 'R'
    elif c is F.W:
        return 'W'
    else:
        reveal_type(c)
        return 'both'


def describe_match(c: F) -> str:
    match c:
        case F.R:
            return 'R'
        case F.W:
            return 'W'
        case _:
            reveal_type(c)
            return 'other'


def int_name(c: I) -> str:
    if c == I.A:
        return 'A'
    reveal_type(c)
    return 'not A'


both = F.R | F.W
reveal_type(both)
print(describe(both))
print(describe(~F.R))
print(describe_match(F.R ^ F.W))
print(describe_match(F.R & F.W))
print(int_name(I.A | I.B), int_name(I.A))
