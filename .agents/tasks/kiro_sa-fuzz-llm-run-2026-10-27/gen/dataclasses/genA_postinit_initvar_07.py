from typing import reveal_type  # noqa

from dataclasses import InitVar, dataclass, field


@dataclass
class Conf:
    raw: InitVar[str]
    size: int = field(init=False)

    def __post_init__(self, raw: str) -> None:
        self.size = len(raw)


@dataclass
class Sub(Conf):
    extra: InitVar[int] = 0

    def __post_init__(self, raw: str, extra: int) -> None:
        super().__post_init__(raw)
        self.size += extra


def go() -> int:
    c = Sub("abc", 2)
    reveal_type(c.size)
    reveal_type(Sub.extra)
    return c.size


print(go())
