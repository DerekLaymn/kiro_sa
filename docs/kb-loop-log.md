# KB-loop log

Branch `kb-loop`, worktree `.worktrees/kb-loop`. Deterministic stage only (`TYPEDIFF_LLM=null`).

## Step 1: setup, integration, baseline

### Base

- Local `main` base commit: `d79bc7d6b63e84ccec981e05fa93a9c4605fcfa1` ("feat: add plan and updates slides to deck").
- Nothing was merged. No push, no config change, no `origin/*` merge.

### Environment

- venv: `/tmp/kbloop/venv`, CPython 3.13.15 (uv), `pip install -e .`
- Pinned tools: ty 0.0.84, mypy 2.4.0, pyright 1.1.414 (pip wrapper), pytest 9.2.0.

### Baseline (before integration, on local main)

- `python -m pytest tests -q`: **76 passed**, 0 failed.
- `typediff kb-selftest`: **8/8 PASS** (TY-REDECLARATION, TY-CALLABLE-DUNDER, TY-STRICT-EQUALITY, TY-SELF-UPPER-BOUND,
  ANNOTATION-ONLY-READ, MYPY-15182-NEW-RETURNS, JOIN-VS-UNION-CALLABLE, MDTEST-TODO).

### Copied from Derek's work (by hand, selected pieces only)

From `origin/main`:

- `scripts/public_issues.py` (whole file)
- `tests/test_known_closure_bug.py` (whole file)
- `seeds/dataclasses/overloaded_post_init.py`
- `seeds/tuples_unpacking/partial_unpack_exception.py`
- `findings/2026-10-25/lambda_rebinding.py`, `findings/2026-10-25/variadic_callback.py` (needed by the test)
- `.gitignore`: appended `.mypy_cache`, `.pytest_cache`, `typediff.egg-info`
- `typediff/kb.py`: added `_rebound_inferred_lambda` and registered it in `_REQUIRES` as `rebound_inferred_lambda`.
  Nothing else from his kb.py was taken. His version also deleted our KB entries (ANNOTATION-ONLY-READ, MYPY-15182-NEW-RETURNS,
  JOIN-VS-UNION-CALLABLE, MDTEST-TODO) and their helpers; those deletions were NOT applied.
- `typediff/data/known_upstream.json`: merged by hand. Added entry `MYPY-9658` (matcher id `UPSTREAM-MYPY-9658`) and prior stance
  `TY-4152`. Kept our TY-1090, TY-4212, TY-2255 entries and TY-4656, TY-4673, TY-1172 prior stances.

From `origin/feat/harvest-pyright-typeshed` (commit `c354744`), via `git apply --3way` of that commit's patch:

- `seeds/README.md`: applied cleanly (harvested-sources table, measured noise per source).
- `scripts/harvest_seeds.py`: one conflict. Resolved by keeping our provenance code (`tool_versions`, tag pinning,
  `PROVENANCE.json`) and adding the new `pyright` and `typeshed` sources, `harvest_pyright`, `harvest_typeshed`,
  and the `has_oracle` check that also accepts `assert_type`.

From `origin/progress/pipeline-fixes-day2`: nothing.

Not copied: run artifacts, `.agents/`, generated `gen/` programs, finding reports, Derek's other kb.py/rules.py/discrepancy.py/typenorm.py changes.

### After integration

- `python -m pytest tests -q`: **83 passed**, 0 failed (76 + the 7 tests in `tests/test_known_closure_bug.py`, all pass).
- `typediff kb-selftest`: **8/8 PASS**, unchanged.
- No integration problems needed fixing beyond the harvest_seeds.py merge conflict above.

## Step 2: corpus

`python scripts/harvest_seeds.py` -> `seeds/harvested/` (git-ignored). Hand seeds in `seeds/` kept.

| source | kept of seen | repo sha |
|---|---|---|
| conformance | 136 of 145 | dc0a8a924c99 |
| ty (ruff mdtest) | 3613 of 4902 | 73e6c488b642 |
| mypy (tag v2.4.0) | 1210 of 1770 | 935ba8afba7c |
| pyright samples | 1045 of 1446 | 74743ab17950 |
| typeshed test_cases | 56 of 74 | 2e4d4dcf657f |

Total 6060 harvested programs. All five sources were reachable.

Issues:

