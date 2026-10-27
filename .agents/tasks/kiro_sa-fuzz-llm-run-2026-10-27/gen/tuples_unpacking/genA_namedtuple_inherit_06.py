from typing import reveal_type  # noqa

from typing import NamedTuple


class Pt(NamedTuple):
    x: int
    y: int


class Pt3(Pt):
    def norm(self) -> int:
        return self.x + self.y

    @property
    def sum(self) -> int:
        return self.x + self.y


def go() -> None:
    p = Pt3(1, 2)
    reveal_type(p)
    x, y = p
    reveal_type(x)
    reveal_type(p._fields)
    reveal_type(p.norm())
    reveal_type(Pt3._make([1, 2]))
    x2, y2, z2 = p
    print(x, y, x2, y2, z2)


try:
    go()
except ValueError:
    print("ValueError")
