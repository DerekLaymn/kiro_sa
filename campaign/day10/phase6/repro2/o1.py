from typing import overload, reveal_type


@overload
def describe(x: object) -> str: ...
@overload
def describe(x: int) -> int: ...
def describe(x: object) -> object:
    return x


assert describe(3) == 4
reveal_type(describe("a"))
reveal_type(describe)
reveal_type(describe(3))
