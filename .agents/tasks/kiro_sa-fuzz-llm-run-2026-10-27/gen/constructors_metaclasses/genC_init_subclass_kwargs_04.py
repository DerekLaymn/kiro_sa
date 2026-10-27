from typing import Any, reveal_type


class Plugin:
    registry: dict[str, type["Plugin"]] = {}

    def __init_subclass__(cls, *, key: str, weight: int = 0, **kw: Any) -> None:
        super().__init_subclass__(**kw)
        cls.registry[key] = cls
        cls.weight = weight


class A(Plugin, key="a", weight=2):
    pass


class B(Plugin, key="b"):
    pass


try:
    class C(Plugin):  # type: ignore
        pass
except TypeError:
    print("TypeError")

reveal_type(A.weight)
print(A.weight, B.weight, sorted(Plugin.registry))
