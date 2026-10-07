# area: constructors_metaclasses
# explores: metaclass __getitem__ (class subscription), metaclass properties and __len__ on the class,
# metaclass members not available on instances
from typing import Any, reveal_type


class Registry(type):
    _items: dict[str, type] = {}

    def __new__(mcs, name: str, bases: tuple[type, ...], ns: dict[str, Any]) -> "Registry":
        cls = super().__new__(mcs, name, bases, ns)
        Registry._items[name.lower()] = cls
        return cls

    def __getitem__(cls, key: str) -> type:
        return Registry._items[key]

    @property
    def label(cls) -> str:
        return cls.__name__.upper()

    def __len__(cls) -> int:
        return len(Registry._items)


class Model(metaclass=Registry):
    pass


class User(Model):
    pass


reveal_type(Model["user"])  # type (via the metaclass __getitem__)
reveal_type(User.label)  # str
reveal_type(len(User))  # int
reveal_type(type(User))  # type[Registry]
print(Model["user"], User.label, len(User))
try:
    print(User().label)  # expect-error: metaclass property is not on instances
except AttributeError as exc:
    print("runtime:", exc)
