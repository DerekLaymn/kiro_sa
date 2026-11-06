from collections.abc import Callable


class C:
    __call__: Callable[[], int]


class D:
    def __init__(self) -> None:
        self.__call__ = lambda: 1


try:
    C()()
except TypeError as exc:
    print("C:", exc)

try:
    D()()
except TypeError as exc:
    print("D:", exc)
