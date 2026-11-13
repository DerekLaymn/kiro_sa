from typing import Generic, TypeVar

Z = TypeVar("Z", contravariant=True)
X = TypeVar("X")


class N(Generic[Z]): ...


class C(Generic[X], N[N["C[C[X]]"]]): ...


_: N[C[int]] = C[int]()
