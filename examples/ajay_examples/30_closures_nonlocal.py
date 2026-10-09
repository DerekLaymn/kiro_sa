# area: narrowing_builtin (scopes)
# explores: narrowing visible in closures, rebinding after a lambda captures a variable (unsound),
# nonlocal counters, default-argument capture in comprehension lambdas
from collections.abc import Callable
from typing import reveal_type


def narrowed_closure(x: int | None) -> int:
    if x is None:
        return 0

    def inner() -> int:
        reveal_type(x)  # int if the checker sees that x is never reassigned
        return x + 1

    return inner()


def reassigned_later(x: int | None) -> Callable[[], int]:
    if x is None:
        x = 0
    f = lambda: x + 1  # expect-error: x is rebound to None below, so the closure may see None
    x = None
    return f


def counter() -> Callable[[], int]:
    count = 0

    def step() -> int:
        nonlocal count
        count += 1
        reveal_type(count)  # int
        return count

    return step


def make_adders() -> list[Callable[[int], int]]:
    return [lambda v, i=i: v + i for i in range(3)]


c = counter()
c()
print(narrowed_closure(4), c(), [f(10) for f in make_adders()])
try:
    reassigned_later(1)()
except TypeError as exc:
    print("runtime:", exc)
