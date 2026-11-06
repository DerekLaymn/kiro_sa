from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def logged(fn: F) -> F:
    print(fn.__name__)
    return fn


def plain(fn: Callable[..., Any]) -> None:
    print(fn.__name__)
