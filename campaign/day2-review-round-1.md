# Stage 3 round 1: bytes-literal normalisation, two new dismissal entries, multi-name ANNOTATION-ONLY-READ

Round 1 fixes a bytes-literal spelling defect in `typenorm`, adds the KB entries `ASSERT-TYPE-LITERAL-RETENTION` and `MYPY-FIRST-ASSIGNMENT-TYPE`, and lets `ANNOTATION-ONLY-READ` match several names on one statement. The review queue went from 7841 to 7470 findings (-4.73%). Tuning went from 6300 to 5960 (-5.40%) and hold-out from 1541 to 1510 (-2.01%). The Plan target (more than 50% on both sets) is far from met, and the plan forbids inventing dismissals to close that gap.

Watch for: (1) `ASSERT-TYPE-LITERAL-RETENTION` auto-dismisses ty's constant-folded `Literal[True]`/`Literal[False]` results against an asserted `bool` (62 findings). I reproduced a case where ty's fold contradicts CPython, so the entry hides a real ty inference bug (confirmed). (2) The entry's docstring says the other tool is silent, but the matcher never checks pyright. 75 of the 130 dismissals have a pyright diagnostic on the statement (likely). (3) The queue shrank 3.4 points less on hold-out than on tuning (confirmed).

**Verdict**: NEEDS_CHANGES

## High-level view

The bytes fix and the `MYPY-FIRST-ASSIGNMENT-TYPE` entry look sound. All 18 sampled dismissals of the first-assignment entry are undeclared-variable re-bindings. The `--allow-redefinition` verify gate is a real, non-circular check, and I confirmed it clears the error on three sampled programs. Pyright agreeing with ty (silence) is required as well. This entry accounts for 182 of the round's dismissals.

`ASSERT-TYPE-LITERAL-RETENTION` is the problem. The idea (the spec leaves literal retention of inferred types open, and the conformance suite says "either is acceptable") is correct for values like `slice(1234, None)` or `pack(1, "text")`. The matcher is wider than the idea. It also accepts any `Literal[True]`/`Literal[False]` versus `bool`, which is ty evaluating a comparison, not retaining a literal. If ty evaluates it wrongly, the entry hides the bug. Such comparisons account for about half of the entry's dismissals.

The multi-name `ANNOTATION-ONLY-READ` extension is correct on the 18 sampled rows. It extends an entry that has `runtime_override=False`, so 4 more findings are dismissed even though CPython raised `NameError` on that exact statement. That is the pre-existing policy for this entry, but the round widens it.

The target is not met and no invented dismissals are needed: the three reveal-mismatch patterns (gradual 623, different 553, uncomparable 450) are 1626 of the 5960 tuning findings and have no non-circular rule yet. Next round should start with the closing of the fold hole, then with the coder's own ranked next-round ideas (error-recovery reveals, `LiteralString`/`type`, `def () -> X` display).

<details>
<summary>Issues (7)</summary>

