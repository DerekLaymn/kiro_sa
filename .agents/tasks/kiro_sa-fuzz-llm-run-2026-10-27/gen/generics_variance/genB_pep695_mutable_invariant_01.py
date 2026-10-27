from typing import reveal_type


class Box[T]:
    def __init__(self, items: list[T]) -> None:
        self.items = items


def take(b: Box[float]) -> None:
    reveal_type(b.items)


bi = Box([1, 2])
reveal_type(bi)
take(bi)  # error: invariant
