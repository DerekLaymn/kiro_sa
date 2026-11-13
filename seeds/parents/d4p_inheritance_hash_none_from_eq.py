# area: inheritance_mro
# hypothesis: A class defining __eq__ without __hash__ has __hash__ = None at runtime; mypy and ty do not model it (mypy#20230), and `assert Plain.__hash__ is None` makes the next lines unreachable for ty (Never) and silent for mypy. Vary: Hashable parameter, set/dict key, dataclass(eq=True).
# origin: generated program (not kept) (seed-a43a619b6518); results/rounds/round-3-report.md section 5 item 8
from dataclasses import dataclass
from typing import reveal_type


class Plain:
    def __eq__(self, value: object) -> bool:
        return True


@dataclass(eq=True)
class Record:
    name: str


class Keyed(Plain):
    def __hash__(self) -> int:
        return 1


assert Plain.__hash__ is None
assert Record("a").name == "a"
assert Record.__hash__ is None
reveal_type(Keyed().__hash__())
assert hash(Keyed()) == 1
unhashable = False
try:
    hash(Plain())
except TypeError:
    unhashable = True
assert unhashable
