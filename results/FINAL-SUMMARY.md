# typediff fuzzing campaign, final summary (Days 1 to 10)

> Paths written as `[campaign working file]`, `[run output]` or `[agent working file]` point to scratch files of the original campaign that are not part of this repository.

The campaign did not file, comment on or open a PR for any issue by itself; the filing steps below were done by the authors. Every number comes from the per-day reports in [`days/`](days/), the issue drafts in [`bugs.md`](bugs.md), the git history of this repository, or read-only `gh` calls made on 2026-11-06 (issue states). Rates were computed while writing this file. Anything that could not be read is listed in section 11.

Pins since Day 6 (Day 5 for ty): mypy 2.4.0, ty 0.0.97, pyright 1.1.414, CPython 3.13.16, target Python 3.13. Days 1 to 4 ran ty 0.0.84 (bumped in `ff8bd5e`).

## 1. What the campaign did

Days 1 and 2 improved the deterministic judge on a harvested corpus (5129 programs) with no LLM and no bug hunting. From Day 3 on, each day mutated or freshly generated about 250 small Python programs with a model (a `claude-haiku-5.5` stand-in at effort `medium`, through a file bridge), ran mypy, ty and pyright plus CPython on each, let the knowledge base (KB) and rules close the discrepancies that are known duplicates, design differences or noise, and read the remaining ones by hand. A read candidate became a draft only after a reduction, a run on the pinned and the newest versions of each tool, a duplicate search on the trackers, and a verdict. Programs that showed a new pattern became parents for the next day's mutation (the 36 parents left after Day 10 are in [`seeds/parents/`](../seeds/parents/)); parents that only reproduced known findings were retired.

Result: 12 drafts with verdict STILL-BUG-NEW (section 5). Drafts 1 to 9 are filed by the user's drafting account, draft 2 is already fixed upstream, drafts 10 to 12 are not filed. Confidence runs from 0.35 to 0.9; only draft 2 is at 0.9.

## 2. Pipeline improvements, with commits

All commits are in the `git log` of this repository.