- `git pull --depth=1` in the script failed for 3 cached clones in `~/.cache/typediff/upstream` (conformance, ty, mypy: "divergent
  branches"; fixing it needs `pull.rebase`/`pull.ff` config, which we do not change). Those sources ran on the already-cached
  checkout, not the latest upstream HEAD. pyright and typeshed pulled fine. The exact commits are in the table above and in
  `seeds/harvested/PROVENANCE.json`. The mypy source is pinned to tag v2.4.0 regardless. ty (ruff mdtest) is not pinned to
  a tag, so it may differ from ty 0.0.84's own test suite.
- Round 1 should sample from the 6060 harvested programs plus the hand seeds in `seeds/` (about 1.5 s per program).

## Round 1 (full corpus, 2026-10-31)

Commands (venv `/tmp/kbloop/venv`, CPython 3.13.15, `TYPEDIFF_LLM=null`, ty 0.0.84, mypy 2.4.0, pyright 1.1.414):

```
python scripts/kbloop_split.py seeds docs/kb-loop-split              # fixed-seed stratified 20% hold-out
python scripts/kbloop_run.py runs/round1/out seeds --jobs 14 ...     # whole corpus, resumable, 4010 s
typediff triage runs/round1/out --top 40 --details --exclude docs/kb-loop-split/holdout.txt
python scripts/kbloop_patterns.py runs/round1/out                    # volume-ranked pattern table (tuning set)
python scripts/kbloop_replay.py runs/round1/out runs/round2/out --rerun-runtime --verify-sample 100
python scripts/kbloop_replay.py runs/round2/out runs/round2b/out --verify-sample 100   # after narrowing (see calibration)
python scripts/kbloop_stats.py runs/round2b/out
```

Corpus: all 6089 programs were run (29 hand + 6060 harvested; no sampling). 6044 ran, 45 rejected by preflight (non-stdlib import
or nondeterminism), 0 timeouts, 0 errors. Hold-out: 1218 programs (1207 ran), tuning: 4871 (4837 ran). KB entries were written only
from tuning-set samples; hold-out numbers below were never used to tune.

Speed-up: `scripts/kbloop_replay.py` re-adjudicates from the saved reports (parsed tool output, runtime result, flags, versions) instead of
re-running the checkers, with live checker runs only for experiment toggles. A random 100 programs gave identical tier/dismissal/decided_by
for replay and a full checker re-run (100/100; round2 pass). Replaying 6044 reports takes about 15-25 minutes (mostly live toggles) instead of 67.

### Queue before and after

| set | programs | live before | live after | change | dismissed before | dismissed after |
|---|---|---|---|---|---|---|
| all | 6044 | 9908 | 8934 | -9.8% | 3213 | 4189 |
| tuning | 4837 | 7939 | 7140 | -10.1% | 2537 | 3335 |
| hold-out | 1207 | 1969 | 1794 | -8.9% | 676 | 854 |

Tuning and hold-out shrink by about the same amount (10.1% vs 8.9%), so there is no sign of overfitting. Before narrowing for calibration the
first pass gave 8694 live (-12.3%); the 240 findings that came back to review are the ones the suite-header requirement removed.

Dismissals added by this round, all set: ORIGIN-ORACLE-REVEAL 798 (tuning 655, hold-out 143), UPSTREAM-MYPY-948 163 (135 / 28),
MYPY-SUITE-ALLOW-EMPTY-BODIES 11 (5 / 6). Categories after (all): DESIGN_DIVERGENCE 2760 (was 1960), DUPLICATE 179 (16),
CONFIG_ARTIFACT 58 (47), SPEC_AMBIGUITY 759, INVALID_TEST 245, KNOWN_LIMITATION 142, NOISE 46. Tool crashes: 25 (unchanged).

### Top live patterns on the tuning set before the round (volume rank)

| # | n | kind | key | n with expectation comment | n CPython raised |
|---|---|---|---|---|---|
| 1 | 1085 | reveal_mismatch | gradual | 1053 | 82 |
| 2 | 806 | reveal_mismatch | different | 787 | 14 |
| 3 | 569 | reveal_mismatch | uncomparable | 507 | 6 |
| 4 | 391 | only_mypy | assignment: incompatible types in assignment | 116 | 1 |
| 5 | 320 | only_ty | unresolved-reference: name used when not defined | 58 | 47 |
| 6 | 238 | reveal_mismatch | ty_more_precise | 232 | 0 |
| 7 | 230 | only_mypy | assert-type: expression is of type X, not Y | 1 | 2 |
| 8 | 185 | only_ty | type-assertion-failure | 0 | 0 |
| 9 | 141 | only_mypy | arg-type | 43 | 5 |
| 10 | 124 | concern_mismatch | assignment | 78 | 10 |
| 11 | 108 | only_mypy | valid-type: variable is not valid as a type | 10 | 0 |
| 12 | 105 | only_ty | invalid-assignment | 23 | 0 |
| 13 | 104 | only_mypy | no-redef | 18 | 1 |
| 14 | 101 | only_ty | invalid-argument-type | 9 | 0 |
| 15 | 89 | reveal_mismatch | mypy_more_precise | 88 | 2 |
| 16 | 72 | only_mypy | attr-defined | 40 | 10 |
| 17 | 69 | only_ty | invalid-return-type | 1 | 0 |
| 18 | 64 | concern_mismatch | valid-type: invalid type comment or annotation | 6 | 0 |
| 19 | 58 | only_mypy | misc: reveal_type expects 1 argument | 0 | 0 |
| 20 | 58 | concern_mismatch | arg-type | 39 | 6 |
| 21 | 54 | only_mypy | has-type: cannot determine type | 50 | 4 |
| 22 | 52 | only_mypy | name-defined | 15 | 4 |
| 23 | 45 | runtime_miss | (both tools silent, CPython raised) | 2 | 44 |
| 24 | 42 | only_mypy | overload-cannot-match | 1 | 0 |
| 25 | 40 | only_ty | empty-body | 1 | 0 |

### Classification of the top patterns

| pattern | class | action |
|---|---|---|
| 1, 6, 15 (reveal gradual / ty_more_precise / mypy_more_precise; 96% carry the origin suite's own expectation) | DESIGN_DIVERGENCE (narrow) | ORIGIN-ORACLE-REVEAL: dismiss only when the origin tool matches its own suite comment, the other tool is only less precise, no spec-defined narrowing, CPython does not contradict. Sources: the program's own suite expectation (harvester `# origin:` header required) and typing spec "Any is compatible with every type". |
| 2, 3 (reveal different / uncomparable) | not dismissed | ORIGIN-ORACLE-NOTE hint explains them (origin tool reproduces its own comment, other differs). |
| ~300 ty-origin reveals where ty does NOT reproduce its own mdtest comment | HARNESS_NOISE (version skew / python-version not honoured) | ORIGIN-MISMATCH hint bucket; harvester fix listed for round 2. |
| 5 (only_ty unresolved-reference, 320) | KNOWN_UPSTREAM | UPSTREAM-MYPY-948 (python/mypy#948 read, open; #3088 closed as duplicate). Also exposed pipeline defect D6. |
| 25-ish, 28, 29 (mypy `empty-body`) | HARNESS_NOISE | MYPY-SUITE-ALLOW-EMPTY-BODIES, verified by re-running mypy with `--allow-empty-bodies`. Source: mypy v2.4.0 `mypy/test/testcheck.py` line 166 and the error-code docs. |
| 7, 8, 32, 43, 45 (assert_type mismatch) | undecided | needs pyright-majority view; round 2 list. |
| 19 (pyright `expected_text=` kwarg) | HARNESS_NOISE candidate | no readable source for a clean entry; round 2 list. |
| 4, 9-14, 16-18, 20-24 | undecided | no readable upstream issue or doc yet; candidates file. |

### Pipeline-defect census (defects in OUR system, found while triaging)

| id | defect | repro | fixed |
|---|---|---|---|
| D1 | variadic tuple `tuple[A, *tuple[B, ...], C]` matched positionally -> false strong "does NOT inhabit" | `reveal_type(l)` in `ty__bidirectional__17.py` | yes, `inhabit.py`, test_kbloop_defects |
| D2 | typing aliases (`Hashable`, `Mapping`, `C[int]`) probed as instances against `type[...]` -> false strong evidence | `v1: Hashable = DC1(0)` in `pyright__dataclassHash1.py` | yes |
| D3 | operators and subscripts that call stub-bodied dunders (`A() + B()` -> None) were not recognised as scaffolding -> false strong evidence | `mypy__check_classes__testReverseOperatorOrderingCase6.py` | yes, `rules._stub_callee` |
| D4 | subclass of a TypedDict counted as a nominal class -> false "dict outside TD2" | `pyright__typedDict23.py` | yes, `state.py` |
| D5 | `TYPE_CHECKING` probed as an operand (False at runtime by definition) -> false strong evidence | `pyright__typedDict28.py` | yes |
| D6 | runtime harness `compile()` inherited its own `from __future__ import annotations`, so CPython reported "success" where 3.13 raises NameError for unquoted forward references; hid the cause of 320 unresolved-reference findings | `class A:\n    def f(self, o: A): ...` | yes (`dont_inherit=True`) and runtime re-run for the corpus |
| D7 | origin comments inside bug-report repros (`# revealed: None` in ty#4841) were read as a suite expectation (found by calibration, my own new code) | calibration case ty-4841 | yes, suite header required |
| D8 | UPSTREAM-MYPY-948 hid the real mypy bug in mypy#7935 behind a forward-reference artefact (found by calibration, my own new code) | calibration case mypy-7935 | yes, mypy-suite header required |
| D9 | mypy-origin programs are checked without the origin suite's defaults (`allow_empty_bodies`, other `[case]` flags) | `mypy__check_classes__testOperatorDoubleUnion*.py` | partly (KB toggle entry); harvester fix in round 2 list |
| D10 | pre-existing: LITERAL-WIDENING, BOTH-GRADUAL, MYPY-OPTIONAL-CHECK and rule:undefined-name dismiss the repros of real ty bug reports ty#4786, #4835, #4817, #4713, #4872 (also with the baseline code, checked) | calibration subset on baseline source | no, in candidates file |

### Verification (commands and results)

- `python -m pytest tests -q`: see "Final verification" at the end of this file.
- `typediff --python-version 3.13 kb-selftest`: all examples PASS (10 entries with examples).
- Calibration: positives were fetched (`typediff --python-version 3.13 --no-pyright calibrate --fetch --timeout 30`, 211 cases:
  the fetch returns more issues than the 166 baseline rows). First pass newly dismissed two known real bugs, both caused by this round:
  ty#4841 (ORIGIN-ORACLE-REVEAL) and mypy#7935 (UPSTREAM-MYPY-948). Both entries were narrowed to require the harvester's `# origin:` suite
  header. Re-run of 13 positives and all negatives with the final code (`scripts/kbloop_calib_subset.py`): ty#4841 kept, mypy#7935 kept, nothing else
  changed versus the first pass. The five other positives dismissed in the first pass but not in the 166-row baseline (ty#4872, #4835, #4817, #4786,
  #4713) are also dismissed by the baseline code (commit 0f1d39b, checked with `PYTHONPATH=/tmp/kbloop/basesrc`), so they are not caused by this round. ty#1172 and ty#1090
  are dismissed by their own pre-existing KB entries. Known-real bugs newly dismissed by this round: 0.

## Round 2 (crash detection + one more pattern batch)

Scope given by the user: (A) fix our own crash-detection defects from `.agents/tasks/crash25-check.md` section 6, (B) classify the next
pattern blocks, (C) report numbers. Same safety rules as round 1. Round 2 re-adjudicated from the saved round-1 reports
(`python scripts/kbloop_replay.py runs/round2b/out runs/round3/out --jobs 14 --verify-sample 100`, result: 100/100 identical to a full checker
re-run), then the 23 crash programs were re-run with the real checkers (`scripts/kbloop_run.py runs/round3/crash ...`, 242 s) and their reports
copied over.

### (A) Crash-detection defects (pipeline defects P1-P5, all fixed with regression tests in `tests/test_crash_detection.py`)

| id | defect | fix |
|---|---|---|
| P1 | negative exit codes (SIGSEGV -11, SIGABRT -6) and pyright "internal error occurred while type checking" with non-JSON stdout were stored as `abnormal_exit` / NEEDS_HUMAN, confidence 0 (15 of 25 rows) | exit code < 0 is a confirmed crash of kind `signal`; pyright internal error is detected before the JSON branch |
| P2 | a pyright timeout was counted twice (`pyright:exitNone` plus `pyright:timeout`) | the abnormal-exit branch is skipped when `exit_code is None` |
| P3 | excerpts kept only the last 25 lines or 1500-2000 characters, cutting the `RangeError: ...` header | `head_tail()` keeps the first 6 and last 19 lines |
| P4 | coarse signatures (`mypy:exit-11`, `ty:exit-6`, `pyright:exit2` merged different bugs) | `mypy:signal-SIGSEGV`, `ty:signal-SIGABRT:stack-overflow`, `pyright:internal:RangeError` |
| P5 | harvested seeds come from an untagged HEAD while the tools are pinned (5 of 11 ty crash rows were fixed one release later) | `harvest_seeds.py` records `version_skew` in `PROVENANCE.json`; every crash finding carries `RERUN-BEFORE-REPORTING` in its review notes |

Re-adjudication of the 25 crash cases (real re-run, 23 programs, 24 crash findings now because the double-counted pyright timeout is gone): 23 CONFIRMED with
signatures (timeout 8, pyright internal_error:RangeError 7, signal 7 = ty stack overflow 3 + mypy SIGSEGV 4, ty salsa panic 1), 1 NEEDS_HUMAN
(`pyright:exit255` on `ty__pep695_type_aliases__70.py`, not a plain timeout). Before: 15 of the 25 sat in review as NEEDS_HUMAN.

### (B) Pattern batch

| pattern | volume | class | outcome |
|---|---|---|---|
| mypy `"reveal_type" expects 1 argument` with pyright-only `expected_text=` / `expected_type=` | 58 tuning, 64 total | HARNESS_NOISE | entry PYRIGHT-REVEAL-EXPECTED-KWARG, INVALID_TEST. Source read: microsoft/pyright `packages/pyright-internal/src/analyzer/typeEvaluator.ts` lines ~10148 and ~10165 (the reveal_type handler reads these keyword names). Narrow: every reveal_type call on the statement carries the keyword, the only mypy diagnostic is that message, no user-defined reveal_type. 5 tests (positive and negatives) plus a kb-selftest example. No calibration positive or negative contains these keywords. |
| only_ty where the ty mdtest marks the statement `# error: [rule]` and ty reports that rule (mypy silent) | many (invalid-assignment 105, invalid-argument-type 101, invalid-return-type 69 ...) | CANDIDATE (mypy side open) | hint-only entry EXPECTED-ERROR-ORACLE: explains and sorts, never dismisses. Positive and negative tests. |
| pyright `expected_text` docs | - | - | pyright docs do not mention it (searched docs/*.md); the source code was used instead |
| only_mypy assignment / arg-type / valid-type / no-redef / has-type, concern_mismatch, assert_type mismatches | ~2500 | undecided | no readable upstream issue or doc found in this round; kept live and listed below |

Stopping rule: round 2 was the last round requested by the user. Natural-stop note: the second batch (only_ty/only_mypy samples) produced no cleanly
classifiable dismissal pattern, only a hint, so a further round would mostly need human or LLM judgement, not more deterministic entries.

### (C) Numbers

| set | live round 1 baseline | live after round 1 | live after round 2 | change round 2 | dismissed after round 2 |
|---|---|---|---|---|---|
| all | 9908 | 8934 | 8869 | -0.7% | 4253 |
| tuning | 7939 | 7140 | 7081 | -0.8% | 3393 |
| hold-out | 1969 | 1794 | 1788 | -0.3% | 860 |

Total since the start: all -10.5%, tuning -10.8%, hold-out -9.2%. Round-2 dismissals: PYRIGHT-REVEAL-EXPECTED-KWARG 64 (58 tuning, 6 hold-out), all INVALID_TEST
(245 -> 309). Crash findings 25 -> 24, with 23 now confirmed instead of 10 (the other 15 were review items).
Live by kind after round 2 (all): only_mypy 3116, only_ty 1982, reveal_mismatch 2727, concern_mismatch 903, runtime_miss 73, reveal_unpaired 44, crash 24.

Pipeline defects found in round 2: P1-P5 (all fixed). Candidate bugs (live): see `docs/kb-loop-candidates.md`, section "Crashes".

### Final verification
See the end of this file (pytest and kb-selftest results).

## Final verification (end of round 2, 2026-11-01)

- `python -m pytest tests -q`: 137 passed, 0 failed.
- `typediff --python-version 3.13 kb-selftest`: 12 PASS, 0 FAIL.
- Calibration: positives fetched (211 cases). After the round-1 narrowing, ty#4841 and mypy#7935 are kept (re-run `scripts/kbloop_calib_subset.py`); no known-real bug is newly dismissed by this work. Round-2 changes (crash parsing, PYRIGHT-REVEAL-EXPECTED-KWARG, hint-only EXPECTED-ERROR-ORACLE) cannot dismiss a calibration positive: none of the 211 sources uses `expected_text`/`expected_type`. Five positives (ty#4872, #4835, #4817, #4786, #4713) are dismissed by pre-existing entries, also with the baseline code; listed as C-2 in `docs/kb-loop-candidates.md`.
- Replay equals a full checker re-run on a random 100 programs in both passes (round1 -> round2: 100/100, round2b -> round3: 100/100).
