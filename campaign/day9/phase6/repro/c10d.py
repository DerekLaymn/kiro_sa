from contextlib import ExitStack
from typing import Literal


class Maybe:
    def __enter__(self) -> None:
        return None

    def __exit__(self, *args: object) -> bool | None:
        return True


class Always:
    def __enter__(self) -> None:
        return None

    def __exit__(self, *args: object) -> Literal[True]:
        return True


def f_optional_bool() -> int:
    with Maybe():
        a = int("x")
    return a


def f_literal_true() -> int:
    with Always():
        b = int("x")
    return b


def f_exit_stack() -> int:
    with ExitStack() as stack:
        stack.callback(print, "cleanup")
        c = int("x")
    return c


for fn in (f_optional_bool, f_literal_true, f_exit_stack):
    try:
        fn()
    except UnboundLocalError:
        print(fn.__name__, "UnboundLocalError")
    except ValueError:
        print(fn.__name__, "ValueError propagated")
