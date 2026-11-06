# area: narrowing_user
# hypothesis: TypeIs removes str from the negative branch of a union while TypeGuard does not, and attribute, index and generic TypeIs narrowing follow the same rules.
# origin: llm
# Hypothesis: TypeIs removes str from the negative branch of a union while TypeGuard does not; attribute and index narrowing follow TypeIs rules.
from typing import TypeGuard, TypeIs, TypeVar, reveal_type

T = TypeVar('T')


def is_str_guard(v: object) -> TypeGuard[str]:
    return isinstance(v, str)


def is_str_is(v: object) -> TypeIs[str]:
    return isinstance(v, str)


def is_all_of(v: list[T], kind: type[T]) -> TypeIs[list[T]]:
    return all(isinstance(x, kind) for x in v)


class Holder:
    def __init__(self, item: int | str) -> None:
        self.item = item


def check_union(x: int | str) -> str:
    if is_str_guard(x):
        reveal_type(x)
    else:
        reveal_type(x)
    if is_str_is(x):
        return x
    reveal_type(x)
    return str(x)


def check_members(h: Holder, pair: tuple[int | str, int | str]) -> str:
    if is_str_is(h.item):
        reveal_type(h.item)
        return h.item
    if is_str_is(pair[0]):
        reveal_type(pair[0])
        return pair[0]
    reveal_type(pair[0])
    return str(h.item) + str(pair[0])


def pick(items: list[int | str]) -> int:
    if is_all_of(items, str):
        reveal_type(items)
        return len(items)
    reveal_type(items)
    return -1


print(check_union(3), check_union('a'))
print(check_members(Holder(4), (1, 'x')), check_members(Holder('b'), ('y', 2)))
print(pick(['p', 'q']), pick([1]))
