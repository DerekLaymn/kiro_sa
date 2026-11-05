from typing import reveal_type


def control_atomic_rhs(items: list[int]) -> None:
    # RHS raises before any store: Literal[1] is correct
    value: int | str = 1
    try:
        value, other = "bad", items[5]
    except IndexError:
        reveal_type(value)


def control_next_statement(items: list[int]) -> None:
    # value is stored by a complete statement before the exception: correct to see "bad"
    value: int | str = 1
    try:
        value = "bad"
        items[5]
    except IndexError:
        reveal_type(value)


control_atomic_rhs([1])
control_next_statement([1])
