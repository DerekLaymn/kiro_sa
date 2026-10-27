from typing import reveal_type


def f(t: tuple[int] | tuple[int, int] | tuple[int, ...]) -> int:
    if len(t) == 2:
        reveal_type(t)
        a, b = t
        return a + b
    reveal_type(t)
    return len(t)


def g(t: tuple[int, str] | tuple[int, str, float]) -> int:
    if len(t) != 2:
        reveal_type(t)
        return 3
    reveal_type(t)
    return 2


def h(t: tuple[int, *tuple[str, ...]]) -> int:
    if len(t) == 1:
        reveal_type(t)
        return 1
    reveal_type(t)
    return len(t)


print(f((1,)), f((1, 2)), f((1, 2, 3)))
print(g((1, "a")), g((1, "a", 1.0)))
print(h((1,)), h((1, "a")))
