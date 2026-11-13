# area: context_managers
# hypothesis: An __exit__ annotated to return Literal[True] swallows the ValueError, so run(True) returns the value set before the raise, while checkers may narrow x after the block as if the block always completed.
# origin: llm
# area: context_managers
# hypothesis: An __exit__ annotated to return Literal[True] swallows the ValueError, so run(True) returns the value set before the raise, while checkers may narrow x after the block as if the block always completed.
from contextlib import ExitStack, contextmanager, suppress
from types import TracebackType
from typing import Iterator, Literal, reveal_type


class Swallow:
    def __enter__(self) -> None:
        return None

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> Literal[True]:
        return True


def run(fail: bool) -> int | None:
    x: int | None = None
    with Swallow():
        x = 1
        if fail:
            raise ValueError('boom')
        x = 2
    reveal_type(x)
    return x


@contextmanager
def tracked(log: list[str]) -> Iterator[int]:
    log.append('enter')
    try:
        yield 7
    finally:
        log.append('exit')


def use_suppress(n: int) -> int | None:
    result: int | None = None
    with suppress(ZeroDivisionError):
        result = 10 // n
    reveal_type(result)
    return result


def stacked() -> list[str]:
    log: list[str] = []
    with ExitStack() as stack:
        cm = stack.enter_context(tracked(log))
        reveal_type(cm)
        log.append(str(cm))
    return log


assert run(True) == 1 and run(False) == 2
assert use_suppress(0) is None and use_suppress(5) == 2
assert stacked() == ['enter', '7', 'exit']
trail: list[str] = []
with tracked(trail) as v:
    reveal_type(v)
assert trail == ['enter', 'exit'] and v == 7
