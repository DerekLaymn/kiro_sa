from typing import Literal, assert_type

# KNOWN DUPLICATE of astral-sh/ty#2171 (open; design in ty#2140). Closed by exactly UPSTREAM-TY-2171-ASSERT.
# The shape is closed by a narrow entry; near-miss controls for it must stay live (see tests/test_upstream_round7.py).
# ty evaluates `Restricted((1,)) < (1,)` as if tuple.__lt__ ran and infers Literal[False]; the subclass overrides
# __lt__ and CPython prints True. mypy and pyright are silent.


class Restricted(tuple[Literal[1]]):
    def __lt__(self, other: tuple[Literal[1], ...], /) -> bool:
        return True


r = Restricted((1,)) < (1,)
print(r)
assert_type(r, bool)
