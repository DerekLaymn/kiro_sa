from typing import Sequence, TypeIs, TypeVar, reveal_type

T = TypeVar("T")


def is_seq_of(x: Sequence[object], t: type[T]) -> TypeIs[Sequence[T]]:
    return all(isinstance(i, t) for i in x)


def is_list[T](x: Sequence[T]) -> TypeIs[list[T]]:
    return isinstance(x, list)


def f(x: Sequence[int | str]) -> int:
    if is_seq_of(x, int):
        reveal_type(x)
        return sum(x)
    reveal_type(x)
    return 0


def g(x: Sequence[int] | tuple[str, ...]) -> int:
    if is_list(x):
        reveal_type(x)
        return 1
    reveal_type(x)
    return 2


print(f([1, 2]), f(["a"]), g([1]), g(("a",)))
