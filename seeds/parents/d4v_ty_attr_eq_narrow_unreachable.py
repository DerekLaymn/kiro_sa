# area: narrowing_user
# hypothesis: ty narrows c.n to Literal[8] after assert c.n == 8 and keeps it across a method call that rebinds self.n, so the next assert c.n == 99 makes the rest of the function Never and the read-only property assignment is never checked (ty#2792). Vary: non-data descriptor shadowed through __dict__, a module-level helper that mutates the attribute, direct assignment between the asserts (stays sound).
# origin: campaign/day4/verify-v2.md candidate 'read-only property Never' (duplicate of ty#2792, instructive)
from typing import reveal_type


class C:
    def __init__(self, n: int) -> None:
        self.n = n

    @property
    def readonly(self) -> int:
        return self.n

    def bump(self) -> None:
        self.n = 99


def f(c: C) -> None:
    assert c.n == 8
    c.bump()
    assert c.n == 99
    reveal_type(c)
    try:
        c.readonly = 5  # expect-error
    except AttributeError:
        print("no setter")


f(C(8))
