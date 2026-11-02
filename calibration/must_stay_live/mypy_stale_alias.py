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
