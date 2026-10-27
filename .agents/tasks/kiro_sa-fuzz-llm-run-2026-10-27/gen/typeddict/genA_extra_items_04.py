from typing import reveal_type  # noqa

from typing_extensions import TypedDict


class Movie(TypedDict, extra_items=int):
    name: str


def go() -> None:
    m: Movie = {"name": "x", "rating": 5}
    reveal_type(m["name"])
    reveal_type(m["rating"])
    bad: Movie = {"name": "y", "rating": "no"}
    print(m, bad)


go()
