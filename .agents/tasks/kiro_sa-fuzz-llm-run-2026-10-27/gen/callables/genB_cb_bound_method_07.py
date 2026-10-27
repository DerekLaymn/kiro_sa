from collections.abc import Callable
from typing import reveal_type


class C:
    def m(self, n: int) -> str:
        return str(n)


c = C()
a: Callable[[int], str] = c.m
b: Callable[[C, int], str] = C.m
d: Callable[[int], str] = C.m  # error
reveal_type(a)
reveal_type(b)
print(a(1), b(c, 2), d if False else 0)
