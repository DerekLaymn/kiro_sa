from collections.abc import Callable


def invoke[*Ts, R](fn: Callable[[*Ts], R], *args: *Ts) -> R:
    return fn(*args)


def increment(value: int) -> int:
    return value + 1


print(invoke(increment, "bad"))
