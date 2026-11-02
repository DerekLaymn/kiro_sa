from typing_extensions import (  # pyright: ignore[reportMissingModuleSource]
    TypeVar,
)
T5 = TypeVar("T5", default="T5")
TA_C = list[T5]
def func2(d1: TA_D, d2: TA_D[int], d3: TA_D[int, float]):
    reveal_type(d1, expected_text="tuple[str, str, list[str]]")
