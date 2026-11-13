# area: narrowing_builtin
# hypothesis: ty keeps the narrowing of an aliased condition (is_none = x is None) when the narrowed variable is reassigned at the end of a loop body, so the next iteration sees int although x is None; mypy and pyright report the None operand. Vary: while loop, attribute target (a.x), isinstance alias, alias recomputed inside the loop (should stay sound), reassignment before the use (should stay sound).
# origin: results/bugs.md candidate 'stale alias condition' (new ty bug, no duplicate found)
def f(x: int | None) -> int:
    is_none = x is None
    total = 0
    for _ in range(2):
        if not is_none:
            total += x + 1  # expect-error
        x = None
    return total


try:
    print(f(3))
except TypeError as exc:
    print("TypeError:", exc)
