# area: overloads
# hypothesis: A union argument is split across overloads, so norm(Literal['a', 'b'] | int) reveals per-member results, and an Any argument matching several overloads reveals Any.
# origin: runs/day8/parents/R_reserve3/rsv_overloads_d41747bd.py
# hypothesis: A union argument is split across overloads, so norm(Literal['a', 'b'] | int) reveals per-member results, and an Any argument matching several overloads reveals Any.
from typing import Any, Literal, TypeVar, overload, reveal_type

T = TypeVar('T')


@overload
def norm(x: Literal['a', 'b']) -> Literal['A', 'B']: ...
@overload
def norm(x: str) -> str: ...
@overload
def norm(x: T) -> T: ...
def norm(x: object) -> object:
    if isinstance(x, str):
        return x.upper()
    return x


def run_union(v: Literal['a', 'b'] | int) -> Literal['A', 'B'] | int:
    r = norm(v)
    reveal_type(r)  # Literal['A', 'B'] | int
    return r


def run_any(a: Any) -> object:
    r = norm(a)
    reveal_type(r)  # Any
    return r


reveal_type(norm('a'))  # Literal['A', 'B']
reveal_type(norm(2))  # int
assert run_union('a') == 'A'
assert run_union(7) == 7
assert run_any('b') == 'B'
assert run_any(3) == 3
