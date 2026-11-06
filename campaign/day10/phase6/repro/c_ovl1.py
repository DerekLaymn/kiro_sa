from typing import overload, reveal_type


@overload
def describe(x: object) -> str: ...
@overload
def describe(x: int) -> int: ...
def describe(x: object) -> object:
    return x + 1 if isinstance(x, int) else "obj"


assert describe(3) == 4
reveal_type(1)
