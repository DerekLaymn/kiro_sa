import typing

T = typing.TypeVar("T")
P = typing.ParamSpec("P")


class User:
    def __init__(self: typing.Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> None: ...

    def __call__(self: typing.Callable[P, T], x: int, *args: P.args, **kwargs: P.kwargs) -> T: ...


User()
