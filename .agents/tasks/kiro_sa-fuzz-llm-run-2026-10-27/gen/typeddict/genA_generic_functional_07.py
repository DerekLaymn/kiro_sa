from typing import reveal_type  # noqa

from typing import Generic, TypedDict, TypeVar

T = TypeVar("T")


class Resp(TypedDict, Generic[T]):
    data: T
    errors: list[str]


Fn = TypedDict("Fn", {"class": int, "ok": bool})


def first(r: Resp[T]) -> T:
    return r["data"]


def go() -> None:
    r: Resp[int] = {"data": 1, "errors": []}
    reveal_type(first(r))
    reveal_type(r["data"])
    f: Fn = {"class": 1, "ok": True}
    reveal_type(f["class"])
    reveal_type(first({"data": "s", "errors": []}))
    print(r, f)


go()
