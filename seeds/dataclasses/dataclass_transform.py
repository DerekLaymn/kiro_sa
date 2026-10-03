# area: dataclasses
# hypothesis: dataclass_transform on a base class / decorator / metaclass synthesizes __init__,
# respects kw_only_default and field specifiers.
# spec: typing spec, dataclasses.html "dataclass_transform".
from typing import Any, dataclass_transform, reveal_type


def model_field(*, default: Any = None, init: bool = True) -> Any:
    return default


@dataclass_transform(kw_only_default=True, field_specifiers=(model_field,))
class ModelMeta(type):
    def __new__(mcs, name: str, bases: tuple[type, ...], ns: dict[str, Any]) -> "ModelMeta":
        cls = super().__new__(mcs, name, bases, ns)
        fields = [k for k in ns.get("__annotations__", {})]

        def __init__(self: Any, **kw: Any) -> None:
            for k in fields:
                setattr(self, k, kw.get(k, ns.get(k)))

        cls.__init__ = __init__  # type: ignore[misc]
        return cls


class Model(metaclass=ModelMeta):
    pass


class User(Model):
    id: int
    name: str = model_field(default="anon")
    secret: str = model_field(default="", init=False)


u = User(id=1)
reveal_type(u.name)
print(u.id, u.name)
try:
    User(1)  # expect-error: kw_only_default=True
except TypeError as exc:
    print('runtime:', type(exc).__name__)
try:
    User(id=1, secret="x")  # expect-error: init=False
except TypeError as exc:
    print('runtime:', type(exc).__name__)
