# area: callables (operators)
# explores: __add__/__mul__/__rmul__, NotImplemented fallback to __radd__, sum() with a custom start
from typing import reveal_type


class Vec:
    def __init__(self, x: float, y: float) -> None:
        self.x, self.y = x, y

    def __add__(self, other: "Vec") -> "Vec":
        return Vec(self.x + other.x, self.y + other.y)

    def __mul__(self, k: float) -> "Vec":
        return Vec(self.x * k, self.y * k)

    def __rmul__(self, k: float) -> "Vec":
        return self * k

    def __repr__(self) -> str:
        return f"Vec({self.x}, {self.y})"


class Money:
    def __init__(self, cents: int) -> None:
        self.cents = cents

    def __add__(self, other: object) -> "Money":
        if isinstance(other, Money):
            return Money(self.cents + other.cents)
        return NotImplemented

    def __radd__(self, other: int) -> "Money":
        return Money(self.cents + other)


v = Vec(1, 2)
reveal_type(v + v)  # Vec
reveal_type(2 * v)  # Vec (int.__mul__ fails -> Vec.__rmul__)
reveal_type(v * 2)  # Vec
reveal_type(sum([Money(1), Money(2)]))  # Money | Literal[0]
print(v + v, 2 * v, v * 2, sum([Money(1), Money(2)], Money(0)).cents)
try:
    v + 1  # expect-error: int is not Vec
except AttributeError as exc:
    print("runtime:", exc)
