from collections.abc import Callable
from typing import reveal_type


class Foo[*Ts, **P = [float, bool]]:
    def args(self) -> tuple[*Ts]:
        raise NotImplementedError

    def fn(self) -> Callable[P, None]:
        raise NotImplementedError


foo = Foo[int]()
reveal_type(foo)
reveal_type(foo.args())
reveal_type(foo.fn())
