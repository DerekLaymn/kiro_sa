from typing import reveal_type


class Cell[T]:
    def __init__(self, v: T) -> None:
        self._v = v

    @property
    def v(self) -> T:
        return self._v

    @v.setter
    def v(self, nv: T) -> None:
        self._v = nv


def g(c: Cell[float]) -> float:
    return c.v


ci = Cell(3)
reveal_type(ci)
print(g(ci))  # error: invariant due to setter
