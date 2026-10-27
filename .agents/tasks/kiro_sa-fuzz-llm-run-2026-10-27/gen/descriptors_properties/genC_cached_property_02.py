from functools import cached_property
from typing import reveal_type


class A:
    calls = 0

    @cached_property
    def value(self) -> int:
        A.calls += 1
        return 10


a = A()
reveal_type(a.value)
reveal_type(A.value)
a.value = 20
print(a.value, A.calls)
del a.value
print(a.value, A.calls)
a.value = "str"  # type: ignore
print(a.value)


class B(A):
    value = "overridden"  # type: ignore


reveal_type(B().value)
print(B().value)
