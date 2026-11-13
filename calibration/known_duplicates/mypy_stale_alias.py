# KNOWN DUPLICATE of astral-sh/ty#2792 (open, attribute narrowing kept after a method call). Closed by exactly
# UPSTREAM-TY-2792. The program also guards MYPY-13807-ALIASED-CONDITIONS, which must NOT explain this reveal: the
# entry's stale-alias guard rejects it.
class A:
    x: int | None

    def clear(self) -> None:
        self.x = None


def f(a: A) -> None:
    # The alias is computed, then `a.x` may change (a.clear()) before the `if`. MYPY-13807-ALIASED-CONDITIONS must not
    # explain this reveal difference away: the aliased expression is no longer what the alias tested.
    is_none = a.x is None
    a.clear()
    if not is_none:
        reveal_type(a.x)
