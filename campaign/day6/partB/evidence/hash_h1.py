from collections.abc import Hashable


class B:
    def __eq__(self, other: object) -> bool:
        return True


def need(h: Hashable) -> None:
    hash(h)


try:
    need(B())
except TypeError as e:
    print("TypeError", e)
