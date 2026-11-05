# Day 3 candidates: verification summary (Day 4 consolidate)

Source files: `campaign/day4/verify-v1.md` (checker crashes), `verify-v2.md` (stale alias, tuple fold, property, Flag), `verify-v3.md` (IntEnum, metaclass operator, recursive alias, `__hash__`).
Date of runs: 2026-11-05. Pinned = project venv (mypy 2.4.0, ty 0.0.84, pyright 1.1.414). Latest = mypy 2.4.1, ty 0.0.97, pyright 1.1.414. Master = mypy 2.5.0+dev.879da562 (ty and pyright have no master build here). CPython 3.13.16.
Nothing was filed, pushed or posted. Playground links are not created (UNVERIFIED-PLAYGROUND everywhere).

## Verdict table

"Draft written" refers to `campaign/day3-issue-drafts.md`. Duplicate status "none found" means the searches in the drafts' duplicate-check summaries returned no match; it is not proof.

| Candidate | Per-tool verdict | Taxonomy class | Dismissal class / URL | Confidence | Duplicate status | Pinned vs latest | Draft written |
|---|---|---|---|---|---|---|---|
| C1 self-referential `__call__` attribute (4 programs) | ty BUG; mypy BUG; pyright NOT_BUG | CRASH (ty stack overflow, mypy segfault); pyright SPEC_AMBIGUITY | ty: DUPLICATE https://github.com/astral-sh/ty/issues/4148; mypy: DUPLICATE https://github.com/python/mypy/issues/22361 | ty 0.90, mypy 0.95, pyright 0.50 | duplicate (both) | identical; ty, mypy crash on pinned, latest and mypy master | no |
| C2 protocol `flatten` (`self: Stream[Stream[T]]`) | ty BUG; mypy NOT_BUG; pyright NOT_BUG | CRASH (ty stack overflow); mypy, pyright NOISE | none (new). Related: ty#4746, #4882 (open), #4694, #4863 (closed) | ty 0.80 | none found | identical on ty 0.0.84 and 0.0.97; mypy and pyright accept | yes (v1 draft 1, ty) |
| C3 `partial \| None` in a loop | ty 0.0.84 BUG; ty 0.0.97, mypy, pyright NOT_BUG | CRASH (salsa panic) on pinned only; others NOISE | fixed in ty 0.0.85, not reportable | 0.97 / 0.95 | not applicable (fixed) | differs: pinned panics, latest reports `unsupported-operator` like the others | no |
| 1a stale alias condition (alias, then method call) | ty NOT_BUG; mypy NOT_BUG; pyright NOT_BUG | ty: INCORRECT_INFERENCE already tracked; mypy KNOWN_LIMITATION; pyright DESIGN_DIVERGENCE | ty: DUPLICATE https://github.com/astral-sh/ty/issues/2792; mypy: https://github.com/python/mypy/issues/13807 | 0.8 (ty), 0.9 (mypy, pyright) | duplicate | identical | no |
| 1b alias narrowing survives reassignment over a loop back edge | ty BUG; mypy NOT_BUG; pyright NOT_BUG | INCORRECT_INFERENCE, observable as FALSE_NEGATIVE | none (new). Related: ty#4379, ty#719, ruff#24302, ty#2792 | 0.9 | none found | identical on 0.0.84 and 0.0.97 | yes (v2 draft 1, ty) |
| 2 constant fold tuple subclass | ty NOT_BUG; mypy NOT_BUG; pyright NOT_BUG | ty: DESIGN_DIVERGENCE (missing override diagnostic) | DUPLICATE https://github.com/astral-sh/ty/issues/2171 (design in https://github.com/astral-sh/ty/issues/2140) | 0.85 | duplicate | identical | no |
| 3 read-only property `Never` | ty NOT_BUG; mypy NOT_BUG; pyright NOT_BUG | INCORRECT_INFERENCE caused by stale attribute narrowing; Day-3 claim "ty is silent" refuted | DUPLICATE https://github.com/astral-sh/ty/issues/2792 | 0.8 | duplicate | identical | no |
| 4 Flag combination `Never` | ty NOT_BUG as new; mypy NOT_BUG; pyright NOT_BUG | INCORRECT_INFERENCE (Flag support) | DUPLICATE https://github.com/astral-sh/ty/issues/876 | 0.9 | duplicate | identical | no |
| 5 IntEnum alias (`Integer.TRUE`) | ty NOT_BUG (ty is right); mypy NOT_BUG; pyright NOT_BUG | mypy FALSE_POSITIVE / INCORRECT_INFERENCE (already reported); pyright KNOWN_LIMITATION | mypy: DUPLICATE https://github.com/python/mypy/issues/16830 and https://github.com/python/mypy/issues/21117; pyright: https://github.com/microsoft/pyright/issues/11100 | ty 0.9, mypy 0.85, pyright 0.85 | duplicate (mypy, pyright) | identical on pinned, latest, mypy master | no |
| 6a metaclass reflected operator `A * B` | mypy BUG; pyright NOT_BUG; ty NOT_BUG (right) | mypy FALSE_POSITIVE (shows as INCORRECT_INFERENCE); pyright DESIGN_DIVERGENCE | mypy: none (new). pyright: https://github.com/microsoft/pyright/issues/4088, #3368, #10644 | mypy 0.7, pyright 0.7, ty 0.9 | none found (mypy) | identical on mypy 2.4.0, 2.4.1, master | yes (v3 draft 1, mypy) |
| 6b metaclass reflected operator `A \| B` | ty NOT_BUG (duplicate); mypy and pyright as 6a | ty INCORRECT_INFERENCE (already reported) | ty: DUPLICATE https://github.com/astral-sh/ty/issues/4683 | 0.9 (ty) | duplicate (ty) | identical | no |
| 7 recursive TVT-default alias tuple reveal | mypy NOT_BUG; ty NOT_BUG; pyright NOT_BUG | mypy DESIGN_DIVERGENCE (recursive placeholder prints as `...`; no narrowing on annotated assignment) | mypy: DUPLICATE https://github.com/python/mypy/issues/2008 | mypy 0.85, ty 0.9, pyright 0.9 | duplicate (narrowing part); `...` display not reported | identical | no |
| 8a `__hash__` None reveal (the Day-3 reveal) | mypy NOT_BUG; ty NOT_BUG; pyright NOT_BUG | ty: NOISE (unreachable code after a statically false assert); mypy underlying FALSE_NEGATIVE | mypy: DUPLICATE https://github.com/python/mypy/issues/20230 (also #18622, #2455) | mypy 0.9, ty 0.8, pyright 0.9 | duplicate (mypy) | identical | no |
| 8b `Hashable` accepts a class with `__eq__` and no `__hash__` | ty BUG; mypy NOT_BUG (duplicate); pyright NOT_BUG (right) | ty FALSE_NEGATIVE | ty: none (new). Related: ty#3781, ruff#27441 | ty 0.7 | none found | identical on 0.0.84 and 0.0.97 | yes (v3 draft 2, ty) |

