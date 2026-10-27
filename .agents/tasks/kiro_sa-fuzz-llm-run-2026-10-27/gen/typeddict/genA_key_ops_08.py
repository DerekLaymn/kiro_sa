from typing import reveal_type  # noqa

from typing import Literal, NotRequired, TypedDict


class T(TypedDict):
    a: int
    b: str
    c: NotRequired[bytes]


def go(t: T, k: Literal["a", "b"], k2: str) -> None:
    reveal_type(t[k])
    reveal_type(t[k2])
    reveal_type(t.get(k2))
    reveal_type(t | {"a": 2})
    reveal_type(t.keys())
    reveal_type(t.items())
    reveal_type(t.copy())
    for key in t:
        reveal_type(key)
    print(t)


try:
    go({"a": 1, "b": "x"}, "a", "b")
except Exception as e:
    print(type(e).__name__)
