from typing import reveal_type  # noqa

from enum import Enum, member, nonmember
from typing import Final


class K(Enum):
    A = 1
    B = nonmember(2)
    _ignore_ = ["tmp"]
    C = member(3)

    def helper(self) -> int:
        return 0

    LIMIT: Final = 10


def go() -> None:
    reveal_type(K.A)
    reveal_type(K.B)
    reveal_type(K.C)
    reveal_type(K.LIMIT)
    reveal_type(K.helper)
    reveal_type(K.C.value)
    print(list(K))


go()
