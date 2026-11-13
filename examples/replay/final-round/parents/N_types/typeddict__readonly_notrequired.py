# area: typeddict
# hypothesis: ReadOnly items cannot be assigned; NotRequired items need a guard; Unpack[TD] checks kwargs.
# spec: typing spec, typeddict.html.
from typing import NotRequired, ReadOnly, TypedDict, Unpack, reveal_type


class Movie(TypedDict):
    title: ReadOnly[str]
    year: NotRequired[int]


class Options(TypedDict, total=False):
    verbose: bool
    level: int


def configure(**kwargs: Unpack[Options]) -> None:
    reveal_type(kwargs)
    print(kwargs)


m: Movie = {"title": "Up"}
if "year" in m:
    reveal_type(m["year"])
print(m.get("year", 0))
m["title"] = "Down"  # expect-error: ReadOnly
configure(verbose=True)
configure(level="high")  # expect-error
configure(color=1)  # expect-error: unknown key
