from collections.abc import Callable
from typing import Generic, ParamSpec, TypeVarTuple, Unpack, assert_type

Ts = TypeVarTuple("Ts")
P = ParamSpec("P", default=[float, bool])


class Foo(Generic[Unpack[Ts], P]):
    def args(self) -> tuple[Unpack[Ts]]:
        raise NotImplementedError

    def fn(self) -> Callable[P, None]:
        raise NotImplementedError


def check(foo: Foo[int, str]) -> None:
    assert_type(foo.args(), tuple[int, str])
    assert_type(foo.fn(), Callable[[float, bool], None])
