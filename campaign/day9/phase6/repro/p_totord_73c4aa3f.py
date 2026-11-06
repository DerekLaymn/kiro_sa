# area: inheritance_mro
# hypothesis: With total_ordering, __lt__ comes from Base and __gt__ is local, so c1 < c2 and c1 > c2 return the literal values; an annotation-only __len__ makes len() raise TypeError at runtime.
# origin: runs/day9/parents/D_shadow/d3p_inheritance_mro_total_ordering_inherited_lt.py
# hypothesis: With total_ordering, __lt__ comes from Base and __gt__ is local, so c1 < c2 and c1 > c2 return the literal values; an annotation-only __len__ makes len() raise TypeError at runtime.
from collections.abc import Callable
from functools import total_ordering
from typing import Literal, reveal_type


class Base:
    def __lt__(self, other: 'Base') -> Literal[True]:
        return True


@total_ordering
class Child(Base):
    def __gt__(self, other: 'Child') -> Literal[False]:
        return False


c1 = Child()
c2 = Child()
reveal_type(c1 < c2)
reveal_type(c1 > c2)
reveal_type(c1 <= c2)
print(c1 < c2, c1 > c2, c1 <= c2, c1 >= c2)


class Probe:
    __len__: Callable[[], int]


class Sized:
    def __len__(self) -> int:
        return 2


p = Probe()
s = Sized()
print('sized', len(s))
try:
    print(len(p))  # expect-error: __len__ is only annotated, not defined
except TypeError as exc:
    print('probe:', type(exc).__name__)
