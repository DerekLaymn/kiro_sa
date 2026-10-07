# area: inheritance_mro (exceptions)
# explores: except* narrowing to ExceptionGroup[...], ExceptionGroup.subgroup
from typing import reveal_type


def risky(n: int) -> None:
    errors: list[Exception] = []
    if n % 2:
        errors.append(ValueError(f"odd {n}"))
    if n % 3 == 0:
        errors.append(KeyError(n))
    if errors:
        raise ExceptionGroup("batch", errors)


def run(n: int) -> list[str]:
    seen: list[str] = []
    try:
        risky(n)
    except* ValueError as eg:
        reveal_type(eg)  # ExceptionGroup[ValueError]
        seen += [str(e) for e in eg.exceptions]
    except* KeyError as eg:
        reveal_type(eg.exceptions)  # tuple[KeyError | ExceptionGroup[KeyError], ...]
        seen.append(f"keys {len(eg.exceptions)}")
    return seen


def plain() -> str:
    try:
        raise ExceptionGroup("g", [TypeError("t")])
    except ExceptionGroup as eg:
        reveal_type(eg)  # ExceptionGroup[Unknown/Any]
        sub = eg.subgroup(TypeError)
        reveal_type(sub)  # ExceptionGroup[TypeError] | None
        return str(sub)


print(run(3), run(4), run(6), plain())
