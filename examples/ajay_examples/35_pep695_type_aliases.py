# area: recursive_aliases
# explores: generic `type` aliases (TypeVar, ParamSpec), recursive generic aliases, alias runtime objects
from collections.abc import Callable
from typing import reveal_type

type Pair[T] = tuple[T, T]
type Handler[**P] = Callable[P, None]
type Nested[T] = T | list[Nested[T]]
type StrMap = dict[str, int]


def swap[T](p: Pair[T]) -> Pair[T]:
    return p[1], p[0]


def register[**P](h: Handler[P]) -> Handler[P]:
    return h


def depth[T](n: Nested[T]) -> int:
    if isinstance(n, list):
        return 1 + max((depth(x) for x in n), default=0)
    return 0


@register
def on_save(path: str, force: bool = False) -> None:
    print("saved", path, force)


counts: StrMap = {"a": 1}
reveal_type(swap((1, 2)))  # tuple[int, int]
reveal_type(on_save)  # (path: str, force: bool = ...) -> None
reveal_type(counts)  # dict[str, int]
reveal_type(Pair)  # TypeAliasType
on_save("f.txt")
print(swap(("x", "y")), counts, Pair.__value__, depth([1, [2, [3]]]))
bad: Pair[int] = (1, "2")  # expect-error
mixed: StrMap = {"a": "b"}  # expect-error
