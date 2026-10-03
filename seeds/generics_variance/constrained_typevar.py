# area: generics_variance
# hypothesis: a constrained TypeVar solves to the *constraint*, never to a subclass of it.
# spec: typing spec, generics.html "Type variables with constraints".
from typing import TypeVar, reveal_type

S = TypeVar("S", str, bytes)


class MyStr(str):
    pass


def concat(a: S, b: S) -> S:
    return a + b


reveal_type(concat(MyStr("a"), MyStr("b")))  # spec: str, not MyStr
reveal_type(concat(b"a", b"b"))
try:
    concat("a", b"b")  # expect-error: no single constraint fits
except TypeError as exc:
    print('runtime:', type(exc).__name__)
print("done")
