# area: context_managers
# hypothesis: An __exit__ annotated as bool or Literal[True] swallows the exception, so a name bound after the raising statement stays unbound, while an __exit__ annotated None and a @contextmanager generator let the exception propagate.
# origin: runs/day10/parents/H_new/d9p_context_managers_swallowed_name_possibly_unbound.py
# area: context_managers
# hypothesis: An __exit__ annotated bool or Literal[True] swallows the exception, so a name bound after the raising statement stays unbound, while __exit__ annotated None or a @contextmanager generator lets the exception propagate.
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from typing import Literal, reveal_type


class SwallowBool:
    def __enter__(self) -> None:
        return None

    def __exit__(self, *args: object) -> bool:
        return True


class SwallowLit:
    def __enter__(self) -> None:
        return None

    def __exit__(self, *args: object) -> Literal[True]:
        return True


class KeepNone:
    def __enter__(self) -> None:
        return None

    def __exit__(self, *args: object) -> None:
        return None


@contextmanager
def guard() -> Iterator[None]:
    yield


def probe_bool(fail: bool) -> str:
    with SwallowBool():
        if fail:
            raise ValueError('bool')
        result = 'ok'
    return result  # expect-error: result is possibly unbound when fail is True


def probe_lit(fail: bool) -> int | None:
    x: int | None = None
    with SwallowLit():
        if fail:
            raise ValueError('lit')
        x = 1
    reveal_type(x)
    return x


def probe_none(fail: bool) -> int | None:
    x: int | None = None
    with KeepNone():
        if fail:
            raise ValueError('none')
        x = 1
    reveal_type(x)
    return x


def probe_ctl(fail: bool) -> int | None:
    x: int | None = None
    with guard():
        if fail:
            raise ValueError('ctl')
        x = 1
    return x


def probe_suppress(fail: bool) -> int | None:
    x: int | None = None
    with suppress(ValueError):
        if fail:
            raise ValueError('suppress')
        x = 1
    return x


print(probe_bool(False), probe_lit(False), probe_none(False))
try:
    print(probe_bool(True))
except NameError as exc:
    print('bool:', type(exc).__name__)
print(probe_lit(True), probe_suppress(True), probe_ctl(False))
try:
    print(probe_none(True))
except ValueError as exc:
    print('none:', type(exc).__name__)
try:
    print(probe_ctl(True))
except ValueError as exc:
    print('ctl:', type(exc).__name__)