1. **Plan target not met (blocking)**: overall 7841 -> 7470 (-4.73%), tuning 6300 -> 5960 (-5.40%), hold-out 1541 -> 1510 (-2.01%). Continue to the next round; do not invent dismissals.
2. **Constant-fold hole in ASSERT-TYPE-LITERAL-RETENTION (blocking, confirmed)**: 62 dismissals are `Literal[True/False]` vs `bool`. Reproducer: `class R(tuple[Literal[1]])` with `__lt__` returning `True`; `r = R((1,)) < (1,)`; ty infers `Literal[False]`, CPython prints `True`, mypy and pyright are silent, and the pipeline reports `live=[]`. Restrict the entry so the asserted expression contains no comparison/operator expression whose result ty evaluated (or exclude `bool` vs `Literal[True/False]`), add a test with this program, and add it to `calibration/negatives` as a must-stay-live case.
3. **Entry text contradicts the matcher (confirmed)**: the docstring says "the other tool is silent", but `m_assert_type_literal_retention` only inspects the failing tool's diagnostics. 55 dismissals carry a pyright `reportAssertTypeFailure` and 20 carry `reportAssertTypeFailure` plus `reportOperatorIssue` (pyright rejects `tuple[Literal[1]] < tuple[Literal[2]]`, which CPython accepts). Either require pyright to be silent or agree with the same literal relation, or fix the text; the swallowed `reportOperatorIssue` should stay visible.
4. **ANNOTATION-ONLY-READ dismisses runtime-crash evidence (likely, non-blocking)**: the entry has `runtime_override=False`; 100 of its dismissals (4 new this round) are programs where CPython raised `NameError` on the dismissed statement. ty and pyright are right and the gap is mypy's, so no ty bug is hidden, but the finding is recorded as DESIGN_DIVERGENCE. Record it as a mypy known limitation (link UPSTREAM-MYPY-948 / `python/mypy#948`) so the crash evidence is not lost, and decide the NameError policy the coder already flagged.
5. **Tuning/hold-out gap (confirmed)**: 5.40% vs 2.01%. `MYPY-FIRST-ASSIGNMENT-TYPE` hits 2.1% of tuning programs and 0.8% of hold-out programs; ASSERT-TYPE dismissals sit in a few pyright-origin programs (33 of the 62 fold dismissals are in one file, `pyright__tupleComparisonResults4`). Report the gap again next round and prefer rules that fire across several origin families.
6. **Calibration cannot see issue 2 (likely)**: the before/after calibration is clean (same 11 pre-existing dismissed positives, none newly dismissed), but the set has no tuple-comparison or constant-fold case, so a clean result is weak evidence for this entry. Add the issue-2 program as a negative.
7. **Remaining largest patterns (tuning, after this round)**: reveal_mismatch gradual 623, different 553, uncomparable 450, only_mypy [assignment] 199 (declared-name rows), only_mypy [assert-type] 197, reveal_mismatch ty_more_precise 187, only_ty [unresolved-reference] 129 (50 with CPython NameError), only_mypy arg-type 118, concern_mismatch [assignment] 114, only_ty invalid-assignment 94.

</details>

<details>
<summary>Details</summary>

## Dismissal audit

