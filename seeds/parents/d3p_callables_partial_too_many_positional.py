# area: callables
# hypothesis: functools.partial(f, 1, 2, 3) binds more positional arguments than f accepts; CPython raises when the partial is called, mypy is silent and ty flags only the partial() line. Vary: keyword arguments, a method, a Protocol-typed callable, a ParamSpec decorator that returns partial.
# origin: harvested program seed-67774769f97e (ruff mdtest call/functools_partial.md block 23; runtime_miss, mypy silent)
from functools import partial

def f(a: int, b: int) -> int:
    return a + b

p = partial(f, 1, 2, 3)  # error: [too-many-positional-arguments]
reveal_type(p)  # revealed: partial[() -> int]
p()
p(1)  # error: [too-many-positional-arguments]
