from typing import reveal_type  # noqa

from dataclasses import dataclass, field


@dataclass
class Bag:
    items: list[int] = field(default_factory=list)
    tags: dict[str, int] = field(default_factory=dict)
    name: str = field(default="n", init=False)


def use() -> int:
    b = Bag([1, 2])
    reveal_type(b.items)
    reveal_type(b.tags)
    reveal_type(b.name)
    return len(b.items)


print(use())
