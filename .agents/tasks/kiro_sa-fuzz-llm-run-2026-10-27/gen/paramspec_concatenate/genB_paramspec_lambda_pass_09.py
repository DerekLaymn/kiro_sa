from collections.abc import Callable
from typing import reveal_type


def ident[**P, R](f: Callable[P, R]) -> Callable[P, R]:
    return f


g = ident(lambda x, y=2: x + y)
reveal_type(g)
print(g(1), g(1, 5))
