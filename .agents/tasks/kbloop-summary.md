# kb-loop summary (branch kb-loop, worktree .worktrees/kb-loop, nothing pushed)

Final verification (venv rebuilt in /tmp/kbloop/venv, TYPEDIFF_LLM=null): `python -m pytest tests -q` = 139 passed; `typediff --python-version 3.13 kb-selftest` = all PASS.

## Numbers: baseline vs final

Corpus: 6044 programs ran (29 hand seeds + harvested; 45 more rejected by preflight). Full corpus, not sampled.

| | baseline (round 1 start) | final (round 4 replay) |
|---|---|---|
| programs | 6044 | 6044 |
| discrepancies | 13096 | 13098 |
| live review queue (all) | 9908 | 9650 (-2.6%) |
| live, tuning set (4837 programs) | 7939 | 7719 |
| live, hold-out (1207 programs) | 1969 | 1931 |
| dismissed | 3213 | 3472 |
| tool crash findings | 25 (15 sat as NEEDS_HUMAN) | 24 (23 CONFIRMED with signatures, 1 NEEDS_HUMAN) |

Auto-dismissed by category (baseline -> final): SPEC_AMBIGUITY 759 -> 759, DESIGN_DIVERGENCE 1960 -> 1962, INVALID_TEST 245 -> 309, KNOWN_LIMITATION 142 -> 305, CONFIG_ARTIFACT 47 -> 58, NOISE 44 -> 63, DUPLICATE 16 -> 16.

Intermediate peak: after round 2 the queue was 8869 (-10.5%). A reviewer finding made ORIGIN-ORACLE-REVEAL hint-only (see below), which returned about 800 items to the queue. The real, kept reduction is 2.6%. Live by kind (final): only_mypy 3116, reveal_mismatch 3525, only_ty 1965, concern_mismatch 903, runtime_miss 73, reveal_unpaired 44, crash 24.

## Pipeline defects fixed (our own system, with regression tests)

D1 variadic tuple inhabitation, D2 typing aliases probed as instances, D3 stub-bodied dunder callee ignored, D4 TypedDict subclass counted as nominal, D5 TYPE_CHECKING probed as operand, D6 runtime harness inherited `from __future__ import annotations`. Crash detection P1-P5 (signal exits, pyright internal error, double-counted timeout, head+tail excerpts, finer signatures, version-skew flag).

## New KB / upstream entries and sources

| entry | effect | source |
|---|---|---|
| UPSTREAM-MYPY-948 (known_upstream.json + matcher) | auto-dismiss, KNOWN_LIMITATION (163 findings); requires the harvester header in the first 6 lines | https://github.com/python/mypy/issues/948 (open feature request), #3088 closed as duplicate; https://mypy.readthedocs.io/en/stable/runtime_troubles.html |
| MYPY-SUITE-ALLOW-EMPTY-BODIES | auto-dismiss (11), verified by toggle `--allow-empty-bodies` | mypy v2.4.0 `mypy/test/testcheck.py` line 166; https://mypy.readthedocs.io/en/stable/error_code_list.html |
| PYRIGHT-REVEAL-EXPECTED-KWARG | auto-dismiss INVALID_TEST (64) | microsoft/pyright `typeEvaluator.ts` ~lines 10148/10165 (source read; pyright docs do not mention it) |
| ORIGIN-ORACLE-REVEAL | hint-only (does not dismiss) after review | the suite's own `# revealed:` comment plus typing-spec Any semantics |
| ORIGIN-ORACLE-NOTE, ORIGIN-MISMATCH, EXPECTED-ERROR-ORACLE, SUITE-EXPECTS-ERROR | hints only, sort and explain, never close | ty mdtest / mypy test expectations |

## Candidate bugs (none verified as a tool bug; see docs/kb-loop-candidates.md)

