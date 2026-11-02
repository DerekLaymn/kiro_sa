# area: narrowing_builtin
# origin: ruff mdtest narrow/type_guards.md block 45
from typing import Generic, TypeVar
from typing_extensions import TypeIs

T = TypeVar("T")

class Container(Generic[T]): ...

def is_container(value: object, other: T) -> TypeIs[Container[T]]:
    return True

while True:
    # error: [possibly-unresolved-reference]
    # error: [possibly-unresolved-reference]
    if is_container(value, type(value)):
        value = value.__str__  # error: [possibly-unresolved-reference]
        bad: str = 42  # error: [invalid-assignment]
    else:
        value = {value}  # error: [possibly-unresolved-reference]
        bad: str = 42  # error: [invalid-assignment]
    reveal_type(value)  # revealed: Divergent | set[Divergent]
