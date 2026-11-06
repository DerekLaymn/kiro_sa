# area: dataclasses
# hypothesis: A dataclass InitVar argument of type Any is accepted by a __post_init__ that has one compatible overload alongside an unrelated str overload, and the instance label reflects the init value.
# origin: runs/day8/parents/N_seeds_a/dataclasses__overloaded_post_init.py
# area: dataclasses
# hypothesis: a dataclass InitVar fed an Any argument is accepted by a __post_init__ with one compatible overload alongside an unrelated str overload
from dataclasses import InitVar, dataclass
from typing import Any, overload, reveal_type


@dataclass
class Record:
    value: InitVar[int]
    label: str = "r"

    @overload
    def __post_init__(self, value: int) -> None: ...
    @overload
    def __post_init__(self, value: str) -> None: ...
    def __post_init__(self, value: int | str) -> None:
        self.label = self.label + str(value)


def build(v: Any) -> Record:
    return Record(v)


r = Record(1)
reveal_type(r)
r2 = build(2)
reveal_type(r2.label)
assert r.label == "r1"
assert r2.label == "r2"
