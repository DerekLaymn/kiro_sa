# area: constructors_metaclasses
# hypothesis: type(name, (Container[int],), {}) fails at runtime (MRO entry resolution needs types.new_class) while ty reveals the class precisely and mypy reveals Any. Vary: types.new_class instead of type(), a non-generic alias base, two conflicting specialisations.
# origin: runs/day2/out3 seed-badf7d3532a5 (ruff mdtest call/type.md block 28; runtime_miss + only_ty)
from typing import Generic, TypeVar

T = TypeVar("T")

class Container(Generic[T]):
    value: T

# Dynamic class inheriting from a generic class specialization
IntContainer = type("IntContainer", (Container[int],), {})
reveal_type(IntContainer)  # revealed: <class 'IntContainer'>

container = IntContainer()
reveal_type(container)  # revealed: IntContainer
reveal_type(container.value)  # revealed: int

class IntContainerBase(Container[int]): ...
class StrContainerBase(Container[str]): ...

# error: [invalid-generic-class]
ConflictingContainer = type("ConflictingContainer", (IntContainerBase, StrContainerBase), {})

# error: [invalid-generic-class]
conflicting_container = type("InlineConflictingContainer", (IntContainerBase, StrContainerBase), {})()
