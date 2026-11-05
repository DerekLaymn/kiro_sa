# area: self_classmethods
# hypothesis: A class with __call__: Self | None, called on an instance, makes checkers segfault or overflow while resolving Self; at runtime the None attribute is not callable and raises TypeError. Variants use Self in a tuple, Optional[Self], a classmethod __call__, and a subclass instance.
# origin: runs/hits/d3p_self_classmethods_self_call_union.py
from typing import Optional, Self


class C:
    __call__: Self | None = None


class Sub(C):
    pass


class Pair:
    __call__: tuple[Self, ...] = ()


class Opt:
    __call__: Optional[Self] = None


class K:
    @classmethod
    def __call__(cls) -> int:
        return 1


def attempt(obj: C | Pair | Opt) -> str:
    try:
        obj()  # expect-error
    except TypeError as exc:
        return f"TypeError: {exc}"
    return "called"


x: C = C()
print(attempt(x), attempt(Sub()), attempt(Pair()), attempt(Opt()), K()())
