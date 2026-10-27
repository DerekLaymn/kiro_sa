from typing import reveal_type  # noqa

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class P:
    x: int


@dataclass(frozen=True)
class Q(P):
    y: int = 0


def go() -> Q:
    q = Q(1, 2)
    r = replace(q, y=5)
    reveal_type(r)
    return r


def mutate(q: Q) -> None:
    try:
        q.x = 3  # error: frozen
    except Exception as e:
        print(type(e).__name__)


mutate(go())