I wrote `/tmp/r1_audit.py` (the repo's `kbloop_sample.py` skips dismissed findings, so it cannot sample them) and drew 18 random findings per rule from `runs/day2/out1`, mixing tuning and hold-out.

`MYPY-FIRST-ASSIGNMENT-TYPE` (182 dismissed, 10 hold-out): all 18 are undeclared re-bindings (`y = 1; y = "s"` in branches, `try/except` re-binding, chained assignment, `__slots__` rebinding in a class body). None has runtime-crash evidence on its statement. Three sampled programs were re-run with and without `--allow-redefinition` and the assignment error disappears in each, so the verify gate does what the entry says. No sampled finding hides a bug.

`ANNOTATION-ONLY-READ` (334 dismissed, 83 hold-out; 39 new this round): all 18 are a `x: T` declaration read before any assignment, with ty and pyright both naming the name and, where the program runs, CPython raising `NameError`. The two-name rows (`u(D_C, A_C)`, `u(t_a, M2(*a))`) are covered correctly by the new multi-name path. No ty bug is hidden. The concern is the policy in issue 4.

`ASSERT-TYPE-LITERAL-RETENTION` (130 dismissed, 4 hold-out): the sampled `slice(1234, None)`, `pack(1, "text")`, `tupleLiteralInference*` and `generics_scoping` rows are legitimate literal-retention differences, and the conformance file says either answer is acceptable. The sampled `tupleComparisonResults*` rows are a different thing: ty computes the result of `left < right` on literal tuples and reports `Literal[True]`/`Literal[False]`. In the sampled programs ty's value matches what the code does at runtime. That is not guaranteed, though. I reproduced a mismatch (`/tmp/r1_cmp2.py`):

```python
class Restricted(tuple[Literal[1]]):
    def __lt__(self, other: tuple[Literal[1], ...], /) -> bool:
        return True
r = Restricted((1,)) < (1,)
assert_type(r, bool)      # ty: inferred Literal[False]; CPython: True; mypy, pyright: silent
```

Run through `typediff seeds`, this program ends with `live=[]`, so the entry dismisses it automatically. The pipeline's purpose is to surface exactly this. The fix belongs in the matcher (do not treat a `bool` vs `Literal[True/False]` difference as retention when the asserted expression is an evaluated comparison or operator), not in the entry's wording.

## Pyright diagnostics swallowed by the assert_type dismissal

The matcher checks every diagnostic of the failing tool but none of pyright's. Of 130 dismissals, 55 have no pyright diagnostic, 55 have only `reportAssertTypeFailure`, and 20 also have `reportOperatorIssue` on tuple comparisons. The 55 with a pyright assert failure are consistent with the literal-retention story only if pyright's own received type is a widening of the same literal, which the matcher never verifies. The 20 operator errors look like a pyright false positive on literal-tuple comparison; dismissing them as ty literal retention removes that from review.

## Round bookkeeping

Commits d171b92, fbf9b12, 0cd8539, d479c03. Every code change has a test: `tests/test_stage3_round1.py` has 13 tests covering bytes normalisation, `is_literal_retention`, both new entries (positive and negative cases, runtime-exception demotion, verify gate) and the multi-name read. The recorded results are 157 passed (`campaign/s3-r1-pytest.txt`) and 13/13 PASS in `kb-selftest` (`campaign/s3-r1-kb-selftest-final.txt`). I did not re-run them. Calibration before/after (`campaign/s3-r1-calib-compare.txt`) shows identical positives (117 kept / 61 invisible / 11 dismissed / 5 excluded) and no newly dismissed positive. The 11 dismissed positives were already dismissed by earlier code. The replay verified 100/100 sampled reports identical to a full re-run. The 14 findings that disappeared are bytes literal pairs that are now equal, an effect of the typenorm fix, not a dismissal.

Log labels match the work. The `[Plan §6 Triage checklist ...]` entries describe the triage steps (reps, per-tool verdicts, variants, duplicate search, decision), `[Plan §3 P1 re-measure ...]` entries describe replay, stats, audit, tests and calibration, and `[Plan §7 pivot]` records the refusal to invent dismissals. The log corrects its own pattern-4 numbers in a labelled `[CORRECTION]` entry.

Repository hygiene: no `runs/`, `seeds/harvested`, `findings/2026-10-27-llm-run/`, `-l` or `calibration/positives.json` in the commits (checked with `git diff --name-only b4bf9e8 HEAD`). `campaign/tmp/*` scripts and `campaign/s3-r1-*` outputs are committed, which is intended campaign material. `campaign/day2-p1` has no remote-tracking branch, so nothing was pushed. My spot-check created one report in the git-ignored `typediff_out/`, which I removed.

</details>

<details>
<summary>File map</summary>

Diff: `git diff b4bf9e8 HEAD`.

- `typediff/typenorm.py`: bytes-literal tokenisation and canonical `b"..."` spelling; `deep_widen`, `is_literal_retention`.
- `typediff/kb.py`: new entries `ASSERT-TYPE-LITERAL-RETENTION`, `MYPY-FIRST-ASSIGNMENT-TYPE`; helpers `_declared_names`, `_name_declared_in_scope`; multi-name `ANNOTATION-ONLY-READ`.
- `tests/test_stage3_round1.py`: 13 tests for the above.
- `calibration/negatives/assert_type_literal_retention.py`, `calibration/negatives/mypy_first_assignment.py`: negatives that must be closed.
- `campaign/day2-run-log.md`, `campaign/s3-r1-*`, `campaign/tmp/*`: log, outputs and helper scripts.

</details>
