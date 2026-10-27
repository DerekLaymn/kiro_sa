from typing import reveal_type  # noqa

from typing import Mapping, NotRequired, TypedDict


class P(TypedDict):
    x: int


class Q(TypedDict):
    x: int
    y: NotRequired[int]


class R(TypedDict):
    x: float


def take_p(p: P) -> None:
    print(p)


def take_r(r: R) -> None:
    print(r)


def take_map(m: Mapping[str, object]) -> None:
    print(m)


def go(q: Q, p: P) -> None:
    take_p(q)
    take_q: Q = p
    take_r(p)
    take_map(q)
    d: dict[str, object] = q
    print(take_q, d)


go({"x": 1}, {"x": 2})
