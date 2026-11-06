from typing import Callable, Concatenate, ParamSpec, TypeVar, reveal_type

P = ParamSpec('P')
R = TypeVar('R')


def logged(f: Callable[P, R]) -> Callable[P, R]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return f(*args, **kwargs)

    return wrapper


def with_tag(f: Callable[P, R]) -> Callable[Concatenate[str, P], R]:
    def wrapper(tag: str, *args: P.args, **kwargs: P.kwargs) -> R:
        return f(*args, **kwargs)

    return wrapper


@with_tag
@logged
def label(name: str, width: int) -> str:
    return name.ljust(width)


@with_tag
def label2(name: str, width: int) -> str:
    return name.ljust(width)


reveal_type(label)
label('t2', 6)
label2('t2', 6)
label('t', 'n', 6)
label('t', 6, 6)
