# area: narrowing_user
# hypothesis: TypeIs narrows in BOTH branches (negative branch removes the type); TypeGuard only in the
# positive branch. Generic TypeIs functions must be solved per call.
# spec: typing spec, narrowing.html.
from typing import TypeGuard, TypeIs, reveal_type


def is_str(x: object) -> TypeIs[str]:
    return isinstance(x, str)


def is_str_guard(x: object) -> TypeGuard[str]:
    return isinstance(x, str)


def is_instance_of[T](x: object, cls: type[T]) -> TypeIs[T]:
    return isinstance(x, cls)


def f(v: int | str, w: int | str, u: int | bytes) -> None:
    if is_str(v):
        reveal_type(v)  # str
    else:
        reveal_type(v)  # int
    if is_str_guard(w):
        reveal_type(w)  # str
    else:
        reveal_type(w)  # int | str  (TypeGuard does not narrow the negative branch)
    if is_instance_of(u, bytes):
        reveal_type(u)  # bytes
    else:
        reveal_type(u)  # int


f(1, "a", b"x")
f("a", 2, 3)
