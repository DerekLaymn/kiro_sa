from collections.abc import Callable
from typing import reveal_type


class Pt:
    def __init__(self, x: int, y: int = 0) -> None:
        self.x = x
        self.y = y


mk1: Callable[[int], Pt] = Pt
mk2: Callable[[str], Pt] = Pt  # error
reveal_type(mk1(1))
reveal_type(list(map(Pt, [1, 2])))
print(mk1(1).y, mk2 if False else 0)
