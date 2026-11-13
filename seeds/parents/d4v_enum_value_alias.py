# area: enums_literals
# hypothesis: Enum members that repeat an earlier member's value are aliases at runtime (E.B is E.A); ty models them, mypy and pyright treat them as separate members, which gives a false positive on a Literal assignment and on assert_never.
# origin: results/bugs.md section 1 (seed-0de4710c02b5, d3p_enums_literals_intenum_true_aliases_one__mut1_2f2cf71e)
from enum import Enum
from typing import Literal, assert_never, assert_type


class E(Enum):
    A = 1
    B = 1
    C = 2


x: Literal[E.A] = E.B
assert_type(E.B, Literal[E.A])


def f(e: E) -> int:
    if e is E.A:
        return 1
    elif e is E.C:
        return 2
    else:
        assert_never(e)


print(E.B is E.A, f(E.B), x)
