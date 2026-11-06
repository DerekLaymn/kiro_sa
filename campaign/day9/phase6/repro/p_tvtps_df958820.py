# area: typevartuple_unpack
# hypothesis: For a PEP 695 class Callback[*Ts, **P = [bool]], Callback[int, str] should keep P at its default and reveal fn as (flag: bool) -> tuple[int, str], and a constrained TypeVar K: (int, str) = int should infer str for a str argument.
# origin: runs/day9/parents/C_tvt/d3p_typevartuple_unpack_paramspec_default_after_tvt.py
# area: typevartuple_unpack
# hypothesis: for class Callback[*Ts, **P = [bool]], Callback[int, str] should keep P at its default (bool,) and reveal fn as (flag: bool) -> tuple[int, str], and a constrained TypeVar K: (int, str) = int should infer str for a str argument; checkers that drop the ParamSpec default or the constraint would disagree.
from typing import Callable, reveal_type


class Callback[*Ts, **P = [bool]]:
    def __init__(self, fn: Callable[P, tuple[*Ts]]) -> None:
        self.fn = fn


class Tag[K: (int, str) = int]:
    def __init__(self, key: K) -> None:
        self.key = key


def pair(flag: bool) -> tuple[int, str]:
    return (int(flag), 'x')


def one(s: str) -> tuple[int]:
    return (len(s),)


cb = Callback[int, str](pair)
reveal_type(cb.fn)  # (flag: bool) -> tuple[int, str]
print(cb.fn(True))

cb2 = Callback[int, [str]](one)
reveal_type(cb2.fn)  # (s: str) -> tuple[int]
print(cb2.fn('abc'))

t1 = Tag(1)
t2 = Tag('a')
reveal_type(t2.key)  # str
print(t1.key, t2.key)
