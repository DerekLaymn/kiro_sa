from typing import Any, reveal_type


class Meta(type):
    def __call__(cls, *args: Any, **kwargs: Any) -> int:
        return 42


class K(metaclass=Meta):
    def __init__(self, x: str) -> None:
        raise RuntimeError("never")


v = K()
reveal_type(v)
print(v + 1)
w = K("a", "b", z=1)
reveal_type(w)
print(w)
