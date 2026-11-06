# area: tuples_unpacking
# hypothesis: When a nested star target raises during a multi-target assignment, the earlier target keeps its new value, so the except handler's match should see 'bad' and return it.
# origin: runs/day8/parents/H_new/d7p_tuples_unpacking_partial_unpack_except_ty.py
# area: tuples_unpacking
# hypothesis: When a nested star target raises during a multi-target assignment, the earlier target keeps its new value, so the except handler's match sees 'bad' and returns it.
from typing import reveal_type


def take(items: tuple[int, ...]) -> str:
    head: int | str = 0
    try:
        head, (a, *b, c) = 'bad', items
    except ValueError:
        reveal_type(head)
        match head:
            case str() as s:
                return s
            case int():
                return 'int'
    return 'unreachable'


result = take((1,))
reveal_type(result)
assert result == 'bad'
