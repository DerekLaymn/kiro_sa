from typing import Self, overload, reveal_type


class Vec:
    def __init__(self, *xs: float) -> None:
        self.xs = xs

    @overload
    def __mul__(self, o: float) -> Self: ...
    @overload
    def __mul__(self, o: "Vec") -> float: ...
    def __mul__(self, o: "float | Vec") -> "Self | float":
        if isinstance(o, Vec):
            return sum(a * b for a, b in zip(self.xs, o.xs))
        return type(self)(*(a * o for a in self.xs))

    @overload
    def __getitem__(self, i: int) -> float: ...
    @overload
    def __getitem__(self, i: slice) -> Self: ...
    def __getitem__(self, i: "int | slice") -> "float | Self":
        if isinstance(i, slice):
            return type(self)(*self.xs[i])
        return self.xs[i]


class Vec3(Vec): ...


def f(a: Vec3, b: Vec) -> None:
    reveal_type(a * 2.0)
    reveal_type(a * b)
    reveal_type(a[0])
    reveal_type(a[:2])
    reveal_type(2.0 * a if False else a)


f(Vec3(1, 2, 3), Vec(1, 1, 1))
print((Vec3(1, 2) * 2).xs, Vec(1, 2) * Vec(3, 4), Vec(1, 2, 3)[1:].xs)
