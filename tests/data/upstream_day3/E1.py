import typing

T = typing.TypeVar("T")
P = typing.ParamSpec("P")


@typing.dataclass_transform()
class Model: ...


class User(Model):
    id: int
    name: str
    city: str

    def __init__(self: typing.Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> None: ...

    @classmethod
    def __call__(cls: typing.Callable[P, T], some_param: typing.Any, *args: P.args, **kwargs: P.kwargs) -> T: ...


user = User()
