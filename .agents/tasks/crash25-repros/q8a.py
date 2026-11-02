from collections.abc import Callable

def decorate[T](callback: Callable[[T], None]) -> T:
    raise NotImplementedError

class C:
    @decorate
    def __new__(cls):
        pass

C()
