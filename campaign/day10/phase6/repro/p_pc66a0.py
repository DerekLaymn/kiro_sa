# area: paramspec_concatenate
# hypothesis: Decorators that forward P.args and P.kwargs keep the wrapped signature, and a Concatenate[str, P] wrapper adds exactly one leading str, so the marked calls must be rejected.
# origin: runs/day10/parents/N_wrap/hv_paramspec_concatenate__conformance__generics_paramspec_components.py
# area: paramspec_concatenate
# hypothesis: Decorators that forward P.args and P.kwargs keep the wrapped signature, and a Concatenate[str, P] wrapper adds exactly one leading str, so the marked calls must be rejected.
from typing import Callable, Concatenate, ParamSpec, TypeVar, assert_type, reveal_type

P = ParamSpec('P')
R = TypeVar('R')


def logged(f: Callable[P, R]) -> Callable[P, R]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        print('call')
        return f(*args, **kwargs)

    return wrapper


def with_tag(f: Callable[P, R]) -> Callable[Concatenate[str, P], R]:
    def wrapper(tag: str, *args: P.args, **kwargs: P.kwargs) -> R:
        print('tag', tag)
        return f(*args, **kwargs)

    return wrapper


@logged
def scale(x: int, factor: float = 1.0) -> float:
    return x * factor


@with_tag
@logged
def label(name: str, width: int) -> str:
    return name.ljust(width)


reveal_type(scale)
reveal_type(label)
assert_type(scale(3, factor=2.0), float)
print(scale(3, 2.0))
print(label('t1', 'name', 6) + '|')


def misuse_label() -> None:
    label('t2', 6)  # expect-error: 6 is not str and width is missing


def misuse_scale() -> None:
    scale('x')  # expect-error: str is not int


try:
    misuse_label()
except TypeError as exc:
    print('label:', type(exc).__name__)

try:
    misuse_scale()
except TypeError as exc:
    print('scale:', type(exc).__name__)
