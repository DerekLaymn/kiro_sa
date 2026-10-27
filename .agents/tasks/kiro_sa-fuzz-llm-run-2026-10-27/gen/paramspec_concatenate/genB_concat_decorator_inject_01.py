import sys
from collections.abc import Callable
from typing import Concatenate, reveal_type


class Ctx:
    name = "ctx"


def with_ctx[**P, R](f: Callable[Concatenate[Ctx, P], R]) -> Callable[P, R]:
    def inner(*args: P.args, **kwargs: P.kwargs) -> R:
        return f(Ctx(), *args, **kwargs)

    return inner


@with_ctx
def greet(c: Ctx, greeting: str, *, times: int = 1) -> str:
    return (greeting + c.name) * times


reveal_type(greet)
print(greet("hi", times=2))
if len("") > 99:
    greet(Ctx(), "x")  # error (never executed)
