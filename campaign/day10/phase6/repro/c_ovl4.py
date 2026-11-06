from typing import overload, reveal_type


@overload
def describe(x: object) -> str: ...
@overload
def describe(x: int) -> int: ...
def describe(x: object) -> object:
    return x + 1 if isinstance(x, int) else "obj"


reveal_type(describe(3))
assert describe(3) == 4
reveal_type(describe("a"))
