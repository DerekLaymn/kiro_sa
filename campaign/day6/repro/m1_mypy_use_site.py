from collections.abc import Callable
from typing import assert_type


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
