from collections.abc import Callable
from typing import reveal_type


class Handler[T]:
    def __init__(self, cb: Callable[[T], None]) -> None:
        self.cb = cb


def use(h: Handler[int]) -> None:
    h.cb(1)


hf = Handler[float](lambda x: print(x))
reveal_type(hf)
use(hf)  # attribute is mutable -> invariant: error expected
