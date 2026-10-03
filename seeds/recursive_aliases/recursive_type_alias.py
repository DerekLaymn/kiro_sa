# area: recursive_aliases (crash hunting: fix-point iteration)
# hypothesis: recursive PEP 695 aliases and mutually recursive generic aliases are resolved without
# panics/hangs, and still reject non-conforming values.
from typing import reveal_type

type Json = None | bool | int | float | str | list[Json] | dict[str, Json]
type Tree[T] = T | list[Tree[T]]
type A = list[B] | int
type B = dict[str, A]


def depth(j: Json) -> int:
    if isinstance(j, list):
        reveal_type(j)
        return 1 + max((depth(x) for x in j), default=0)
    if isinstance(j, dict):
        return 1 + max((depth(v) for v in j.values()), default=0)
    return 0


def flatten[T](t: Tree[T]) -> list[T]:
    if isinstance(t, list):
        return [y for x in t for y in flatten(x)]
    return [t]


a: A = [{"k": 1}, {"k": [{"z": 2}]}]
bad: Json = {"k": {1, 2}}  # expect-error: set is not Json
print(depth([1, [2, {"a": [3]}]]), flatten([1, [2, [3]]]), a)
