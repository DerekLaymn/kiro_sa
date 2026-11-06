from dataclasses import InitVar, dataclass
from typing import overload


@dataclass
class Record:
    value: InitVar[int]

    @overload
    def __post_init__(self, value: str) -> None: ...
    @overload
    def __post_init__(self, value: bytes) -> None: ...
    def __post_init__(self, value: object) -> None:
        print(type(value))


Record(1)
