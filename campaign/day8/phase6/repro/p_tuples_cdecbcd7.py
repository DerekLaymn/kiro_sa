# area: tuples_unpacking
# hypothesis: When a later nested star target raises ValueError, the earlier target keeps its newly assigned value inside the except handler, so checkers that treat the assignment as atomic will disagree.
# origin: runs/day8/parents/H_new/d7p_tuples_unpacking_partial_unpack_except_ty.py
# area: tuples_unpacking
# hypothesis: When a later target in a nested star unpacking raises, the earlier target keeps its new value in the except handler, so checkers that treat the assignment as atomic disagree.
from typing import reveal_type


def take(items: tuple[int, ...]) -> str:
    value: int | str = 1
    try:
        value, (first, *rest) = "bad", items
    except ValueError:
        reveal_type(value)
        match value:
            case str():
                return value
            case _:
                return str(value)
    return "unreachable"


result = take(())
reveal_type(result)
assert result == "bad"
