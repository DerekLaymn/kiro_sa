from collections.abc import Callable


def store(c: Callable[[int], None]) -> None:
    c.y = 1


def load(c: Callable[[int], None]) -> int:
    return c.y


class A:
    def __call__(self, x: int) -> None: ...

    def setup(self: Callable[[int], None]) -> None:
        self.y = 1
        print(self.y)


a = A()
a.setup()
