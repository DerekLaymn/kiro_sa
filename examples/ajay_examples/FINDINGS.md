# First run of ajay_examples (ty 0.0.84, mypy 2.4.0, pyright 1.1.414, CPython 3.13)

I triaged this run with `typediff triage --details` and checked each item by hand against all three checkers
and CPython.

## Worth reporting (after a duplicate check)

| example | tool | what happens | evidence |
|---|---|---|---|
| `11_flag_strenum.py` L26 | **ty** | `Perm.R \| Perm.W` is inferred as `Literal[Perm.R, Perm.W]`, but the runtime value is the *combined* member `Perm.R\|W`, which is neither. Code narrowing on `is Perm.R` / `is Perm.W` then treats the else-branch as unreachable, and `assert_never` crashes at runtime while ty reports nothing. pyright infers `Perm` | Runtime value outside the revealed type (strong); assert_never witness crashes. Probably covered by the unchecked "Handling of `enum.Flag`" item in ty#876. Comment there, or file it linking #876 |
| `01_typevartuple_shapes.py` L29 | **ty** | `call_with(area, "2", 1.5)` with `def call_with[*Ts, R](f: Callable[[*Ts], R], *args: *Ts)`: ty is silent; mypy and pyright reject it; CPython raises `TypeError` | Runtime crash; two other checkers agree. Closest issue is ty#4262 (different: lost tuple length). Looks new |
| `30_closures_nonlocal.py` L22 | **mypy** | `x` is narrowed to `int`, a lambda captures it, then `x = None`. mypy is silent (it keeps the narrowing inside the lambda); ty and pyright report it; CPython raises `TypeError` | Runtime crash. Probably a known mypy issue (narrowing in closures); search python/mypy |

## Not bugs (my example comment was wrong, or this is a documented difference)

- `33` plain `bool` passed to `Literal[True]`/`Literal[False]` overloads: the spec expands `bool` to
  `Literal[True] | Literal[False]`, so ty and pyright are right and **mypy** is the outlier. The comment is fixed.
- `16` `callable(v)` on `int | Callable[[], int]`: ty keeps `int & <callable>` (an int subclass could define
  `__call__`), so `v()` returns `object`. This is deliberate soundness in ty; mypy and pyright narrow to `() -> int`.
- `04` LiteralString: mypy treats `LiteralString` as `str` (documented mypy limitation).
- `13` custom `__class_getitem__`: mypy does not support it (documented).
- `22` `Final` inside a loop: only mypy checks this. `ClassVar[T]`: only ty reports it. These are missing checks
  rather than wrong verdicts, so they are low priority.
- `37` `prices["x"] = "cheap"`: ty infers the dict literal's value type from later writes (`dict[str, str | float]`).
  This is inference design, not a soundness hole.

## typediff fixes made from this run

- The type normaliser dropped enum qualifiers inside `Literal` (`Literal[Mode.FAST]` became `Literal[FAST]`).
  That produced a false "runtime value outside the type" alarm on `11` L20.
- The normaliser did not understand mypy's NamedTuple display `tuple[int, int, fallback=Pair[int]]`. That produced
  three false runtime alarms on `12`.
- `typediff triage --details` now prints both tools' messages, the evidence and the report path for each example.
