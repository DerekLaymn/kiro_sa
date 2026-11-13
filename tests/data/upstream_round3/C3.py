from typing import Callable, ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")


def test(x: Callable[P, T]) -> Callable[P, T]:
    return x


test(test)
