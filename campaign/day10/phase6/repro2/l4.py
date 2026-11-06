from typing import Protocol


class Sink(Protocol):
    def __call__(self, value: int) -> None: ...


def use(s: Sink) -> None: ...


use(lambda x: None)
use(lambda *args: None)
use(lambda x, **kw: None)
use(lambda *a, **k: None)
use(lambda value=0: None)
