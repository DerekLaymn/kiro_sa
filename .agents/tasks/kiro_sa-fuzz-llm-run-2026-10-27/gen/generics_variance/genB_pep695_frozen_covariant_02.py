from typing import reveal_type


class Ro[T]:
    def __init__(self, v: T) -> None:
        self._v = v

    @property
    def v(self) -> T:
        return self._v


class Sink[T]:
    def put(self, v: T) -> None:
        print(v)


def f(r: Ro[float], s: Sink[int]) -> None:
    reveal_type(r.v)
    s.put(1)


ri = Ro(1)
reveal_type(ri)
f(ri, Sink[int]())  # OK covariant
sf: Sink[float] = Sink[int]()  # error: contravariant
si: Sink[int] = Sink[float]()  # OK
reveal_type(si)
