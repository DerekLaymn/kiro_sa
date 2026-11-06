from collections.abc import Callable


class A:
    def __call__(self, x: int) -> None: ...

    def setup(self: Callable[[int], None]) -> None:
        self.y = 1


a = A()
a.setup()
print(a.y)
