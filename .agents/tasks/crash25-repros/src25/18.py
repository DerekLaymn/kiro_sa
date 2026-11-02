# area: narrowing_builtin
# origin: ruff mdtest narrow/type_guards.md block 46
from typing_extensions import TypeIs

class Container[T]: ...

def is_container[T](value: object, other: T) -> TypeIs[Container[T]]:
    return True

while True:
    # error: [possibly-unresolved-reference]
    # error: [possibly-unresolved-reference]
    if is_container(value, type(value)):
        value = value.__str__  # error: [possibly-unresolved-reference]
    else:
        value = {value}  # error: [possibly-unresolved-reference]
    reveal_type(value)  # revealed: Divergent | set[Divergent]
