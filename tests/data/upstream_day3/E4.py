import typing

T = typing.TypeVar("T")
P = typing.ParamSpec("P")


class User:
    @classmethod
    def __call__(cls: typing.Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T: ...


user = User()
user()
