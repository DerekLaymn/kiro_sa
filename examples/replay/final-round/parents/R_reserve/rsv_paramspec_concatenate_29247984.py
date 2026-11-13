# area: paramspec_concatenate
# hypothesis: Concatenate parameters are contravariant, so a decorator that injects an object argument must reject a callee whose first parameter is narrower (str).
# origin: N_wrap/paramspec_concatenate__decorator_signature.py
# area: paramspec_concatenate
# hypothesis: Concatenate parameters are contravariant, so a decorator that injects an
# `object` argument must reject a callee whose first parameter is narrower (`str`).
from collections.abc import Callable
from typing import Concatenate, reveal_type


def logged[**P, R](fn: Callable[P, R]) -> Callable[P, R]:
    def inner(*args: P.args, **kwargs: P.kwargs) -> R:
        return fn(*args, **kwargs)
    return inner


def with_ctx[**P, R](fn: Callable[Concatenate[object, P], R]) -> Callable[P, R]:
    def inner(*args: P.args, **kwargs: P.kwargs) -> R:
        return fn('ctx', *args, **kwargs)
    return inner


@logged
@with_ctx
def audit(ctx: object, table: str, limit: int = 10) -> list[str]:
    return [f'{ctx}:{table}'] * limit


@with_ctx  # expect-error: callee's first parameter `str` does not accept `object`
def strict(ctx: str, table: str) -> str:
    return ctx + table


reveal_type(audit)
reveal_type(strict)
print(audit('t', limit=2), strict('t'))
try:
    audit('t', limit='x')  # expect-error: list * str raises TypeError at runtime
except TypeError as exc:
    print('runtime:', type(exc).__name__)
