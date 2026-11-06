# area: typevartuple_unpack
# hypothesis: A PEP 695 class with a TypeVarTuple followed by a defaulted ParamSpec is accepted by mypy and ty but may raise TypeError when CPython 3.13 executes it.
# origin: runs/day9/parents/C_tvt/d3p_typevartuple_unpack_paramspec_default_after_tvt.py
# hypothesis: A PEP 695 class with a TypeVarTuple followed by a defaulted ParamSpec is accepted by mypy and ty but may raise TypeError when CPython 3.13 executes it.
from typing import Callable, reveal_type

class Callback[*Ts, **P = [bool]]:
    def __init__(self, fn: Callable[P, tuple[*Ts]]) -> None:
        self.fn = fn

def make(x: int, y: str) -> tuple[int, str]:
    return (x, y)

cb = Callback(make)
reveal_type(cb)
reveal_type(cb.fn)
print(cb.fn(1, "a"))
