# Bug 4 (ty): see examples/bugs/README.md for the issue link and the expected/actual result.
from collections.abc import Hashable


class Plain:
    def __eq__(self, value: object) -> bool:
        return True


class Sub(Plain): ...


class Keyed(Plain):
    def __hash__(self) -> int:
        return 1


def need(x: Hashable) -> int:
    return hash(x)


need(Keyed())  # fine
need(Plain())  # runtime: TypeError: unhashable type: 'Plain'
need(Sub())    # runtime: TypeError: unhashable type: 'Sub'
