import sys
from collections.abc import Callable
from typing import ClassVar, reveal_type


def plain(n: int) -> int:
    return n


class H:
    inst: Callable[[int], int]
    cls_attr: ClassVar[Callable[[int], int]] = plain

    def __init__(self) -> None:
        self.inst = plain


h = H()
reveal_type(h.inst)
reveal_type(h.cls_attr)
print(h.inst(1))
if len("") > 99:
    # at runtime a plain function stored as a class attr binds self -> TypeError
    print(h.cls_attr(1))
