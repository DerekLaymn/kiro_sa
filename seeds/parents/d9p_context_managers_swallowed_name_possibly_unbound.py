# area: context_managers
# hypothesis: A with block whose __exit__ returns bool may swallow an exception raised inside the block, so a name bound after the raising statement is unbound after the block (CPython raises UnboundLocalError); pyright reports the use, ty only under an off-by-default rule, mypy not even with possibly-undefined. Vary: the __exit__ annotation (None, Literal[True], Literal[False]), contextlib.suppress, ExitStack, async with, try/finally, del of the name.
# origin: generated program context_managers/gen0_b82d2e9e (not kept), draft 10 in results/bugs.md: mypy does not report a possibly-undefined name after a swallowing with block
from contextlib import ExitStack, suppress
from typing import reveal_type


class Swallow:
    def __enter__(self) -> int:
        return 7

    def __exit__(self, *args: object) -> bool:
        return True


class Strict:
    def __enter__(self) -> None:
        return None

    def __exit__(self, *args: object) -> None:
        return None


def guarded(fail: bool) -> str:
    with Swallow() as level:
        reveal_type(level)
        if fail:
            raise TypeError('boom')
        result = f'level {level}'
    return result  # expect-error: possibly unbound when fail is True


def strict(fail: bool) -> str:
    with Strict():
        if fail:
            raise TypeError('strict')
        result = 'fine'
    return result


print(guarded(False))
try:
    print(guarded(True))
except (NameError, TypeError) as exc:
    print('runtime:', type(exc).__name__)
try:
    print(strict(True))
except TypeError as exc:
    print('strict runtime:', type(exc).__name__)
print(strict(False))
missing: dict[str, int] = {}
with suppress(KeyError):
    _ = missing['absent']
with ExitStack() as stack:
    value = stack.enter_context(Swallow())
    reveal_type(value)
