from typing import Iterable, Sequence, TypeVar, overload, reveal_type

T = TypeVar("T")
K = TypeVar("K")


@overload
def first(x: Sequence[T]) -> T: ...
@overload
def first(x: Iterable[T]) -> T | None: ...
def first(x: Iterable[T]) -> T | None:
    for i in x:
        return i
    return None


@overload
def get(d: dict[K, T], k: K) -> T | None: ...
@overload
def get(d: dict[K, T], k: K, default: T) -> T: ...
def get(d: dict[K, T], k: K, default: T | None = None) -> T | None:
    return d.get(k, default)


def f() -> None:
    reveal_type(first([1, 2]))
    reveal_type(first({1, 2}))
    reveal_type(first("ab"))
    reveal_type(first(iter([b"x"])))
    reveal_type(get({"a": 1}, "a"))
    reveal_type(get({"a": 1}, "a", 0))
    reveal_type(get({"a": 1}, "a", "s"))


f()
print(first([1]), first(set()), get({1: 2}, 3, 4))
