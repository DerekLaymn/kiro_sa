from typing import TypeGuard, reveal_type


def all_str(xs: list[object]) -> TypeGuard[list[str]]:
    return all(isinstance(x, str) for x in xs)


def f(xs: list[object]) -> int:
    if not all_str(xs):
        reveal_type(xs)
        return -1
    reveal_type(xs)
    return len("".join(xs))


def g(xs: list[object] | None) -> int:
    if xs is not None and all_str(xs):
        reveal_type(xs)
        return len(xs)
    reveal_type(xs)
    return 0


def h(x: int | str) -> None:
    ok = all_str([x])
    if ok:
        reveal_type(x)


print(f(["a", "b"]), f([1]), g(["x"]), g(None))
h(1)
