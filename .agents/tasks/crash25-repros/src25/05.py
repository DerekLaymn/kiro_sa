# area: recursive_aliases
# origin: ruff mdtest pep695_type_aliases.md block 70
from typing import Callable, Concatenate

# error: [cyclic-type-alias-definition]
type Recursive[T] = int | Recursive[list[T]]

def _(value: Recursive[int]):
    reveal_type(value + 1)  # revealed: int
    reveal_type(1 + value)  # revealed: int

type RecursiveParamspec[**P] = Callable[[], RecursiveParamspec[Concatenate[int, P]]]

def paramspec_alias(func: RecursiveParamspec):
    reveal_type(func)  # revealed: () -> RecursiveParamspec[(int, /, *args: Unknown, **kwargs: Unknown)]

type RecursiveCallable[T] = Callable[[RecursiveCallable[T]], RecursiveCallable[T | RecursiveCallable[T]]]

def callable_alias(x: RecursiveCallable[int]):
    reveal_type(x)  # revealed: (RecursiveCallable[int], /) -> RecursiveCallable[int | RecursiveCallable[int]]

type GrowingList[T] = list[GrowingList[T | GrowingList[T]]]

def growing_list(x: GrowingList[int]):
    reveal_type(x)  # revealed: list[GrowingList[int | GrowingList[int]]]

type GrowingCallable[T] = Callable[[], GrowingCallable[T | GrowingCallable[T]] | None]

def growing_callable(x: GrowingCallable[int]):
    # revealed: (() -> GrowingCallable[int | GrowingCallable[int] | GrowingCallable[int | GrowingCallable[int]]] | None) | None
    reveal_type(x())
