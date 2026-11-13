import typing

T = typing.TypeVar("T")
P = typing.ParamSpec("P")


class User:
    @classmethod
    def __call__(cls: typing.Callable[P, T], x: int, *args: P.args, **kwargs: P.kwargs) -> T: ...


User()
