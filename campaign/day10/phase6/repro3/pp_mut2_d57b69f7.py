# area: context_managers
# hypothesis: A with block whose __exit__ returns True can swallow a raise and leave a later name unbound, and an instance-assigned __getitem__ is ignored by subscription, so checkers that accept either disagree with CPython.
# origin: runs/day10/parents/H_new/d9p_context_managers_swallowed_name_possibly_unbound.py
# area: context_managers
# hypothesis: A with block whose __exit__ returns True can swallow a raise and leave a later name unbound, and an instance-assigned __getitem__ is ignored by subscription, so checkers that accept either disagree with CPython.
from typing import reveal_type


class Swallow:
    def __enter__(self) -> int:
        return 7

    def __exit__(self, *args: object) -> bool:
        return True


def guarded(fail: bool) -> str:
    with Swallow() as level:
        reveal_type(level)
        if fail:
            raise TypeError('boom')
        result = f'level {level}'
    return result  # expect-error: possibly unbound when fail is True


class Control:
    def __getitem__(self, key: int) -> int:
        return key * 2


class Shadowed:
    def __init__(self) -> None:
        self.__getitem__ = lambda key: key + 1  # expect-error: cannot assign to a method


def probe() -> None:
    print(Control()[3])
    try:
        print(Shadowed()[3])  # expect-error: instance __getitem__ is not used by subscription
    except TypeError as exc:
        print('shadowed:', type(exc).__name__)


print(guarded(False))
try:
    print(guarded(True))
except (NameError, TypeError) as exc:
    print('runtime:', type(exc).__name__)
probe()
