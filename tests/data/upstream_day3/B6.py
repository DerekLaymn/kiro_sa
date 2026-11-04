from typing import Generic, TypeVar

Z = TypeVar("Z", covariant=True)


class N(Generic[Z]): ...


class C(N[N["C"]]): ...


_: N[C] = C()
