# area: dataclasses
# hypothesis: One compatible overload is enough to accept the generated InitVar call, and the runtime records the int argument's branch via isinstance narrowing.
# origin: runs/day8/parents/R_reserve3/rsv_dataclasses_223fff8f.py
# area: dataclasses
# hypothesis: One compatible overload is enough to accept the generated InitVar call, and the runtime records the int argument's branch via isinstance narrowing.
from dataclasses import InitVar, dataclass, field
from typing import overload, reveal_type


@dataclass
class Record:
    value: InitVar[int]
    seen: list[str] = field(default_factory=list)

    @overload
    def __post_init__(self, value: int) -> None: ...
    @overload
    def __post_init__(self, value: str) -> None: ...
    def __post_init__(self, value: int | str) -> None:
        if isinstance(value, int):
            self.seen.append('int')
        else:
            self.seen.append('str')


def make(v: int) -> Record:
    rec = Record(v)
    reveal_type(rec)
    reveal_type(rec.seen)
    return rec


rec = make(1)
assert rec.seen == ['int'], rec.seen
print(rec.seen)
