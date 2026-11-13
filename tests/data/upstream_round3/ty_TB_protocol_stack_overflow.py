from typing import Protocol, TypeVar

T1 = TypeVar("T1", covariant=True)
T2 = TypeVar("T2")

class P1(Protocol[T1]):
    def b(self) -> int: ...
    def a(self, other: "P1[T2]") -> T1: ...

class P2(Protocol[T1]):
    def a(self, other: "P1[T2] | P2[T2]") -> T1: ...
