from collections.abc import Hashable
from dataclasses import dataclass


class Plain:
    def __eq__(self, value: object) -> bool:
        return True


class Sub(Plain): ...


class Keyed(Plain):
    def __hash__(self) -> int:
        return 1


@dataclass
class Record:
    name: str


def need(x: Hashable) -> int:
    return hash(x)


need(Keyed())  # fine
need(Record("a"))  # runtime: TypeError (dataclass eq=True, frozen=False)
need(Plain())  # runtime: TypeError: unhashable type: 'Plain'
need(Sub())  # runtime: TypeError: unhashable type: 'Sub'
