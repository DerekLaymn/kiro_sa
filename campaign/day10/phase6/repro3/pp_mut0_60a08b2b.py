# area: context_managers
# hypothesis: A with-block whose __exit__ is annotated bool or Literal[True] swallows the raised TypeError, leaving the name bound after the raise unbound, while a None-annotated __exit__ propagates the error.
# origin: runs/day10/parents/H_new/d9p_context_managers_swallowed_name_possibly_unbound.py
# area: context_managers
# hypothesis: A with-block whose __exit__ is annotated bool or Literal[True] swallows the TypeError so a name bound after the raise is unbound afterwards, while a None-annotated __exit__ and contextlib.suppress show which controls do not swallow.
from collections.abc import Callable
from contextlib import suppress
from typing import Literal, reveal_type


class SwallowBool:
    def __enter__(self) -> int:
        return 1

    def __exit__(self, *args: object) -> bool:
        return True


class SwallowLiteral:
    def __enter__(self) -> int:
        return 1

    def __exit__(self, *args: object) -> Literal[True]:
        return True


class Propagate:
    def __enter__(self) -> int:
        return 1

    def __exit__(self, *args: object) -> None:
        return None


def bool_block(fail: bool) -> str:
    with SwallowBool():
        if fail:
            raise TypeError('bool')
        x = 1
    reveal_type(x)
    return f'bool {x}'  # expect-error: possibly unbound when fail is True


def literal_block(fail: bool) -> str:
    with SwallowLiteral():
        if fail:
            raise TypeError('literal')
        y = 2
    reveal_type(y)
    return f'literal {y}'  # expect-error: possibly unbound when fail is True


def none_block(fail: bool) -> str:
    with Propagate():
        if fail:
            raise TypeError('none')
        z = 3
    reveal_type(z)
    return f'none {z}'


def suppress_block(fail: bool) -> str:
    with suppress(TypeError):
        if fail:
            raise TypeError('suppress')
        w = 4
    reveal_type(w)
    return f'suppress {w}'  # expect-error: possibly unbound when fail is True


def attempt(fn: Callable[[bool], str], fail: bool) -> str:
    try:
        return fn(fail)
    except (NameError, TypeError) as exc:
        return type(exc).__name__


for fn in (bool_block, literal_block, none_block, suppress_block):
    print(attempt(fn, False), attempt(fn, True))
