from collections.abc import Iterable
from typing import reveal_type


def flat(values: Iterable[int]) -> None:
    # control: the unpack fails before any target is bound; Literal[0] is right
    state = 0
    try:
        first, second = values
        state = 1
    except ValueError:
        reveal_type(state)


def flat_then_unpack(values: Iterable[int]) -> None:
    # `state` is bound first, the second target's unpack fails afterwards
    state = 0
    try:
        state, (first, second) = 1, values
    except ValueError:
        reveal_type(state)


flat([1])
flat_then_unpack([1])
