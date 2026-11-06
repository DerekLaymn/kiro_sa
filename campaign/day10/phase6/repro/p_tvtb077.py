# area: typevartuple_unpack
# hypothesis: A PEP 695 class with a TypeVarTuple followed by a defaulted ParamSpec, nested inside a generic Box, should get the same specialised callable types from mypy and ty.
# origin: runs/day10/parents/C_tvt/d3p_typevartuple_unpack_paramspec_default_after_tvt.py
# area: typevartuple_unpack
# hypothesis: a PEP 695 class with *Ts followed by a defaulted ParamSpec should specialise to the same callable type in both checkers, including when nested inside another generic.
from typing import Callable, reveal_type


class Callback[*Ts, **P = [bool]]:
    def __init__(self, fn: Callable[P, tuple[*Ts]]) -> None:
        self.fn = fn

    def call(self, *args: P.args, **kwargs: P.kwargs) -> tuple[*Ts]:
        return self.fn(*args, **kwargs)


class Box[T]:
    def __init__(self, item: T) -> None:
        self.item = item


def to_pair(flag: bool) -> tuple[int, str]:
    return (int(flag), str(flag))


def to_one(flag: bool) -> tuple[int]:
    return (int(flag),)


cb = Callback[int, str](to_pair)
reveal_type(cb.fn)
reveal_type(cb.call)
boxed = Box(Callback[int](to_one))
reveal_type(boxed.item)
reveal_type(boxed.item.call(True))
cb.call(False)
boxed.item.call(True)
