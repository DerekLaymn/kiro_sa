# area: tuples_unpacking
# hypothesis: An exception raised by a later unpacking target leaves the earlier target's store in place: CPython reaches the except branch with value == 'bad'. ty 0.0.97 and pyright 1.1.414 reveal Literal[1] there (the multi-target assignment treated as atomic), mypy reveals int | str. Vary: a nested star target, a match/isinstance narrowing in the handler, a for-loop target, an attribute or subscript target as the first element, a finally block, with/del.
# origin: runs/day7/gen/tuples_unpacking/tuples_unpacking__partial_unpack_exception__mut0_1a265ba6.py (seed-1b309724816f); two sibling mutants (a5e7d2e6, 662f76ab) show the same finding; hand seed seeds/tuples_unpacking/partial_unpack_exception.py
# runtime: value keeps "bad" after the ValueError raised by the second target
from typing import reveal_type


def split(items: tuple[int, ...]) -> str:
    value: int | str = 1
    try:
        value, (a, b) = "bad", items
    except ValueError:
        reveal_type(value)
        return value if isinstance(value, str) else str(value)
    return "unreachable"


result = split((1,))
reveal_type(result)
assert result == "bad"
