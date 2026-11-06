from typing import Callable, ParamSpec, TypeVar, reveal_type

T = TypeVar("T")
P = ParamSpec("P")


class Job:
    def run(self: Callable[[int], int], x: int) -> int:
        return self(x)


class Other:
    def run(self: int) -> None: ...