New findings with a draft: C2 (ty crash), 1b (ty narrowing), 6a (mypy operator), 8b (ty hashability). All four have a reproducer under `runs/hits/d4v_*.py` (git-ignored; on disk only). Day-3 "strong" evidence for IntEnum alias and recursive alias was an artefact of literal identity and the recursive `...` printer, so neither is a bug.

## Cross-check of the three verify files

Every verdict, confidence and URL in the table above was compared with the bottom-line tables and the VERDICT sections of `verify-v1.md` (C1 to C3), `verify-v2.md` (1a, 1b, 2, 3, 4) and `verify-v3.md` (1 to 4), and with the `[Plan §6 / verify ...]` lines of `campaign/day4-run-log.md`. No verdict, number or URL differs between the files. Differences of wording only:

- v2 labels candidate 4 "NOT_BUG as a new finding, underlying INCORRECT_INFERENCE, faulty_tool ty (already tracked)"; v3 labels the same kind of case (IntEnum, 6b) "NOT_BUG (underlying ...)". Both mean: a real defect that is already reported, so no new report. The table uses the same convention.
- v1 reports mypy master as INTERNAL ERROR (uncompiled) and mypy 2.4.x as SIGSEGV for C1. The table says "crash" for all three.
- v2 and v3 say pinned, latest and master output were identical for every program; v1 shows one exception, C3 (ty 0.0.84 panics, 0.0.97 does not). The table follows v1 for C3.
- The Day-3 report called IntEnum alias and recursive alias "strong" evidence. v3 refutes both (literal identity, recursive `...` printer). The table follows v3.
- The format reference `temp/issue_drafts.md` named in the task does not exist; the drafts file keeps the format of `issue-drafts-v1.md` to `-v3.md`.

Commands: this file and `day3-issue-drafts.md` were written from the verify and draft files with no checker re-run. The commands behind the numbers are listed in each verify file (section "Command template"/"Setup"); the drafts file was concatenated by `/tmp/cons/build.py` (reads `campaign/day4/issue-drafts-v{1,2,3}.md`, renumbers, adds a duplicate-check and not-checked note per draft; it asserts exactly 4 drafts and ran without error).

## Day-4 side outcomes

