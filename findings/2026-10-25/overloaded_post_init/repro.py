from dataclasses import InitVar, dataclass
from typing import overload


@dataclass
class Record:
    value: InitVar[int]

    @overload
    def __post_init__(self, value: int) -> None: ...
    @overload
    def __post_init__(self, value: str) -> None: ...
    def __post_init__(self, value: int | str) -> None:
        print(value)


Record(1)