| Day | Change | Commit |
|---|---|---|
| 1 to 2 | Parallel corpus runner and fixed-seed 20 % hold-out split | `74a782a` |
| 1 to 2 | Friend work integrated (mypy#9658 matcher, public issues, pyright/typeshed harvest), kb-loop baseline | `0f1d39b` |
| 1 to 2 | Origin oracle, MYPY-948 and suite-empty-bodies entries, replay tooling (`--rerun-runtime`) | `0d517b7`, `c324ac6` |
| 1 to 2 | Crash detection (signals, pyright internal errors, no double count, head+tail excerpts, finer signatures) | `178a862` |
| 2 | `assert_type` literal retention and first-assignment entries; REVEAL-ERROR-RECOVERY; MYPY-13807-ALIASED-CONDITIONS; NameError policy (user decision); stale-alias guard | `fbf9b12`, `c1d243b`, `9456642`, `ba8fbe0`, `a4147b3`, `10dd9b1`, `d924841` |
| 2 | Reviewer loop, 3 rounds, never approved; queue 7841 to 7277 (7.19 %, target of 50 % not met) | `4055e85` (report) |
| 3 | Known-upstream entries: 11 crash entries, 9 discrepancy entries, 2 prior stances | `ce63f5c`, `ca5f30b`, `ee5e6ac` |
| 3 | `generate --n` yields distinct variants (was 1 distinct prompt for `--n 3`) | `dc51a60` |
| 3 | Kill the whole process group when a checker times out (orphaned pyright node processes) | `032bf3d` |
| 4 | ty#4656 recorded as a closed design difference, not a bug; flaky-test fix | `074ceb4`, `1c3cd05` |
| 4 | Entries TY-4148 (crash) and TY-876-ARGTYPE | `78a6546` |
| 5 | Crashes auto-close only through a known-upstream entry and record the closing reference | `3aab933` |
| 5 | C1 `__call__` self-reference shapes for TY-4148 and MYPY-22361; "Variant k of n" line in prompts; `inbox_status` reports orphan answers | `3b1cf93`, `afe5df3`, `8ad46bb` |
| 5 | Morning entries (enum aliases, Flag else reveal, `~Flag`, property setter, local C1 crash) | `6c9825a` |
| 5 | ty pin 0.0.84 to 0.0.97; TY-4883 and TY-4884 marked fixed in 0.0.97 | `ff8bd5e`, `3074ef5`, `622f5b7` |
| 6 | TY-4756 entry and TY-2171 prior stance | `74b3018` |
| 7 | Narrow entries for ty#2171 and ty#2792 (19 Day-6 rows closed, 0 false closures in the controls) | `cd88cd8` |
| 7 | Opt-in `only_pyright` finding kind for pyright errors that mypy and ty miss; `kbloop_stats` prints live count without it | `977007d`, `48e6e08` |
| 8 | ParamSpec self-callable family, duplicate matchers (descriptor store, pyright#11382, `Hashable`), display-noise canonicaliser, caught-exception evidence; review fixes | `b4c6482`, `47d5df6`, `ffff035` |
| 9 | Quoted `'Self'`, `TY-2792-READONLY` in a nested `def`; operators `dunder_instance_shadow` and `exit_swallow_flip`; areas `dunder_dispatch` and `context_managers` | `42a7af8` |
| 10 | `TY-CONTEXTMANAGER-ITERATOR-DEPRECATED` (closed 25 Day-9 rows and 12 Day-10 rows) | `63cd5b2` |
| 10 | `MYPY-8595-METACLASS-CALL` (closed 4 Day-10 rows and 1 Day-9 row) | `334ff8c` |

Tests and self-test: 144 passed at the start of Day 2 (`day2-run-report.md`), 360 on Day 3, 373 on Day 4, 422 on Day 5, 426 on Day 6, 498 on Day 7, 604 on Day 8, 655 on Day 9, **730 on Day 10**. `kb-selftest`: 11 PASS at the start of Day 2, 20 on Day 3, 21 on Days 4 and 5 (20 after the ty bump removed one firing entry), 20 on Days 6 to 10.

## 3. KB growth

`known_upstream.json` counts and the number of `KBEntry(` occurrences in `typediff/kb.py`, read with `git show` at the last commit of each day as chosen here. The day-to-commit mapping is mine, from `git log` order; Days 1 and 2 share one JSON state.

| Day | Commit | `known_upstream.json` entries | of which `kind=crash` | prior stances | `KBEntry(` in `kb.py` |
|---|---|---|---|---|---|
| 1 | `7f2969d` | 5 | 0 | 4 | 39 |
| 2 | `096a153` | 5 | 0 | 4 | 44 |
| 3 | `7d4488d` | 25 | 11 | 6 | 44 |
| 4 | `a403712` | 27 | 12 | 6 | 44 |
| 5 | `622f5b7` | 30 | 12 | 6 | 44 |
| 6 | `1f54286` | 31 | 12 | 7 | 44 |
| 7 | `03d88a5` | 35 | 12 | 7 | 44 |
| 8 | `1df508f` | 39 | 12 | 7 | 47 |
| 9 | `5a16806` | 39 | 12 | 7 | 47 |
| 10 | `c6c5a9a` | 39 | 12 | 7 | 49 |

Day 3 added 20 entries and 2 prior stances after the user's team-filed upstream crashes and discrepancy bugs were recorded. Day 10 added two matcher entries in `kb.py` only. The `known_upstream.json` entries are matched by message, source shape and (for crashes) signal; prior stances never dismiss.

How much the KB changed live counts, measured by replaying old reports on a later KB (replay output, not a new judge run):

| Reports | Replay | Live before to after |
|---|---|---|
| Day 2 `out3` | Day-3 KB | 7277 to 7273 |
| Day 5 | Day-5 morning KB | 136 to 110 (26 findings changed, all hand-checked) |
| Day 6 | Day-6 KB, then Part A | 218 to 212 to 194 (19 changed in Part A, 11 same-family rows stay live on purpose) |
| Day 7 | Day-10 KB (`--rerun-runtime`) | 107 to 75 (`phase7/results/stats_replayed_day7.out`; includes the Day-8 harness change) |
| Day 8 | Day-10 KB | 155 to 152 |
| Day 9 | Day-10 KB | 224 to 198 (25 by the `deprecated` entry, 1 by `MYPY-8595`) |

## 4. Live-rate trend per day

Judge-run figures as recorded in each `dayN-stats.txt` (the KB at the time of the run; Days 3 to 5 with ty 0.0.84, Day 5 judged before its morning entries). "Findings" = discrepancies + tool crash events. Rates computed here. Days 1 and 2 are a different regime (a harvested corpus, no generation) and are not in the table: Day 1 ran 29 hand seeds (35 discrepancies, 25 live, 14 programs with live), Day 2 ran 5086 programs with 7277 live findings at the end.

| Day | Programs | Discrepancies | Tool crash events | Findings | Auto-closed | Live | Live per program | Programs with live | Live w/o `only_pyright` per program | Drafts added |
|---|---|---|---|---|---|---|---|---|---|---|
| 3 | 160 | 50 | 18 | 68 | 20 | 48 | 0.30 | 41 (25.6 %) | n/a | 0 (candidates, verified on Day 4) |
| 4 | 246 | 175 | 40 | 215 | 73 | 142 | 0.58 | 83 (33.7 %) | n/a | 4 (drafts 1 to 4, from Day 3 candidates) |
| 5 | 250 | 154 | 42 | 196 | 60 | 136 | 0.54 | 105 (42.0 %) | n/a | 0 |
| 6 | 250 | 259 | 62 | 321 | 103 | 218 | 0.87 | 127 (50.8 %) | n/a | 1 (draft 5) |
| 7 | 224 | 151 | 31 | 182 | 75 | 107 | 0.48 | 68 (30.4 %) | 88 / 224 = 0.39 | 2 (6, 7) |
| 8 | 250 | 208 | 16 | 224 | 69 | 155 | 0.62 | 104 (41.6 %) | 135 / 250 = 0.54 | 1 (8) |
| 9 | 250 | 335 | 4 | 339 | 115 | 224 | 0.90 | 129 (51.6 %) | 180 / 250 = 0.72 | 2 (9, 10) |
| 10 | 250 | 247 | 0 | 247 | 75 | 172 | 0.69 | 101 (40.4 %) | 142 / 250 = 0.57 | 2 (11, 12) |

Day 3 findings 68 = 50 + 18; Day 4 215 = 175 + 40; Day 5 196 = 154 + 42; Day 6 321 = 259 + 62; Day 7 182 = 151 + 31; Day 8 224 = 208 + 16; Day 9 339 = 335 + 4; Day 10 247 = 247 + 0 (computed here; each equals live + auto-closed in the stats file).

The same reports re-judged on the final Day-10 KB (so the KB is held fixed): Day 7 75 / 224 = 0.33 (0.28 without `only_pyright`), Day 8 152 / 250 = 0.61 (0.53), Day 9 198 / 250 = 0.79 (0.62), Day 10 168 / 250 = 0.67 (0.55). Days 3, 4 and 6 were not replayed on the final KB; Day 5 and Day 6 replays on their own morning KBs are in section 3.

Reading the trend: the live rate per program did not fall steadily, because the generation mix changed every day (crash-family programs: 40 on Day 7, 22 on Day 9, 10 on Day 10; new areas and operators added; the opt-in `only_pyright` kind added on Day 7). Tool crash events fell from 62 on Day 6 to 0 on Day 10 because the crash families were closed by entries and then mutated less. The auto-closed share was 29.4 % to 34.0 % on the judge runs of Days 3 to 6 and 8 to 10 (Day 7: 41.2 %), so most of the live queue each day is new material to read, not noise the KB could have closed. New drafts per day do not follow the live rate: 0.87 live per program on Day 6 gave 1 draft, 0.48 on Day 7 gave 2.

## 5. Verified bugs (drafts 1 to 12)

"Verified" here means: reduced, run on CPython 3.13.16 and on the pinned and newest versions of each tool, and searched on the trackers, with verdict STILL-BUG-NEW in `results/bugs.md`. It does not mean a maintainer confirmed it. **Only drafts 1 and 2 were verified by the user on a playground;** drafts 3 to 12 have a `<PLAYGROUND LINK>` placeholder (drafts 3 to 9 were filed anyway by the user's account; whether the user ran them on a playground first is not recorded). Confidence is the draft's own number. Filing state is from the author listing and `gh issue view` of 2026-11-06 (read-only).

| # | Tool | One-line description | Verdict | Conf. | User playground | Filed / state |
|---|---|---|---|---|---|---|
| 1 | ty | stack overflow when a class is checked against a protocol whose method annotates `self` as `Stream[Stream[T]]` | STILL-BUG-NEW (CRASH), none found | 0.80 | yes | ty#4933, open (labels `bug`, `fatal`; maintainer comment says a fix PR has blockers) |
| 2 | ty | alias narrowing (`is_none = x is None`) survives a reassignment that reaches the use over a loop back edge | STILL-BUG-NEW, none found | 0.9 | yes | ty#4934, **closed completed** 2026-11-05; fixed by astral-sh/ruff#30074 "[ty] Invalidate aliased conditions across loop iterations" (merged 2026-11-05 22:09 UTC) |
| 3 | mypy | reflected operator of a subclass metaclass ignored for class-object operands (`A * B`); cause confirmed by instrumenting mypy master | STILL-BUG-NEW | 0.7 | no | mypy#22377, open; a contributor offered to fix it (2026-11-06) |
| 4 | ty | class with `__eq__` and no `__hash__` accepted as `Hashable` | STILL-BUG-NEW | 0.7 | no | ty#4941, open (labels `bug`, `runtime semantics`, `unsoundness`) |
| 5 | mypy | `Foo[int, str]` on a class with a `TypeVarTuple` followed by a defaulted `ParamSpec` is rejected and inferred as `Any`; runtime half is python/typing#2211 | STILL-BUG-NEW (mypy only) | 0.7 | no | mypy#22375, open (`bug`) |
| 6 | ty | `except` clause sees the old value after a nested unpacking target failed half-way through an assignment | STILL-BUG-NEW (ty 0.0.97 and 0.0.98) | 0.5 | no | ty#4958, open, no labels |
| 7 | pyright | `RangeError: Maximum call stack size exceeded` when a descriptor `__get__` is decorated by a class-body function without `self` | STILL-BUG-NEW (CRASH, pyright 1.1.414 = latest) | 0.8 | no | pyright#11984, open (`bug`) |
| 8 | mypy | overloaded `__post_init__` of a dataclass: every overload item is checked against the InitVar signature, so an item without the InitVar type gets `[override]` | STILL-BUG-NEW (2.4.0, 2.4.1, master) | 0.6 | no | mypy#22385, open (`bug`) |
| 9 | mypy | `a < b` for two operands of the same type tries `b.__gt__` first when `__lt__` and `__gt__` come from different classes of the MRO; the inferred type is that of the wrong method | STILL-BUG-NEW | 0.6 | no | mypy#22386, open (`bug`) |
| 10 | mypy | `possibly-undefined` does not report a name assigned in a `with` block whose `__exit__` returns `bool`, although the name is unbound after a swallowed exception (pyright reports it; ty only with an off-by-default rule) | STILL-BUG-NEW (opt-in check, FALSE_NEGATIVE) | 0.4 | no | **not filed** |
| 11 | mypy | a `lambda` with other parameter names (or positional-only parameters) is accepted for a callback protocol whose `__call__` names its parameter, while the equivalent `def` is rejected | STILL-BUG-NEW (2.4.0, 2.4.1, master; ty and pyright reject) | 0.5 | no | **not filed** |
| 12 | pyright | `closed=True` and `extra_items=` on a `typing.TypedDict` class are accepted for `pythonVersion` below 3.15, where CPython raises `TypeError` | STILL-BUG-NEW (1.1.414 = latest); same report exists for mypy (#21747) and was fixed in ty (#4031) | 0.35 | no | **not filed** |

Notes on the table:

* Days of origin: drafts 1 to 4 from Day 3 candidates (verified on Day 4, re-checked on Day 6), 5 from Day 6, 6 and 7 from Day 7, 8 from Day 8, 9 and 10 from Day 9, 11 and 12 from Day 10.
* By tool: ty 4 (drafts 1, 2, 4, 6), mypy 6 (3, 5, 8, 9, 10, 11), pyright 2 (7, 12); 12 in total.
* By class (the drafts' own labels, grouped here): 2 crashes (1, 7); 5 false negatives (2, 4, 10, 11, 12); 5 false positives or wrong inference (3, 5, 6, 8, 9).
* Draft 2 is the highest-confidence draft (0.9, playground-verified). It was fixed upstream the day it was filed (ruff#30074 merged), which is the only confirmed maintainer outcome that is a fix. Of the open drafts, only ty#4933 (a maintainer reply about a fix PR with blockers) and mypy#22377 (a contributor offered a fix) have comments; ty#4941, mypy#22375, ty#4958, pyright#11984, mypy#22385 and mypy#22386 have none.
* The Day-10 draft 11 text originally said "21 `only_ty` rows"; the saved reports give 10 in the three named mutants. Corrected in phase 7 (`day10-report.md` section 5).

## 6. Previously filed issues by the user's accounts (context only)

States read with `gh issue view` on 2026-11-06. The listed authors are as GitHub shows them (`DerekLaymn` for the drafting account; `Choco-princess` and `Pika-pikachu30` for the others); these are context for the KB entries, not part of the 12 drafts.

| Issue | Title (shortened) | State |
|---|---|---|
| ty#4656 | False negative: Self parameter is not enforced on inherited methods | closed not planned 2026-10-05: intended behaviour per carljm (`Self` is a typevar bound to the defining class); recorded as a design difference, KB `TY-SELF-UPPER-BOUND` |
| ty#4882 | Stack overflow on two generic protocols with a self-referential method | open |
| ty#4883 | Exponential time comparing deeply nested tuple types | closed completed 2026-11-03 (KB marks it fixed in ty 0.0.97) |
| ty#4884 | TypeVar solver fails to infer type argument from generic TypedDict | closed completed 2026-11-02 (fixed in ty 0.0.97) |
| ty#4898 | Stack overflow when passing a ParamSpec identity function to itself | open |
| ty#4899 | Abort (memory blowup) or panic with a `Callable[P, T]`-annotated self in `__init__` and a ParamSpec `__call__` | open (maintainer reproduced the plain-method panic) |
| ty#4900 | Stack overflow on generic base class that expands its own type argument | open |
| mypy#22339 | PEP 695 variance inference treats a writable `Callable[[T], None]` attribute as contravariant | open (a contributor posted a cause in `infer_variance()`) |
| mypy#22343 | Segfault on type alias that refers to itself through another generic alias | open (cause posted by a contributor) |
| mypy#22344 | Segfault on class parameterised by a TypeVar whose default is itself | open (cause posted by a contributor) |
| mypy#22360 | contravariant generic with a self-referential base | open |
| mypy#22361 | Segfault / RecursionError when calling an instance whose class declares `__call__` as an attribute | open |
| pyright#11851 | TypedDict subtyping: ReadOnly required incorrectly accepts NotRequired source key | open |
| pyright#11960 | Pyright hangs when specializing a self-recursive PEP 695 type alias | closed completed 2026-11-03 (a contributor points to #11968 as covering it) |
| pyright#11961 | Crash (`RangeError`) when a constructor method is annotated ... | open |

The crash entries TY-4882, TY-4898, TY-4899, TY-4900, MYPY-22343, MYPY-22344, MYPY-22360, MYPY-22361 and PYRIGHT-11961 correspond to issues in this list (TY-4148 is ty#4148, not in the list), and the KB's `UPSTREAM-*` discrepancy entries record the others. Crash events that match an entry are auto-closed with the closing reference; that is why Days 7 to 10 show few live crash findings. The campaign never re-filed any of them.

## 7. Duplicates found

Candidates that looked like bugs and were closed as duplicates, fixed, or design. States are as recorded in the verification files on the day (not re-queried now, except where section 5 or 6 says otherwise).

* **Crashes:** self-referential `__call__` attribute: ty#4148 and mypy#22361 (Day 4). `partial | None` in a loop: ty 0.0.84 panic, fixed in ty 0.0.85. pyright `RangeError` on a constructor path: pyright#11961 / PR #11965 (different frames from draft 7).
* **ty:** stale alias condition after a method call and read-only property `Never`: ty#2792. Tuple-subclass constant fold: ty#2171 (design in ty#2140). Flag combination `Never`: ty#876. Metaclass `A | B`: ty#4683. `Self` parameter on a subclass: ty#4656 (closed, intended). Annotation-only dunders: ty#4570, ty#491 (open). `object + object` after `case (a, b)` with a non-final class: ty#1578 (design, closed not planned). `Never` after `assert str_value == 4`: ty#3419 (closed completed), ty#4051 and ty#3162 (open). ParamSpec self-annotation family: ty#3666. `closed=True` before 3.15: ty#4031 (closed, fixed).
* **mypy:** IntEnum alias: mypy#16830, #21117 (and pyright#11100). Recursive alias reveal: mypy#2008. `__hash__` None reveal: mypy#20230. `__eq__` without `__hash__` accepted as `Hashable`: mypy#2455 and #18622, fix pending in open PR #19168. Metaclass `__call__` return type ignored: mypy#8595 (closed, "unlikely this will be ever supported"), request #14122. Flag narrowing by `==` / `is` / `match`: mypy#21937 (open, fix PR #21942). Forward references without quotes (`NameError` not reported): mypy#948 (open), #17610, #9932. Constrained TypeVar `Need type annotation`: mypy#19618. Annotation-only dunders: mypy#2113 (open since 2016). `closed=True` before 3.15: mypy#21747 (open). Reflected operator message text: mypy#22316 / PR #22380 (different from draft 9).
* **pyright:** `Gauge.level` is `Clamped | int` for a data descriptor assigned in `__init__`: pyright#11382.
* **python/typing:** `class Callback[*Ts, **P = [bool]]` raises `TypeError` in CPython: python/typing#2211 (open; a runtime bug, the checkers follow the spec).
* **Fixed after our report:** ty#4934 (draft 2, ruff#30074). Fixed before the pin moved: ty#4883, ty#4884 (ty 0.0.97).

## 8. Known limitations

* **Generator.** All programs were written by a stand-in model (`claude-haiku-5.5`, effort `medium`; up to 2 sessions per day lack the effort field in the session file). Program quality was checked by preflight and by reading triage clusters, not per program. Eight operators are bare names (the model reads the name and guesses); Day 10 measured only the distance from the parent (140 of 151 mutants changed by more than 0.20), not whether the operator was applied.
* **Judge.** Deterministic, no LLM. It dismisses a finding only through a KB entry, a rule or a crash entry; each dismissal rule was checked by reading its hits, but entries such as `PRECISION-RUNTIME-CONSISTENT` and `LITERAL-WIDENING` close tens of rows per day. Evidence labels (`strong`, `medium`) are heuristics: Day 10 found a `SELF_CONTRADICTION` row that was a harness false positive, and rows where mypy's diagnostic on the same line was not paired.
* **Reading.** Most live findings are read only as triage clusters. Individually examined rows per day were a minority (Day 9: 33 of 224; Day 10: at most 39 of 172). The sets of rows never read can hide bugs.
* **Versions.** One target version (Python 3.13); tools pinned (ty 0.0.97 while 0.0.99 was out, pyright 1.1.414 from September). No build of `main` of any tool; no playground for drafts 3 to 12.
* **Duplicate search.** `gh search` matches words anywhere in text, not meaning. "None found" means the listed term sets returned nothing (for example 204 queries on Day 10), not that no duplicate exists.
* **Runtime oracle.** CPython evidence is only as good as the program executing the statement. Known artefacts since Day 5 and 6: `...` read as a variadic tuple, `runtime_miss` anchored on the wrong frame. `reveal_type` needs the checker's own expression, so CPython cannot confirm a reveal.
* **Crash hunting.** Closing a crash needs a source-shape predicate; the draft-1 expanding-receiver overflow (20 live crashes on Day 6) has no entry, so its parents were excluded from generation. Days 8 to 10 produced no new crash after drafts 1 and 7.
* **Coverage.** Day-10 plan sent 0 programs to `match_statement`, `recursive_aliases`, `dataclasses`, `tuples_unpacking` and `async_generators`; `final_classvar` and `protocols` gave 0 live findings in 18 programs. The `[holdout]` block of the stats files has 0 programs on Days 3 to 10, so the generated runs have no hold-out measurement.
* **Queued, never implemented:** `TY-NONFINAL-PATTERN`, `ASSERT-NEVER-ALL-REJECT`, wider `JOIN-VS-UNION`, a rule for reveals after an invalid type form, a mypy `Attribute function "__call__" ... does not accept self argument` matcher, KB entries for mypy#21937 and the mypy "Can only replace ParamSpec" message.
* **Day 2 target.** The plan's target of halving the review queue on the harvested corpus was not met (7.19 % overall, 5.78 % on the hold-out set), and the reviewer never approved.

## 9. Results that did not hold up

* ty#4656 (the first report) was closed as intended behaviour.
* Day 3's strong-evidence IntEnum alias and recursive alias candidates were artefacts (literal identity, the printer of recursive aliases).
* Day 10's strong-evidence set produced 0 new bugs by itself (10 programs: 5 duplicates, 4 not-a-bug, 1 mixed).
* Day 6 "no duplicate found" for the `Hashable` mypy candidate was later replaced by mypy#2455 / #18622.

## 10. Recommended filing order (unfiled drafts 10, 11, 12)

The user pastes these; the agent never files. Drafts 1 to 9 are already filed (section 5) and need no action unless the user wants to add the draft-2 or draft-3 context to the existing issues.

Before each filing: (1) run the reduced program on the matching playground (`<PLAYGROUND LINK>` is still a placeholder; use the pin and the newest version, and note that the playground's tool version may differ from the pinned one, for example pyright 1.1.414); (2) run one last **exact-title search** on the target tracker (`gh search issues "<exact title>" --repo <repo>` and the same for PRs, plus the nearest-title variants), because the trackers receive new reports daily (the last search for these three was 2026-11-06 or earlier); (3) copy the body without the fence lines and set the title from the draft.

| Order | Draft | Why this place in the order |
|---|---|---|
| 1 | **11** (mypy, lambda against a callback protocol) | Confidence 0.5. A direct inconsistency inside one tool: mypy rejects `def named_x(x: int)` and accepts `lambda x`, `lambda x, /` and `lambda y, z=0` for the same protocol, against the documented rule on parameter names (related closed docs issue mypy#8805). CPython raises `TypeError` for the keyword call; ty and pyright reject all four shapes; mypy 2.4.0, 2.4.1 and master behave the same. 19 issue and 7 PR queries found nothing. Risk: the maintainers may call the lambda leniency intended (a code comment in `infer_lambda_type_using_context` keeps the lambda's own names for ParamSpec contexts). |
| 2 | **10** (mypy, `possibly-undefined` after a swallowing `with`) | Confidence 0.4. Runtime `UnboundLocalError`, pyright reports it by default, ty reports it under its off-by-default rule, mypy does not even with `--enable-error-code possibly-undefined`, although mypy's type checker already models swallowing (`Missing return statement`). The `async with` form behaves the same. Risk: it is an opt-in check that works without type information, so it may be a known limit; the cause (`partially_defined.py`) was read, not instrumented. |
| 3 | **12** (pyright, `closed=` / `extra_items=` before 3.15) | Confidence 0.35. Pyright accepts both for `pythonVersion` 3.12 to 3.15; ty rejects below 3.15 (right) and mypy has the same gap in the open mypy#21747. Risk: the reporter of mypy#21747 and ty#4031 wrote that the arguments should be allowed in stub files and rejected at runtime, so pyright's maintainers may prefer not to version-gate; `typing_extensions.TypedDict` is valid on 3.13 and all three tools accept it. Search for a duplicate on pyright again just before filing and consider whether to link mypy#21747 and ty#4031. |

Order logic: evidence strength first (an inconsistency within one tool, then a gap in an opt-in check, then a version-gate question that already has a split verdict among the tools). All three have a confidence below 0.6; none should be described as confirmed.

## 11. What was NOT verified

* Drafts 10, 11 and 12 on a playground; drafts 3 to 9 on a playground by the user (not recorded).
* ty `main`, pyright `main`, mypy PR branches (for example PR #21942); none was built. A fix may already be on `main` for any open draft.
* Causes in mypy (`check_op_reversible` for draft 9, `partially_defined.py` for draft 10, `infer_lambda_type_using_context` for draft 11) were read from master source, not shown by instrumentation; draft 3 is the only cause confirmed by instrumenting mypy master.
* The reason ty#4934 was closed without a comment: the timeline shows ruff#30074 cross-referenced and merged the same day, so I read it as the fix; no maintainer text says so.
* Whether the `gh` author names are all accounts of the user; the task lists them as such and I did not check.
* How much of the changes in live rate comes from the KB versus the mix on Days 3 to 6 (no replay on the final KB), and for Days 7 to 10 beyond the KB rows shown in section 3.
* Most live findings of every day (section 8), in particular the unreduced Day-10 clusters (28 `reveal_mismatch | uncomparable`, 12 `only_ty` dunder `invalid-argument-type`, 17 `only_pyright runtime_contradicts`).
* Whether the eight least-used operators did what their names say.
* Day-6 candidates 2 (ty recursive alias solution) and 3 (mypy memory blow-up), never revisited.
* Whether any open duplicate in section 7 changed state after the day it was recorded.

## 12. Final state of the repository checks (run on 2026-11-06 for the Day-10 report)

* `.venv/bin/python -m pytest tests -q`: 730 passed.
* `.venv/bin/typediff --python-version 3.13 kb-selftest`: 20 PASS, 0 FAIL.
* `python scripts/check_hits.py 0.80`: 36 files, 0 with problems.
* Pins unchanged: mypy 2.4.0, ty 0.0.97, pyright 1.1.414, CPython 3.13.16.
* Report files: `results/days/day10-report.md` (Day 10 vs Day 9) and this file.
