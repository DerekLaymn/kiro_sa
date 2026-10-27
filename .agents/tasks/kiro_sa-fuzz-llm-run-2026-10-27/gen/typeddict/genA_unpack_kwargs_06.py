from typing import reveal_type  # noqa

from typing import NotRequired, Required, TypedDict, Unpack


class Opts(TypedDict, total=False):
    verbose: bool
    level: Required[int]


class Opts2(Opts):
    name: NotRequired[str]


def f(**kw: Unpack[Opts2]) -> int:
    reveal_type(kw)
    reveal_type(kw["level"])
    reveal_type(kw.get("name"))
    return kw["level"]


def go() -> None:
    f(level=1)
    f(level=1, verbose=True, name="n")
    f(verbose=True)
    f(level="x")
    f(level=1, other=2)
    o: Opts2 = {"level": 3}
    f(**o)


try:
    go()
except Exception as e:
    print(type(e).__name__)
