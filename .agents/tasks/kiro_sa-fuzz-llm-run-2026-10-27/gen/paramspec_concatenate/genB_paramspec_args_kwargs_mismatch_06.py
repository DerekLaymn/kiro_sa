from collections.abc import Callable
from typing import reveal_type


def bad[**P, R](f: Callable[P, R]) -> Callable[P, R]:
    def inner(*args: P.args, **kwargs: P.kwargs) -> R:
        return f(*args)  # error: kwargs missing

    return inner


@bad
def k(a: int) -> int:
    return a


reveal_type(k)
print(k(1))
