# area: narrowing_user
# hypothesis: type(value) == C guards narrow an Any-typed value differently in ty than in mypy and pyright when the compared class uses a metaclass with a custom __eq__, and when the guard uses != or a union-typed sample.
# origin: runs/day10/parents/N_flow/s3r1_ty_type_equality_narrowing_any.py
# area: narrowing_user
# hypothesis: type(value) == C guards narrow an Any-typed value differently in ty than in mypy and pyright when the compared class uses a metaclass with a custom __eq__, and when the guard uses != or a union-typed sample.
from typing import Any, reveal_type


class EqualMeta(type):
    def __eq__(cls, other: object) -> bool:
        return True

    def __hash__(cls) -> int:
        return 0


class Equal(metaclass=EqualMeta):
    pass


def eq_guard(value: Any, sample: dict[str, int] | tuple[int, int]) -> str:
    if type(value) == type(sample):
        reveal_type(value)
        return 'matched'
    reveal_type(value)
    return 'other'


def neq_guard(value: Any, sample: int) -> str:
    if type(value) != type(sample):
        reveal_type(value)
        return 'different'
    reveal_type(value)
    return 'same'


def metaclass_guard(value: Equal | str, sample: str) -> str:
    if type(value) == type(sample):
        reveal_type(value)
        return 'eq'
    reveal_type(value)
    return 'neq'


def object_guard(value: object, sample: int) -> str:
    if type(value) == type(sample):
        reveal_type(value)
        return 'int'
    return 'not int'


print(eq_guard({'a': 1}, {'b': 2}))
print(neq_guard('x', 3))
print(metaclass_guard(Equal(), 'q'))
print(object_guard(5, 0))
print(object_guard('s', 0))
