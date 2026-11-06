# area: tuples_unpacking
# hypothesis: When a later target of a tuple assignment raises, the earlier target keeps its new value, so the except branch sees 'bad' even though checkers may narrow value to Literal[1] or treat the assignment as atomic.
# origin: runs/day8/parents/H_new/d7p_tuples_unpacking_partial_unpack_except_ty.py
# area: tuples_unpacking
# hypothesis: When a later target of a tuple assignment raises, the earlier target keeps its new value, so the except branch sees 'bad' even though checkers may narrow value to Literal[1] or treat the assignment as atomic.
from typing import reveal_type


class Box[T]:
    def __init__(self, inner: T) -> None:
        self.inner = inner


def split(box: Box[tuple[int, ...]]) -> str:
    value: int | str = 1
    try:
        value, (a, b) = 'bad', box.inner
    except ValueError:
        reveal_type(value)
        return value if isinstance(value, str) else str(value)
    return 'unreachable'


pair: Box[tuple[int, ...]] = Box((1,))
result = split(pair)
reveal_type(result)
assert result == 'bad'
