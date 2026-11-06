from typing import Literal, overload, reveal_type


@overload
def parse(kind: Literal["int"]) -> int: ...
@overload
def parse(kind: str) -> str: ...
def parse(kind: str) -> int | str:
    return 1 if kind == "int" else kind


k: str = "int"
reveal_type(k)
reveal_type(parse(k))
print(type(parse(k)))
