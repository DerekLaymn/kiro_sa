# area: narrowing_user
# hypothesis: TypeIs narrows both branches so the negative branch excludes str, while TypeGuard narrows only the positive branch, and a generic TypeIs keeps the element type.
# origin: llm
# hypothesis: TypeIs narrows both branches so the negative branch excludes str, while TypeGuard narrows only the positive branch; attribute and subscript narrowing follow the same rules.
from typing import TypeGuard, TypeIs, TypeVar, reveal_type, assert_type

T = TypeVar('T')


def is_str(value: int | str) -> TypeIs[str]:
    return isinstance(value, str)


def is_str_guard(value: int | str) -> TypeGuard[str]:
    return isinstance(value, str)


def is_same(value: T, kind: type[T]) -> TypeIs[T]:
    return isinstance(value, kind)


class Box:
    def __init__(self, item: int | str) -> None:
        self.item = item


def describe(box: Box, items: list[int | str]) -> str:
    if is_str(box.item):
        reveal_type(box.item)
    else:
        reveal_type(box.item)
    if is_str_guard(items[0]):
        reveal_type(items[0])
    else:
        reveal_type(items[0])
    return f'{box.item}/{items[0]}'


def generic_branch(value: int | str) -> int:
    if is_same(value, int):
        assert_type(value, int)
        return value + 1
    reveal_type(value)
    return len(value)


b = Box(3)
print(describe(b, [1, 'x']))
print(describe(Box('hi'), ['a']))
print(generic_branch(4), generic_branch('abc'))
