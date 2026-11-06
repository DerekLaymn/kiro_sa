# area: typevartuple_unpack
# hypothesis: A class generic over a TypeVarTuple followed by a defaulted TypeVar gives the tuple and the default type to reveal_type, and the default-typed method runs at runtime.
# origin: runs/day10/parents/C_tvt/d3p_typevartuple_unpack_paramspec_default_after_tvt.py
# hypothesis: A class generic over a TypeVarTuple followed by a defaulted TypeVar gives the tuple and the default type to reveal_type, and the default-typed method runs at runtime.
from typing import Generic, TypeVar, TypeVarTuple, reveal_type

Ts = TypeVarTuple('Ts')
D = TypeVar('D', default=bool)


class Pair(Generic[*Ts, D]):
    def __init__(self, *items: *Ts) -> None:
        self.items = items

    def first_or(self, fallback: D) -> D:
        return fallback


def describe(p: Pair[int, str, bool]) -> None:
    reveal_type(p.items)
    reveal_type(p.first_or(True))


p1: Pair[int, str, bool] = Pair(1, 'a', True)
describe(p1)
print(p1.items, p1.first_or(False))
