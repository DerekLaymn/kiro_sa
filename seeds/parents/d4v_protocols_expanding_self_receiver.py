# area: protocols
# hypothesis: ty overflows its stack (0.0.84 and 0.0.97) when a plain class is assigned to a protocol whose method annotates self as Stream[Stream[T]], because every receiver check needs a larger receiver type. mypy and pyright accept it. Vary: Stream[list[T]], Stream[tuple[T]], Stream[dict[str, T]], a generic Impl, old-style TypeVar, argument or return position instead of assignment; Stream[T | None] and a method-level TypeVar do not crash but ty rejects them (ty#4746).
# origin: verification of seed-d8c0c3a3b3ad (protocol_flatten), reduced by hand; nearest tracker entries ty#4746, ty#4882, ty#4863
from typing import Protocol


class Stream[T](Protocol):
    def flatten(self: "Stream[Stream[T]]") -> None: ...


class Impl:
    def flatten(self) -> None: ...


x: Stream[int] = Impl()
