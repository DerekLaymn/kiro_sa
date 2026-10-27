from collections.abc import Callable
from typing import reveal_type


def run(x: int | Callable[[], int] | str) -> int:
    if callable(x):
        reveal_type(x)
        return x()
    reveal_type(x)
    return 0


print(run(lambda: 3), run(1), run("s"))
