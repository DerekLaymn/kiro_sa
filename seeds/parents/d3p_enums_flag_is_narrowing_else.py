# area: enums_literals
# hypothesis: mypy expands enum.Flag into its members for `is` narrowing, so the else branch is unreachable and unchecked, although F.R | F.W is neither member. Vary: ==, match statement, `in (F.R, F.W)`, IntFlag, a parameter vs a local variable.
# origin: fuzz/llm-run-2026-10-27 bug-06 (mypy Flag is-narrowing, candidate)
import enum


class F(enum.Flag):
    R = 1
    W = 2


def h(x: F) -> str:
    if x is F.R:
        return "R"
    elif x is F.W:
        return "W"
    else:
        return 1 + "bad"


print(h(F.R | F.W))
