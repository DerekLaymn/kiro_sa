# area: context_managers
# hypothesis: An __exit__ annotated to return Literal[True] that returns True swallows the TypeError raised inside the with block, so a name bound only inside the block is unbound afterwards and CPython raises UnboundLocalError, while the None-returning __exit__ and the @contextmanager and suppress controls show the non-swallowing behavior.
# origin: runs/day10/parents/H_new/d9p_context_managers_swallowed_name_possibly_unbound.py
# area: context_managers
# hypothesis: An __exit__ annotated to return Literal[True] that returns True swallows the TypeError raised inside the with block, so a name bound only inside the block is unbound afterwards and CPython raises UnboundLocalError, while the None-returning __exit__ and the @contextmanager and suppress controls show the non-swallowing behavior.
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager, suppress
from typing import Literal, reveal_type


class Swallow:
    def __enter__(self) -> int:
        return 7

    def __exit__(self, *args: object) -> Literal[True]:
        return True


class Strict:
    def __enter__(self) -> None:
        return None

    def __exit__(self, *args: object) -> None:
        return None


@contextmanager
def gen_ctx() -> Iterator[int]:
    yield 3


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


def gen_block(fail: bool) -> str:
    with gen_ctx():
        if fail:
            raise ValueError('gen')
        out = 'gen'
    return out


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
try:
    print(gen_block(True))
except ValueError as exc:
    print('gen runtime:', type(exc).__name__)
print(gen_block(False))
missing: dict[str, int] = {}
with suppress(KeyError):
    _ = missing['absent']
with ExitStack() as stack:
    value = stack.enter_context(Swallow())
    reveal_type(value)
