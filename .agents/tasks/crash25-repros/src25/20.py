# area: protocols
# origin: python/mypy check-protocols.test [case testTwoUncomfortablyIncompatibleProtocolsWithoutRunningInIssue9771]
from typing import cast, Protocol, TypeVar, Union

T1 = TypeVar("T1", covariant=True)
T2 = TypeVar("T2")

class P1(Protocol[T1]):
    def b(self) -> int: ...
    def a(self, other: "P1[T2]") -> T1: ...

class P2(Protocol[T1]):
    def a(self, other: Union[P1[T2], "P2[T2]"]) -> T1: ...

p11: P1 = cast(P1, 1)
p12: P1 = cast(P2, 1)   # E
p21: P2 = cast(P1, 1)
p22: P2 = cast(P2, 1)   # E
