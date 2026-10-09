# area: callables
# explores: positional-only, keyword-only, *args/**kwargs types, defaults, and invalid call shapes
from typing import reveal_type


def f(a: int, /, b: int, *, c: int = 0) -> int:
    return a + b + c


def g(*args: int, **kwargs: str) -> str:
    reveal_type(args)  # tuple[int, ...]
    reveal_type(kwargs)  # dict[str, str]
    return f"{sum(args)} {','.join(kwargs.values())}"


def h(a: int, b: int = 1, *rest: str, key: bool, **extra: float) -> tuple[int, int, tuple[str, ...], bool, dict[str, float]]:
    return a, b, rest, key, extra


reveal_type(h(1, key=False))
print(f(1, 2), f(1, b=2, c=3), g(1, 2, x="a"), h(1, 2, "x", key=True, z=1.5))
bad = [
    lambda: f(a=1, b=2),  # expect-error: `a` is positional-only
    lambda: f(1, 2, 3),  # expect-error: `c` is keyword-only
    lambda: h(1),  # expect-error: missing keyword-only `key`
]
for call in bad:
    try:
        call()
    except TypeError as exc:
        print("runtime:", exc)
