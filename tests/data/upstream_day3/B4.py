from typing import Generic, TypeVar

Z = TypeVar("Z", contravariant=True)


class N(Generic[Z]): ...


class C(N[N["C"]]): ...


def f(c: C) -> N[C]:
    return c
