# area: paramspec_concatenate
# explores: ParamSpec as a class type parameter; P.args/P.kwargs stored and replayed later
from collections.abc import Callable
from typing import reveal_type


class Task[**P, R]:
    def __init__(self, fn: Callable[P, R]) -> None:
        self.fn = fn

    def run(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return self.fn(*args, **kwargs)

    def bind(self, *args: P.args, **kwargs: P.kwargs) -> Callable[[], R]:
        return lambda: self.fn(*args, **kwargs)


def greet(name: str, *, punct: str = "!") -> str:
    return f"hi {name}{punct}"


t = Task(greet)
reveal_type(t)  # Task[(name: str, *, punct: str = ...), str]
reveal_type(t.run("ann", punct="?"))  # str
later = t.bind("bob")
reveal_type(later)  # () -> str
print(t.run("ann"), later())
try:
    t.run(1, 2)  # expect-error: wrong type and too many positional arguments
except TypeError as exc:
    print("runtime:", exc)
