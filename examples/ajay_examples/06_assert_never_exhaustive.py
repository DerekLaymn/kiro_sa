# area: narrowing_builtin
# explores: exhaustiveness over a union type alias with isinstance + assert_never (and a forgotten case)
from dataclasses import dataclass
from typing import assert_never, reveal_type


@dataclass
class Ok:
    value: int


@dataclass
class Err:
    message: str


@dataclass
class Pending:
    pass


type Result = Ok | Err | Pending


def handle(r: Result) -> str:
    if isinstance(r, Ok):
        return f"ok {r.value}"
    elif isinstance(r, Err):
        return f"err {r.message}"
    elif isinstance(r, Pending):
        return "pending"
    else:
        reveal_type(r)  # Never
        assert_never(r)


def forgot(r: Result) -> str:
    if isinstance(r, Ok):
        return "ok"
    elif isinstance(r, Err):
        return "err"
    else:
        assert_never(r)  # expect-error: Pending is not handled


print(handle(Ok(1)), handle(Err("x")), handle(Pending()), forgot(Ok(2)))
try:
    forgot(Pending())
except AssertionError as exc:
    print("runtime:", exc)
