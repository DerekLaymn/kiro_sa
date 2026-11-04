from typing import Generic, TypeVar

Z = TypeVar("Z")


class N(Generic[Z]): ...


class C(N[N["C"]]): ...


_: N[C] = C()
