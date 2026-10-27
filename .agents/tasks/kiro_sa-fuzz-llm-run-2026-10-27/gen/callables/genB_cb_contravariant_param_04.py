from collections.abc import Callable
from typing import reveal_type


class A: ...
class B(A): ...


def takes_a(a: A) -> B:
    return B()


def takes_b(b: B) -> A:
    return b


f: Callable[[B], A] = takes_a  # OK
g: Callable[[A], B] = takes_b  # error
reveal_type(f(B()))
print(f(B()), g if False else 0)
