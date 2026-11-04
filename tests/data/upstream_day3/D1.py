from typing import Any, Generic, TypeVar

Z = TypeVar("Z", contravariant=True)
X = TypeVar("X")


class N(Generic[Z]): ...


class C(Generic[X], N[N["C[C[X]]"]]): ...


_: N[C[Any]] = C[Any]()
