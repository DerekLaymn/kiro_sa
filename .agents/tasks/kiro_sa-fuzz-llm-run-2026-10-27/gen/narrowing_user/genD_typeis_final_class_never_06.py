from typing import final, TypeIs, reveal_type


@final
class F: ...


class P: ...
class Q: ...


def is_p(x: object) -> TypeIs[P]:
    return isinstance(x, P)


def is_f(x: object) -> TypeIs[F]:
    return isinstance(x, F)


def f(x: F | Q) -> None:
    if is_p(x):
        reveal_type(x)
    else:
        reveal_type(x)


def g(x: F) -> None:
    if is_p(x):
        reveal_type(x)
    else:
        reveal_type(x)


def h(x: P | Q) -> None:
    if is_f(x):
        reveal_type(x)
    else:
        reveal_type(x)


f(F())
g(F())
h(P())
