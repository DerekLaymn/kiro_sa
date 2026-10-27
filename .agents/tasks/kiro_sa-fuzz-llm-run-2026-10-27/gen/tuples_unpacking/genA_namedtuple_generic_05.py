from typing import reveal_type  # noqa

from typing import Generic, NamedTuple, TypeVar

T = TypeVar("T")


class Pair(NamedTuple, Generic[T]):
    left: T
    right: T
    tag: str = ""


def go() -> None:
    p = Pair(1, 2)
    reveal_type(p)
    a, b, c = p
    reveal_type(a)
    reveal_type(c)
    reveal_type(p[1])
    reveal_type(p[:2])
    reveal_type(p._replace(tag="x"))
    reveal_type(p._asdict())
    s: Pair[str] = Pair("a", "b")
    print(a, b, c, s)


go()
