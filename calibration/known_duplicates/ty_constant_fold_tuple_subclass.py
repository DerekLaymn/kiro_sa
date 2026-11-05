from typing import Literal, assert_type

# KNOWN DUPLICATE of astral-sh/ty#2171 (open; design in ty#2140). Closed by exactly UPSTREAM-TY-2171-ASSERT.
# Until Day 6 this file was a "must stay live" program (reviewer round 1 of stage 3); on Day 7 the decision was to close
# the shape with a narrow entry and move it here.
# ty evaluates `Restricted((1,)) < (1,)` as if tuple.__lt__ ran and infers Literal[False]; the subclass overrides
# __lt__ and CPython prints True. mypy and pyright are silent.


class Restricted(tuple[Literal[1]]):
    def __lt__(self, other: tuple[Literal[1], ...], /) -> bool:
        return True


r = Restricted((1,)) < (1,)
print(r)
assert_type(r, bool)
