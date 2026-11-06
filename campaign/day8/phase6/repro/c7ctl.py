from dataclasses import InitVar, dataclass


@dataclass
class Record:
    value: InitVar[int]

    def __post_init__(self, value: str) -> None:
        print(type(value))


Record(1)
