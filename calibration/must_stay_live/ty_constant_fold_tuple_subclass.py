from typing import Literal, assert_type

# MUST STAY LIVE (reviewer round 1 of stage 3): no KB entry may close this program.
# ty evaluates `Restricted((1,)) < (1,)` as if tuple.__lt__ ran and infers Literal[False]; the subclass overrides
# __lt__ and CPython prints True. mypy and pyright are silent. A "literal retention" dismissal would hide this.


class Restricted(tuple[Literal[1]]):
    def __lt__(self, other: tuple[Literal[1], ...], /) -> bool:
        return True


r = Restricted((1,)) < (1,)
print(r)
assert_type(r, bool)