Crashes, reproduce 3/3 on pinned tools (mypy 2.4.0, ty 0.0.84, pyright 1.1.414). Re-run on newest releases before reporting (flag RERUN-BEFORE-REPORTING). Evidence strength: strong (runtime crash), version-skew risk.

| id | tool | minimal repro | status |
|---|---|---|---|
| MA | mypy SIGSEGV | `type Meta[T] = type[T]` then `type X = Meta[X]` | new; master gives RecursionError |
| MB | mypy hang | `type Id[T] = T` then `type X = Id[X]` | new |
| ME | mypy SIGSEGV | `T = TypeVar("T", default="T")`; `class C(Generic[T]): ...` | new, related to python/mypy#16940 |
| MC | mypy hang | `type RecursiveParamspec[**P] = Callable[[], RecursiveParamspec[Concatenate[int, P]]]` | duplicate of python/mypy#21123 |
| TB | ty stack overflow (0.0.84-0.0.95) | two generic protocols P1, P2 (8 lines, `.agents/tasks/crash25-check.md` section 5.9) | new; ty main untested |
| TA | ty exponential time | nested tuple comparison depth 20 | new (perf), low priority |
| TS | ty slow match | tuple-of-unions match | duplicate of astral-sh/ty#4676 |
| TX | ty hang/overflow/panic on 5 programs | `ty__narrow__type_guards__45/46`, etc. | fixed in ty 0.0.85 |
| PR | pyright RangeError | `class C:\n    __init__: type["C"]\nC()` | pyright, out of scope |

Other leads (weaker):
- C-3 runtime_miss: 73 programs where CPython raises a type error and both tools are silent, e.g. `seeds/harvested/gradual_any/ty__del__4.py` (`del c.x` on a missing attribute). Strong runtime evidence, but not yet checked that the exception is the test's intended `# error`.
- C-1 ty reveals `Unknown` where mypy's suite blessed a concrete type, e.g. `mypy__check_classes__testAttributeDefOrder2.py`. Imprecision only, suite expectation is the only evidence.

## Remaining top patterns needing an LLM judge or a human

1. only_mypy (3116): assignment, arg-type, valid-type, no-redef, attr-defined. No readable upstream source found.
2. reveal_mismatch (3525): `different` and `uncomparable` reveal pairs, including about 300 ty-origin ORIGIN-MISMATCH cases (version skew, mdtest python-version not honoured).
3. only_ty (1965): mostly suite negative tests where ty is right and mypy has a false negative. These are candidate mypy false negatives, not dismissable.
4. concern_mismatch (903) and assert_type mismatches (~490): need a pyright majority view as weak evidence.
5. C-2: the dismissals of the known-real reports ty#4872, #4835, #4817, #4713, #4786. They dismiss the visible noise line, while the bug is a missing diagnostic elsewhere that a ty-vs-mypy diff cannot see. Not narrowed.

## Honest limits

- The whole corpus ran once and was re-adjudicated by replay of saved reports. Replay equalled a full checker re-run on random 100-program samples in the earlier passes (100/100). The sample line for the final replay (round 3 -> 4) was not retained after /tmp was wiped, so the final replay is unverified by that check.
- KB entries were written from tuning-set samples only. The hold-out fell 1969 -> 1931 (-1.9%), tuning 7939 -> 7719 (-2.8%), so there is no sign of overfitting, but the gains are small.
- Calibration was a full 211-row run on code before the last category-only edit to UPSTREAM-MYPY-948; not repeated after it.
- The pattern batches for only_mypy and only_ty were sampled, not read exhaustively. They produced hints, not dismissals.
- The crash repros come from an untagged upstream HEAD checked against pinned tools. Five ty rows were already fixed one release later, so each report needs a re-run on current releases.
- No bug is confirmed. Derek's four reported bugs were not part of this loop.
- The venv in /tmp/kbloop was wiped during the work and rebuilt; `runs/` is git-ignored and may vanish.
- Untracked `.agents/tasks/kbloop-review.md` inside the worktree was left alone.
