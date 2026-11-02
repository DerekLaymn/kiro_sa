# area: gradual_any
# origin: ruff mdtest annotations/union.md block 7
from functools import partial

def f(x: int) -> int:
    return x

def loop(flag: bool) -> None:
    value = partial(f)
    while flag:
        value = value | None  # error: [unsupported-operator]
    reveal_type(value)  # revealed: partial[(x: int) -> int] | Unknown

def reverse_loop(flag: bool) -> None:
    value = staticmethod(f)
    while flag:
        value = None | value  # error: [unsupported-operator]
    reveal_type(value)  # revealed: staticmethod[def f(x: int) -> int] | Unknown
