from dataclasses import dataclass
from typing import TypeIs, reveal_type


def is_str(x: object) -> TypeIs[str]:
    return isinstance(x, str)


@dataclass
class Box:
    v: int | str
    items: list[int | str]


def f(b: Box) -> int:
    if is_str(b.v):
        reveal_type(b.v)
        return len(b.v)
    reveal_type(b.v)
    return b.v


def g(b: Box) -> int:
    if is_str(b.items[0]):
        reveal_type(b.items[0])
        b.items[0] = 3
        reveal_type(b.items[0])
        return 1
    return 0


def h(d: dict[str, int | str]) -> int:
    if is_str(d["k"]):
        reveal_type(d["k"])
        return len(d["k"])
    return d["k"]  # type: ignore[return-value]


print(f(Box(1, [])), f(Box("ab", [])), g(Box(1, ["a"])), h({"k": "xyz"}), h({"k": 4}))
