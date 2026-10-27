from collections.abc import Callable
from typing import reveal_type


class Task[**P, R]:
    def __init__(self, f: Callable[P, R]) -> None:
        self.f = f


def one(a: int) -> int:
    return a


t1: Task[[int], int] = Task(one)
t2: Task[..., int] = t1
t3: Task[[str], int] = t1  # error
reveal_type(t2)
print(t1, t2, t3)
