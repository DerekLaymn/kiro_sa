from collections.abc import Hashable
from dataclasses import dataclass


@dataclass
class Record:
    name: str


class OnlyNe:
    def __ne__(self, value: object) -> bool:
        return True


class OnlyLt:
    def __lt__(self, value: object) -> bool:
        return True


class Restored(OnlyNe):
    pass


class NoneHash:
    __hash__ = None  # type: ignore[assignment]


class EqAndHash:
    def __eq__(self, value: object) -> bool:
        return True

    __hash__ = object.__hash__


def need(x: Hashable) -> int:
    return hash(x)


reveal_type(Record.__hash__)

need(Record("a"))  # expected error (dataclass eq, unhashable)
need(OnlyNe())  # ok
need(OnlyLt())  # ok
need(Restored())  # ok
need(NoneHash())  # expected error (__hash__ = None)
need(EqAndHash())  # ok
