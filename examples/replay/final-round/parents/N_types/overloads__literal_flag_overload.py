# area: overloads
# hypothesis: overload resolution with Literal[True]/Literal[False]/bool fallbacks and union arguments.
# spec: typing spec, overload.html "Overload call evaluation" (step 5: union expansion).
from typing import Literal, overload, reveal_type


@overload
def load(raw: Literal[True]) -> bytes: ...
@overload
def load(raw: Literal[False] = ...) -> str: ...
@overload
def load(raw: bool) -> str | bytes: ...
def load(raw: bool = False) -> str | bytes:
    return b"x" if raw else "x"


def pick(flag: bool, lit: Literal[True, False]) -> None:
    reveal_type(load(True))
    reveal_type(load())
    reveal_type(load(flag))
    reveal_type(load(lit))  # union expansion: str | bytes


pick(True, False)
print(load(True), load())
