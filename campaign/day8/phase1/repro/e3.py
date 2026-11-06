from typing import Callable, ParamSpec, TypeVar, reveal_type

T = TypeVar("T")
P = ParamSpec("P")


class User:
    @classmethod
    def __call__(cls: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
        raise NotImplementedError


try:
    User.__call__(1)
except NotImplementedError:
    pass
reveal_type(User.__call__)