| Item | Outcome | Evidence |
|---|---|---|
| ty#4656 (Self parameter not enforced on inherited methods) | Design difference, not a bug. Closed "not planned" 2026-10-05; ty#4673 closed as duplicate 2026-10-05; ty#4849 closed as duplicate 2026-10-28 (carljm: intentional). The pipeline already dismisses Self-parameter findings as DESIGN_DIVERGENCE via `kb:TY-SELF-UPPER-BOUND`, while a real crash through Self-typed state stays in REVIEW. Only wording and data changed: `known_upstream.json` TY-4656 note ("reported by us, closed as intended behaviour (design divergence), not a bug"), TY-4673 stance `open` to `duplicate-of`, plus `kb.py`, README, seeds/README, DESIGN §8, FUZZING_PLAN §1. No code change, no new tests. Suites (`test_phase3`, `test_upstream_day3`, `test_kbloop_upstream`, `test_kb_fixD`) pass: 213 passed. | `campaign/day4/fix-4656.md`; commits 074ceb4 (data/wording) and adead10 (log) |
| Flaky `test_timeout_kills_grandchild` | Not reproduced before the fix (30/30 with 4 burners, 30/30 with 72 burners on 24 cores). After a first rewrite 1/30 failed under load: `_alive()` raised ProcessLookupError reading `/proc/<pid>/stat` as the process exited. Test-only fix: timeout 1s to 5s, atomic pidfile write, polling with 30s deadlines, `_alive` tolerates FileNotFoundError/ProcessLookupError, `finally` kills the grandchild. Production `_exec` (killpg on timeout) unchanged. After the fix: 30/30 under 4 burners, 3/3 full suites at 360 passed. | `campaign/day4-run-log.md` `[Plan §3 daily loop / flaky-test]`; commit 1c3cd05 |

## Retire recommendations (to be added by the Day-4 morning step, not added here)

Patterns that are design differences, known limitations or already reported upstream:

| Pattern | Add as | URL | Note |
|---|---|---|---|
| ty stack overflow on self-referential `__call__` (`__call__: "C"`, `Self \| None`, mutual pairs) | upstream entry `TY-4148` | https://github.com/astral-sh/ty/issues/4148 | No entry exists, so Day-3 showed it as a live crash. The mypy twin is already covered by `MYPY-22361`. |
| ty `A \| B` ignores metaclass `__or__` | upstream entry | https://github.com/astral-sh/ty/issues/4683 | Open. |
| ty attribute narrowing not invalidated by calls (stale alias after method call; read-only property `Never`) | upstream entry | https://github.com/astral-sh/ty/issues/2792 | Open. Covers candidates 1a and 3. |
| ty constant folding of tuple-subclass comparison | upstream entry, DESIGN_DIVERGENCE | https://github.com/astral-sh/ty/issues/2171, design in https://github.com/astral-sh/ty/issues/2140 | `calibration/must_stay_live/ty_constant_fold_tuple_subclass.py` still reproduces. |
| ty Flag combination `Never` | extend KB entry `TY-876` | https://github.com/astral-sh/ty/issues/876 | Gap: `TY-876` only matches `reveal_mismatch` and `type-assertion-failure`. An `only_mypy` `arg-type` where ty is silent because Flag-derived `Never` made the line unreachable is not matched. |
| mypy no aliased-condition narrowing | KB, KNOWN_LIMITATION | https://github.com/python/mypy/issues/13807 | pyright documents the same limit for member-access chains (DESIGN_DIVERGENCE). |
| mypy enum value aliases (`TRUE = 1` after `ONE = 1`) | upstream entry | https://github.com/python/mypy/issues/16830, https://github.com/python/mypy/issues/21117 | pyright side: https://github.com/microsoft/pyright/issues/11100, maintainer declines (KNOWN_LIMITATION). ty is correct. |
| mypy declared type not narrowed on initial assignment, recursive alias printed with `...` | upstream entry (DESIGN_DIVERGENCE) | https://github.com/python/mypy/issues/2008 | Evidence rule "runtime value does not inhabit the revealed type" mis-fires when the text contains a recursive-alias `...`. A normalizer treating that `tuple[X, ...]` as opaque would remove the class. |
| mypy `__eq__` without `__hash__` still hashable | upstream entry | https://github.com/python/mypy/issues/20230, https://github.com/python/mypy/issues/18622, https://github.com/python/mypy/issues/2455 | Open. |
| pyright reflected operator priority | KB, DESIGN_DIVERGENCE | https://github.com/microsoft/pyright/issues/4088, https://github.com/microsoft/pyright/issues/3368, https://github.com/microsoft/pyright/issues/10644 | Maintainer: as designed (instances). Applies to the metaclass case as well. |
| ty reveals `Never` after a statically false assert (e.g. `assert Plain.__hash__ is None`) | noise rule, not an upstream entry | none | Unreachable-code evaluation. |
| ty `Self` parameter not enforced on inherited methods | already retired: `TY-4656` (stance `intended`), KB `TY-SELF-UPPER-BOUND` | https://github.com/astral-sh/ty/issues/4656, https://github.com/astral-sh/ty/issues/4849 | Nothing to add. Optional: a `TY-4849` prior stance (closed duplicate, carljm: intentional); none exists yet. |
| ty `partial \| None` in a loop panic | none | fixed in ty 0.0.85 | Retire only for pinned ty 0.0.84; disappears on a pin bump. |

Do not retire: C2, 1b, 6a, 8b (new, drafts written, not yet filed).
