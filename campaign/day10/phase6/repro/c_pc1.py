from typing import Callable, Concatenate, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def with_tag(f: Callable[P, R]) -> Callable[Concatenate[str, P], R]:
    def wrapper(tag: str, *args: P.args, **kwargs: P.kwargs) -> R:
        return f(*args, **kwargs)

    return wrapper


@with_tag
def label(name: str, width: int) -> str:
    return name.ljust(width)


label("t2", 6)
