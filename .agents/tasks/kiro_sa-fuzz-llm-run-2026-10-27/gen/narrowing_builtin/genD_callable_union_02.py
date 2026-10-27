from typing import Callable, reveal_type


class Fn:
    def __call__(self, x: int) -> int:
        return x + 1


def run(v: int | Callable[[int], int] | Fn | type[str]) -> object:
    if callable(v):
        reveal_type(v)
        return v(3)
    reveal_type(v)
    return v


def run2(v: str | Callable[[], str]) -> str:
    if not callable(v):
        reveal_type(v)
        return v
    reveal_type(v)
    return v()


print(run(1), run(lambda n: n * 2), run(Fn()), run(str))
print(run2("a"), run2(lambda: "b"))
