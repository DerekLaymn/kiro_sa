# area: descriptors_properties / callables
# explores: functools.cached_property and functools.partial typing
from functools import cached_property, partial
from typing import reveal_type


class Report:
    def __init__(self, rows: list[int]) -> None:
        self.rows = rows

    @cached_property
    def total(self) -> int:
        return sum(self.rows)


def power(base: int, exp: int) -> int:
    return base**exp


square = partial(power, exp=2)
r = Report([1, 2, 3])
reveal_type(r.total)  # int
reveal_type(Report.total)  # cached_property[int]
reveal_type(square)  # partial[int]
reveal_type(square(3))  # int
print(r.total, square(3))
try:
    square("3")  # expect-error: str is not int
except TypeError as exc:
    print("runtime:", exc)
