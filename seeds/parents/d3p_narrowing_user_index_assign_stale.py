# area: narrowing_user
# hypothesis: After narrowing xs[0] is not None and then assigning xs[0] = None, mypy keeps the stale narrowed int and misses the runtime TypeError. Vary: dict key, nested index xs[0][1], attribute of a subscript, a method call between narrowing and use, a negative or variable index.
# origin: fuzz/llm-run-2026-10-27 bug-01 (mypy stale index narrowing, candidate)
from typing import reveal_type


def a(xs: list[int | None]) -> int:
    if xs[0] is not None:
        xs[0] = None
        reveal_type(xs[0])
        return xs[0] + 1
    return 0


a([1])
