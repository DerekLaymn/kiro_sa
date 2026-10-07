# area: final_classvar
# explores: Final at module/class/instance level, Final inside a loop, `global` reassignment, ClassVar[T]
from typing import ClassVar, Final, reveal_type

MAX: Final = 3
RATE: Final[float] = 0.5


class Config[T]:
    instances: ClassVar[int] = 0
    default: ClassVar[T]  # expect-error: ClassVar cannot contain type variables

    def __init__(self, value: T) -> None:
        self.value: Final = value
        Config.instances += 1


for i in range(2):
    LIMIT: Final = i  # expect-error: Final inside a loop is reassigned


def bump() -> None:
    global MAX
    MAX = 4  # expect-error: cannot assign to a Final name


reveal_type(MAX)  # int (Literal[3])
reveal_type(Config(1).value)  # int
reveal_type(Config.instances)  # int
c = Config("x")
c.value = "y"  # expect-error: Final attribute (allowed at runtime)
bump()
print(MAX, RATE, c.value, Config.instances, LIMIT)
