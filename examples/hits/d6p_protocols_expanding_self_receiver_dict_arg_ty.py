# area: protocols
# hypothesis: A protocol method that annotates self as Stream[dict[str, T]] with an old-style TypeVar, with a plain class passed in argument position instead of assignment, should be accepted by mypy and pyright; ty may overflow its stack or reject it.
# origin: runs/day6/parents/A_ty_crash/d4v_protocols_expanding_self_receiver.py
# area: protocols
# hypothesis: A protocol method that annotates self as Stream[dict[str, T]] with an old-style TypeVar, with a plain class passed in argument position instead of assignment, is accepted by mypy and pyright; ty may overflow its stack or reject it.
from __future__ import annotations
from typing import Protocol, TypeVar, reveal_type

T = TypeVar('T')


class Stream(Protocol[T]):
    def flatten(self: Stream[dict[str, T]]) -> None: ...


class Impl:
    def flatten(self) -> None:
        print('flattened')


def take(s: Stream[int]) -> int:
    return 1


Impl().flatten()
reveal_type(take(Impl()))
print(take(Impl()))
