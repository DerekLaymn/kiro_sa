from typing import reveal_type  # noqa

from typing import Any, Callable, dataclass_transform


def my_field(*, default: Any = ..., kw_only: bool = False, init: bool = True) -> Any:
    return default


@dataclass_transform(kw_only_default=True, field_specifiers=(my_field,))
def model(cls: type) -> type:
    return cls


@dataclass_transform(frozen_default=True)
class Meta(type):
    pass


@model
class User:
    id: int
    name: str = my_field(default="anon")
    flag: bool = my_field(kw_only=False, default=False)


class Frozen(metaclass=Meta):
    x: int


def go() -> None:
    u = User(id=1, name="a")
    reveal_type(u.id)
    f = Frozen(x=1)
    reveal_type(f.x)
    f.x = 2


try:
    go()
except Exception as e:
    print(type(e).__name__)
