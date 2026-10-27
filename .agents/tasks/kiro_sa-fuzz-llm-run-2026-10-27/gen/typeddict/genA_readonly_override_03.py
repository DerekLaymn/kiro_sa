from typing import reveal_type  # noqa

from typing import NotRequired, ReadOnly, TypedDict


class Movie(TypedDict):
    name: ReadOnly[str]
    year: int


class Sub(Movie):
    name: ReadOnly[str]
    extra: NotRequired[int]


def edit(m: Movie) -> None:
    m["year"] = 1
    m["name"] = "x"
    del m["year"]
    m.update({"year": 3})
    m.setdefault("year", 4)
    m.pop("year")


def go() -> None:
    s: Sub = {"name": "n", "year": 1}
    edit(s)
    reveal_type(s["name"])


try:
    go()
except Exception as e:
    print(type(e).__name__)
