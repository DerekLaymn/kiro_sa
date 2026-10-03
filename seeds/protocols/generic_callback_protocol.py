# area: protocols / callables
# hypothesis: callback protocols with keyword-only params, defaults and generics are matched
# against functions exactly (names, kinds, defaults).
# spec: typing spec, protocol.html "Callback protocols" + callables.html.
from typing import Protocol


class Handler[T](Protocol):
    def __call__(self, item: T, *, retries: int = ...) -> bool: ...


def good(item: int, *, retries: int = 3) -> bool:
    return item > retries


def no_default(item: int, *, retries: int) -> bool:
    return True


def renamed(value: int, *, retries: int = 3) -> bool:
    return True


def run(h: Handler[int]) -> bool:
    return h(5)


print(run(good))
try:
    run(no_default)  # expect-error: protocol has a default for `retries`
except TypeError as exc:
    print('runtime:', type(exc).__name__)
try:
    run(renamed)  # expect-error: `item` may be passed by keyword
except TypeError as exc:
    print('runtime:', type(exc).__name__)
