from typing import Generic, TypeVar

Z = TypeVar("Z", contravariant=True)
X = TypeVar("X")


class N(Generic[Z]): ...


class C(Generic[X], N[N["C[C[X]]"]]): ...


def f(c: C[int]) -> N[C[int]]:
    return c
