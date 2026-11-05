# area: typevartuple_unpack
# hypothesis: class Foo[*Ts, **P = [float, bool]] puts a defaulted ParamSpec after a TypeVarTuple, which the typing spec allows (PEP 696); mypy rejects the subscript Foo[int, str] with "Can only replace ParamSpec" and degrades the result to Any, while ty and pyright accept it and CPython raises TypeError at class creation (python/typing#2211). Vary: a defaulted TypeVar after *Ts (all checkers must reject), P with Concatenate, a nested Foo[Foo[int], str], the legacy Generic[Unpack[Ts], P] spelling, a TypeVarTuple default too.
# origin: campaign/day6/repro/m1_mypy_use_site.py (Part A verdict: mypy bug STILL-BUG-NEW, campaign/day6-verification.md section 5.5; ty not-a-bug)
from collections.abc import Callable
from typing import assert_type

try:
    class Foo[*Ts, **P = [float, bool]]:
        def args(self) -> tuple[*Ts]:
            raise NotImplementedError

        def fn(self) -> Callable[P, None]:
            raise NotImplementedError

    foo = Foo[int, str]()
    assert_type(foo.args(), tuple[int, str])
    assert_type(foo.fn(), Callable[[float, bool], None])

    bar = Foo[int, str, [bytes]]()
    assert_type(bar.args(), tuple[int, str])
    assert_type(bar.fn(), Callable[[bytes], None])
except TypeError as e:
    print('TypeError:', e)
