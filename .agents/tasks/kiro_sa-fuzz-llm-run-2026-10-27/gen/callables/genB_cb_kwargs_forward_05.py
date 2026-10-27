from typing import Protocol, reveal_type


class P(Protocol):
    def __call__(self, *, a: int, b: int) -> int: ...


def k(**kwargs: int) -> int:
    return sum(kwargs.values())


def k2(**kwargs: str) -> int:
    return len(kwargs)


p: P = k  # OK
q: P = k2  # error
reveal_type(p)
print(p(a=1, b=2), q if False else 0)
