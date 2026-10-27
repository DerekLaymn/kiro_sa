from typing import reveal_type


class P:
    def __new__(cls, x: int) -> "P":
        obj = super().__new__(cls)
        return obj

    def __init__(self, x: int, y: str = "d") -> None:
        self.x = x
        self.y = y


p = P(1)
reveal_type(p)
print(p.x, p.y)
try:
    P(1, "z")  # type: ignore
except TypeError:
    print("TypeError")
p2 = P(2)
print(p2.y)
