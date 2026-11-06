from typing import Protocol


class Sink(Protocol):
    def __call__(self, value: int) -> None: ...


s1: Sink = lambda x: None
s2: Sink = lambda x, /: None
s3: Sink = lambda *, value: None
s4: Sink = lambda y, z=0: None


def holder(s: Sink = lambda x: None) -> None: ...
