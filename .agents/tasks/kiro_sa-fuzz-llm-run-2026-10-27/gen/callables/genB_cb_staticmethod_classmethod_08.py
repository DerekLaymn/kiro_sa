from collections.abc import Callable
from typing import reveal_type


class C:
    @staticmethod
    def s(n: int) -> int:
        return n

    @classmethod
    def k(cls, n: int) -> int:
        return n


c = C()
a: Callable[[int], int] = c.s
b: Callable[[int], int] = c.k
d: Callable[[C, int], int] = C.k  # error
reveal_type(c.s)
reveal_type(c.k)
print(a(1), b(2), d if False else 0)
