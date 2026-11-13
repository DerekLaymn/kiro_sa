from collections.abc import Callable


def build(value: int | None) -> Callable[[], int]:
    if value is None:
        value = 0
    callback = lambda: value + 1
    value = None
    return callback


print(build(1)())
