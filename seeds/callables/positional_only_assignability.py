# area: callables
# hypothesis: Callable assignability respects positional-only/keyword-only kinds, *args, defaults, and
# lambdas' inferred parameter types.
# spec: typing spec, callables.html "Assignability rules for callables".
from collections.abc import Callable
from typing import Protocol, reveal_type


def pos_only(a: int, /) -> int:
    return a


def kw_only(*, a: int) -> int:
    return a


def star(*args: int) -> int:
    return sum(args)


class TakesA(Protocol):
    def __call__(self, a: int) -> int: ...


f1: Callable[[int], int] = pos_only  # ok
f2: Callable[[int], int] = kw_only  # expect-error: cannot be called positionally
f3: Callable[[int, int], int] = star  # ok
f4: TakesA = pos_only  # expect-error: protocol allows a=... by keyword
f5: Callable[[int], str] = lambda x: str(x + 1)
reveal_type(f5)
print(f1(1), f3(1, 2), f5(1))
