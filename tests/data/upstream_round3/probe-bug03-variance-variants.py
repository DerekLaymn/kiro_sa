from collections.abc import Callable
from typing import Final


class Plain[T]:  # control: mutable T attribute
    def __init__(self, v: T) -> None:
        self.v = v


class CbInit[T]:  # candidate: mutable Callable[[T], None] attribute set in __init__
    def __init__(self, cb: Callable[[T], None]) -> None:
        self.cb = cb


class CbAnn[T]:  # same, declared with a class-level annotation
    cb: Callable[[T], None]


class Producer[T]:  # mirror: mutable Callable[[], T] attribute
    def __init__(self, f: Callable[[], T]) -> None:
        self.f = f


class CbFinal[T]:  # Final attribute: contravariant is sound here
    def __init__(self, cb: Callable[[T], None]) -> None:
        self.cb: Final = cb


class CbMethod[T]:  # method with T parameter: contravariant is sound
    def call(self, x: T) -> None: ...


def check(
    p: Plain[int],
    ci: CbInit[int],
    ca: CbAnn[int],
    pr: Producer[float],
    cf: CbFinal[int],
    cm: CbMethod[int],
) -> None:
    pf: Plain[float] = p  # expect error (invariant)
    cif: CbInit[float] = ci  # expect error (invariant); wrong direction check below
    cic: CbInit[bool] = ci  # contravariance direction: CbInit[int] -> CbInit[bool]
    caf: CbAnn[bool] = ca  # contravariant direction
    prf: Producer[object] = pr  # expect error (mutable, covariant use => invariant)
    cff: CbFinal[bool] = cf  # contravariant OK (Final)
    cmf: CbMethod[bool] = cm  # contravariant OK (method)
