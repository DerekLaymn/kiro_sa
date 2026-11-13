# area: inheritance_mro
# hypothesis: With @functools.total_ordering, __lt__ is inherited from Base and __gt__ is defined locally; mypy reveals the opposite literal for `c1 < c2` and `c1 > c2` than ty and pyright, and Any for the synthesized methods. Vary: define __le__ locally, swap which base supplies the ordering method, return bool instead of Literal.
# origin: runs/day2/out3 seed-bcd8afd96f79 (ruff mdtest decorators/total_ordering.md block 8; reveal mismatch, mypy contradicts runtime)
from functools import total_ordering
from typing import Literal, reveal_type


class Base:
    def __lt__(self, other: "Base") -> Literal[True]:
        return True


@total_ordering
class Child(Base):
    def __gt__(self, other: "Child") -> Literal[False]:
        return False


c1 = Child()
c2 = Child()
reveal_type(c1 < c2)
reveal_type(c1 > c2)
reveal_type(c1 <= c2)
print(c1 < c2, c1 > c2, c1 <= c2, c1 >= c2)
