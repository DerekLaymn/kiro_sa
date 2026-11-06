# area: context_managers
# hypothesis: An instance-level __enter__ is ignored by the with statement because CPython looks special methods up on the type, so it raises TypeError while a class-level __enter__ works and a swallowing __exit__ leaves the bound name unbound.
# origin: runs/day10/parents/H_new/d9p_context_managers_swallowed_name_possibly_unbound.py
# area: context_managers
# hypothesis: An instance-level __enter__ is ignored by the with statement because CPython looks special methods up on the type, so it raises TypeError while a class-level __enter__ works and a swallowing __exit__ leaves the bound name unbound.
from collections.abc import Callable
from typing import Literal, reveal_type


class Shadowed:
    def __init__(self, fn: Callable[[], int]) -> None:
        self.__enter__ = fn

    def __exit__(self, *args: object) -> Literal[True]:
        return True


class Control:
    def __enter__(self) -> int:
        return 7

    def __exit__(self, *args: object) -> Literal[True]:
        return True


def shadowed_with() -> int:
    try:
        with Shadowed(lambda: 1) as value:  # expect-error
            return value
    except TypeError as exc:
        print('shadowed:', type(exc).__name__)
    return -1


def control() -> int:
    with Control() as value:
        reveal_type(value)
        result = value
    return result


def guarded(fail: bool) -> str:
    with Control() as level:
        if fail:
            raise TypeError('boom')
        result = f'level {level}'
    return result  # expect-error


print(shadowed_with())
print(control())
print(guarded(False))
try:
    print(guarded(True))
except NameError as exc:
    print('unbound:', type(exc).__name__)
