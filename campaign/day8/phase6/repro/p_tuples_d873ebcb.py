# area: tuples_unpacking
# hypothesis: When a later nested star target fails to unpack, the earlier target's store of 'bad' remains visible in the except branch, so the handler sees 'bad' rather than the old int value.
# origin: runs/day8/parents/H_new/d7p_tuples_unpacking_partial_unpack_except_ty.py
# area: tuples_unpacking
# hypothesis: When a later nested star target raises, the earlier target store of 'bad' stays visible in the except branch.
from typing import reveal_type


def pick(items: tuple[int, ...]) -> str:
    value: int | str = 1
    try:
        value, (a, *b, c) = 'bad', items
    except ValueError:
        reveal_type(value)
        return value if isinstance(value, str) else str(value)
    return 'unreachable'


result = pick((1,))
reveal_type(result)
assert result == 'bad'
