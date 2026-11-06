# Day 10 run log

Branch `campaign/day10-p2`, created from `campaign/day9-p2` at `5a16806` (Day 9 report; verification committed in `02d533f`). Local only, nothing pushed, no GitHub writes.

Pins unchanged: mypy 2.4.0, ty 0.0.97, pyright 1.1.414, CPython 3.13.16, target Python 3.13.

## Setup: weaknesses Day 10 could fix (from `day9-report.md` section 7)

1. ty `deprecated` on `@contextmanager` with `-> Iterator[..]`: 25 of 224 live findings (11 %), no rule or KB entry.
2. `runtime_supports` for `only_pyright` cannot tell a documented trade-off from a defect (20 of 22 rows).
3. Queued matchers: `TY-NONFINAL-PATTERN`, `ASSERT-NEVER-ALL-REJECT`, wider `JOIN-VS-UNION`, `MYPY-8595`, reveal after invalid type form, mypy `Attribute function "__call__"` for annotation-only dunders.
4. Operator-follow for new operators checked only by regex.
5. Duplicates not closed by the KB reappear live.

## Chosen for Day 10 phase 1

Weakness 1: add a matcher/rule for the ty `deprecated` diagnostic on `@contextmanager` generators so these findings are classified instead of counted live. This follows the Day 9 report section 7 first bullet (pipeline fix, as Day 9 phase 1 did for the Day-8 matcher weaknesses). A unit test in `tests/` is required for it.
