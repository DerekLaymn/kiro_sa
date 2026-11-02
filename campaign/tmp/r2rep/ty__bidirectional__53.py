# area: gradual_any
# origin: ruff mdtest bidirectional.md block 53
from typing import Callable, TypedDict

class TD(TypedDict):
    x: int

def first[T](x: list[T]) -> T:
    return x[0]

type ObjectCallback = Callable[[object], None]
type IntCallback = Callable[[int], None]

def make_callback[T](callback: Callable[[T], None]) -> Callable[[T], None]:
    return callback

def consume(value: int) -> None:
    pass

x1: TD = first([{"x": 0}, {"x": 1}])
reveal_type(x1)  # revealed: TD

x2: TD | None = first([{"x": 0}, {"x": 1}])
reveal_type(x2)  # revealed: TD

# error: [missing-typed-dict-key] "Missing required key 'x' in TypedDict `TD` constructor"
# error: [invalid-key] "Unknown key "y" for TypedDict `TD`"
# error: [invalid-assignment] "Object of type `TD | dict[str, int]` is not assignable to `TD`"
x3: TD = first([{"y": 0}, {"x": 1}])

# error: [missing-typed-dict-key] "Missing required key 'x' in TypedDict `TD` constructor"
# error: [invalid-key] "Unknown key "y" for TypedDict `TD`"
# error: [invalid-assignment] "Object of type `TD | None | dict[str, int]` is not assignable to `TD | None`"
x4: TD | None = first([{"y": 0}, {"x": 1}])

# `ObjectCallback` is redundant in this union, so expanding the aliases collapses the narrowing
# target to `IntCallback`.
x5: ObjectCallback | IntCallback = make_callback(lambda value: consume(value.bit_length()))
