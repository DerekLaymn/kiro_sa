# known_duplicates

Real discrepancies that an open upstream issue already tracks. Each program must be closed by exactly one KB entry
(`decided_by`), so a program here is a regression test for a narrow dismissal, not a bug to file:

| program | closed by | upstream |
|---|---|---|
| `ty_constant_fold_tuple_subclass.py` | `UPSTREAM-TY-2171-ASSERT` | astral-sh/ty#2171 (open), design in ty#2140 |
| `mypy_stale_alias.py` | `UPSTREAM-TY-2792` | astral-sh/ty#2792 (open) |

The assertions are in `tests/test_stage3_round2.py` and `tests/test_stage3_round3.py`. Near-miss controls (the same
shape without the trigger) must stay live; they live next to the assertions and in `tests/test_upstream_day7.py`.
