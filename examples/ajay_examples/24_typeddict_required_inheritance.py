# area: typeddict
# explores: Required inside total=False, NotRequired in a base, TypedDict inheritance and structural subtyping
from typing import NotRequired, Required, TypedDict, Unpack, reveal_type


class Opts(TypedDict, total=False):
    host: Required[str]
    port: int
    debug: bool


class Base(TypedDict):
    id: int
    tag: NotRequired[str]


class Child(Base):
    extra: list[int]


def connect(**kw: Unpack[Opts]) -> str:
    reveal_type(kw["host"])  # str
    reveal_type(kw.get("port"))  # int | None
    return f"{kw['host']}:{kw.get('port', 80)}"


def show(c: Child) -> str:
    reveal_type(c["extra"])  # list[int]
    reveal_type(c.get("tag"))  # str | None
    return str(c["id"])


child: Child = {"id": 1, "extra": [1]}
base: Base = child  # ok: Child is a structural subtype of Base
print(connect(host="h", port=1), connect(host="x"), show(child), base["id"])
try:
    connect(port=1)  # expect-error: missing required `host`
except KeyError as exc:
    print("runtime: KeyError", exc)
