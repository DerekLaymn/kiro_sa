from typing import ClassVar, Protocol, reveal_type


class Registry(Protocol):
    kind: ClassVar[str]


class A:
    kind: ClassVar[str] = "a"


class B:
    def __init__(self) -> None:
        self.kind = "b"


class C:
    kind = "c"


def show(r: Registry) -> str:
    reveal_type(r.kind)
    return r.kind


print(show(A()))
print(show(B()))
print(show(C()))
print(show(A))
