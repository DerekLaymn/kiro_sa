from collections.abc import Callable


class A:
    def __init__(self: Callable[[int], None], x: int) -> None:
        self.x = x


a = A(1)
print(a.x)
