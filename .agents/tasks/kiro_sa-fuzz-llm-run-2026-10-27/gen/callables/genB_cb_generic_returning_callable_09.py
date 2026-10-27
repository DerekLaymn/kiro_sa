from collections.abc import Callable
from typing import reveal_type


def mk[T](x: T) -> Callable[[T], T]:
    def inner(y: T) -> T:
        return x if y is None else y

    return inner


f = mk(1)
reveal_type(f)
reveal_type(f(2))
f("s")  # error
print(f(2))
