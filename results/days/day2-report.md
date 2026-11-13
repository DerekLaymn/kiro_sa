# Day-2 P1 run report (typediff pipeline campaign)

> Paths written as `[campaign working file]`, `[run output]`, `[agent working file]` or `[temp file]` point to scratch files of the original campaign that are not part of this repository.

Goal of the run: improve the pipeline (the internal plan §3 P1), not hunt bugs. Branch [campaign working file], local only, nothing pushed. `TYPEDIFF_LLM=null` throughout: 0 LLM calls. All numbers below are copied from [run output] (git-ignored, regenerable) and from [campaign working file], which has the per-action detail and the evidence file for each claim.

**Outcome in one paragraph.** The review queue shrank 7.19 % overall (7841 -> 7277), 7.54 % on the tuning set (6300 -> 5825) and 5.78 % on the hold-out set (1541 -> 1452). The plan's > 50 % target was **not met** on either set. The reviewer never approved (3 rounds, `approved=false` each time). The remaining queue is dominated by expectation-comment programs from the ty/mypy/pyright test suites that need a per-construct oracle, and by candidate false negatives. Plan §7 forbids inventing dismissals, so none were invented. The pipeline got safer as well as smaller: the review found and this run fixed five false-dismissal holes (section 5).

---

## 1. Plan step -> what was done

Legend: **done** = followed the plan as written; **off-plan** = deviation, reason given; **skipped** = not done. All commands run from the repo root with venv binaries by absolute path (the fish shell rejected `source activate`). Abbreviations: `PY=.venv/bin/python`, `L=TYPEDIFF_LLM=null`.

| Plan step | Status | Exact command / action |
|---|---|---|
| Branch setup | done | `git checkout -b [campaign working file] main` |
| §4 Setup: venv, versions | done | `.venv/bin/python --version; .venv/bin/python -m pip list`. Found pyright 1.1.400 (not the pinned 1.1.414) |
| §4 Setup: pin pyright | off-plan (plan says `pip install ... pyright` unpinned; docs/design.md/calibration pin 1.1.414) | `.venv/bin/python -m pip install pyright==1.1.414` ([campaign working file]) |
| §4 Setup: `fetch-docs` | done | `typediff fetch-docs > [campaign working file]` (862 chunks) |
| §4 Setup: `kb-selftest` | done | `typediff --python-version 3.13 kb-selftest > [campaign working file]`: 11 PASS, 0 other |
| §4 Setup: pytest baseline | done (extra check, not in §4) | `.venv/bin/python -m pytest tests -q`: 144 passed |
| §4 Setup: harvest | done (see Day 1 d) | |
| §4 Setup: OpenRouter env vars | skipped | no LLM in this run (task constraint) |
| §3 Day 1 (a) Setup (§4) | done | rows above |
| §3 Day 1 (b) check `known_upstream.json` | done, read-only | read `typediff/data/known_upstream.json`; ids/URLs in [campaign working file]. 5 entries (TY-1090, TY-4212, TY-2255, MYPY-9658, MYPY-948), 4 prior_stances (TY-4656, TY-4152, TY-4673, TY-1172). Nothing added in Stage 1 |
| §3 Day 1 (c) `typediff seeds seeds/` | done | `L typediff --python-version 3.13 seeds seeds/ > [campaign working file]`: 29 programs, 35 discrepancies, 25 live, 14 programs with live findings, 0 crashes (plan prose says 27 seeds / 16 with findings: stale) |
| §3 Day 1 (d) harvest | done | `.venv/bin/python scripts/harvest_seeds.py > [campaign working file]`: 5129 files (plan prose says 4,849: stale; script now also harvests pyright and typeshed and filters ty mdtests by python version) |
| §3 Day 1 (e) | not a plan step | the plan's Day 1 list has four bullets (setup, known_upstream, seeds, harvest). The kb-selftest and pytest runs are part of (a) |
| §3 Days 2-3 corpus run | done, interrupted and resumed (off-plan, no pipeline change) | `env TYPEDIFF_LLM=null .venv/bin/python scripts/kbloop_run.py [run output] seeds/harvested --jobs 14 --progress [run output] > [run output] 2>&1`. Died at 2850/5129 when the hosting tool call was cut off; the identical command was re-run (resumable): `total=5129 {'skip': 2876, 'ok': 2229, 'rejected': 24}`. `--jobs 14` kept although the later allowance was 20 (not restarted) |
| §3 Days 2-3 stats | done | `kbloop_stats.py [run output] --split [run output] --json [run output] > [run output]` |
| 80/20 tuning / hold-out split | done (plan §3 does not name this step; the KB-loop docs do) | `.venv/bin/python scripts/kbloop_split.py seeds/harvested [run output] > [run output]`. Written to [run output], not over the tracked `docs/kb-loop-split`, because that split belongs to the teammate's older 6089-program corpus (1003 of the 1025 new hold-out files are in the old hold-out, 22 are new) |
| Triage (§3 `typediff triage`), each round | done | `typediff triage [run output]<N-1> --top 30 --details` ([campaign working file]<N>-triage-top30.txt) and `.venv/bin/python scripts/kbloop_patterns.py [run output]<N-1> --split [run output] --top 40 --md [campaign working file]<N>-patterns-tuning.md` (round 1); `--set tuning|holdout` in rounds 2-3. Samples: `scripts/kbloop_sample.py ... --split [run output]` (its default is the old split) |
| Triage checklist (§6), each pattern | done, items (5) duplicates read-only, item (6) playground **UNVERIFIED-PLAYGROUND** for every pattern | reproduce on mypy, ty, pyright, CPython with [campaign working file]; spec grep; `gh api search/issues` and `gh search issues` (read-only); toggle experiments |
| Decide (§3 four-way choice) | done | outcomes per pattern in section 4. `known_upstream.json`: **no entry added**, because no real upstream issue matched an auto-closable pattern and an entry without a real URL would be invented. KB entries used instead (repo precedent: MYPY-15182-NEW-RETURNS) [off-plan relative to decision (i)] |
| Re-measure, round 1 | done | `PY scripts/kbloop_replay.py [run output] [run output] --jobs 14 --verify-sample 100`, then `kbloop_stats.py [run output] --split [run output] --json [run output]`. verify-sample 100/100 identical |
| Re-measure, round 2 | done | same with `out1 -> out2`. Replay run twice; the first (`out2-pre-guard`) fed an audit that led to a guard, numbers below are from the final replay. verify-sample 100/100 |
| Re-measure, round 3 | done | same with `out2 -> out3`. verify-sample 100/100 |
| Reviewer loop | done, 3 rounds, never approved | verdicts: [campaign working file] (`day2-review-round.json` is a copy of the latest). Review docs: [campaign working file] |
| Round 1 | done | patterns 1-8 triaged; typenorm bytes fix, 2 KB entries, ANNOTATION-ONLY-READ generalised |
| Round 2 (reviewer's 7 issues) | done | constant-fold hole, pyright agreement, 3 new KB entries, normaliser refinements; deviation: must-stay-live programs go to a new `calibration/must_stay_live/` instead of `calibration/negatives/` (negatives are by definition programs that must be closed; mixing opposite semantics would corrupt that metric) |
| Round 3 (reviewer's issues) | done, one user decision | stopped and asked before changing NameError behaviour (`send_message` warning); user chose option (a) plus the hint of (c), no dismissal |
| Calibration regression (§8 'Calibration', re-run each round) | done, approximated | `scripts/kbloop_calib_subset.py` in 4 chunks with `--negatives`, same settings as `typediff --no-pyright calibrate`; positives = 194 open maintainer-labelled reports fetched read-only from GitHub REST without auth (the README baseline of ty 80 / mypy 76 was on an older issue set) |
| Calibration `--no-pyright` caveat | off-plan | the full `typediff calibrate` with pyright was not run |
| §3 P2-P6 (LLM mutation, generation, crash hunting, judging, filing, write-up) | skipped | outside P1 and forbidden by the no-LLM, no-GitHub-write constraint |
| Filing issues / contacting maintainers | skipped | no GitHub write of any kind |
| Push / PR | skipped | local branch only |

---

## 2. Tool versions

Verified with `.venv/bin/python -m pip list` after the pin:

| Component | Version |
|---|---|
| Python (venv) | 3.13.16 |
| CPython used as runtime oracle / target | 3.13 (`--python-version 3.13`) |
| ty | 0.0.84 |
| mypy | 2.4.0 |
| pyright | 1.1.414 (pinned; the venv initially had 1.1.400) |
| typing_extensions | 4.16.0 |
| pytest | 8.3.5 |
| typediff | 0.1.0 (editable from the repo) |

`pyright --version` printed nothing in the captured output; the pip metadata is the evidence for the pin. Pyright itself was exercised through the pipeline and gave real diagnostics in every round.

---

## 3. Funnel numbers

Corpus: 29 hand seeds (Stage 1, not in the split) and 5129 harvested programs. 5086 produced reports; 43 were rejected by preflight (non-stdlib import or non-determinism). 0 timeouts, 0 runner errors. Tuning = 4072 programs ran (4104 in the set), hold-out = 1014 ran (1025 in the set).

### 3.1 Baseline (out0) vs after (out3)

| Metric | Baseline all | After all | Baseline tuning | After tuning | Baseline hold-out | After hold-out |
|---|---|---|---|---|---|---|
| Programs run | 5086 | 5086 | 4072 | 4072 | 1014 | 1014 |
| Discrepancies | 10615 | 10597 | 8486 | 8469 | 2129 | 2128 |
| **Review queue (live)** | **7841** | **7277** | **6300** | **5825** | **1541** | **1452** |
| Auto-closed (dismissed) | 2784 | 3330 | 2194 | 2652 | 590 | 678 |
| Programs with live findings | 2642 | 2566 | 2120 | 2058 | 522 | 508 |
| Tool crashes (each also a live finding) | 10 | 10 | 8 | 8 | 2 | 2 |
| Shrink of the queue | | **7.19 %** (-564) | | **7.54 %** (-475) | | **5.78 %** (-89) |
| 50 % target (strictly less than half) | <= 3920 | **not met** | <= 3149 | **not met** | <= 770 | **not met** |

Checks: 5825 + 1452 = 7277 and 6300 + 1541 = 7841. Findings = live + dismissed (baseline 10625 = 7841 + 2784; the 10 extra over discrepancies are the crash findings).

### 3.2 Auto-closed by category

| Category | All base | All after | Tuning base | Tuning after | Hold-out base | Hold-out after |
|---|---|---|---|---|---|---|
| DESIGN_DIVERGENCE | 1667 | 1619 | 1334 | 1347 | 333 | 272 |
| SPEC_AMBIGUITY | 458 | 458 | 335 | 335 | 123 | 123 |
| KNOWN_LIMITATION | 286 | 656 | 227 | 508 | 59 | 148 |
| INVALID_TEST | 242 | 242 | 192 | 192 | 50 | 50 |
| NOISE | 60 | 284 | 56 | 220 | 4 | 64 |
| CONFIG_ARTIFACT | 58 | 58 | 41 | 41 | 17 | 17 |
| DUPLICATE | 13 | 13 | 9 | 9 | 4 | 4 |

DESIGN_DIVERGENCE fell overall (1667 -> 1619) although MYPY-FIRST-ASSIGNMENT-TYPE added 182, because ANNOTATION-ONLY-READ (334 findings at the end) was re-categorised from DESIGN_DIVERGENCE to KNOWN_LIMITATION in round 2. I did not break the 48-finding net drop down further.

### 3.3 Per round (cumulative against the Stage-2 baseline 7841 / 6300 / 1541)

| State | Overall live | Tuning live | Hold-out live | Overall shrink | Tuning shrink | Hold-out shrink | Discrepancies (all) | Dismissed (all / tuning / hold-out) | Programs with live (all / tuning / hold-out) |
|---|---|---|---|---|---|---|---|---|---|
| Baseline (out0) | 7841 | 6300 | 1541 | | | | 10615 | 2784 / 2194 / 590 | 2642 / 2120 / 522 |
| After round 1 (out1) | 7470 | 5960 | 1510 | 4.73 % | 5.40 % | 2.01 % | 10601 | 3141 / 2521 / 620 | 2595 / 2081 / 514 |
| After round 2 (out2) | 7351 | 5877 | 1474 | 6.25 % | 6.71 % | 4.35 % | 10597 | 3256 / 2600 / 656 | 2570 / 2061 / 509 |
| After round 3 (out3) | 7277 | 5825 | 1452 | 7.19 % | 7.54 % | 5.78 % | 10597 | 3330 / 2652 / 678 | 2566 / 2058 / 508 |

Change within each round:

| Round | Overall | Tuning | Hold-out |
|---|---|---|---|
| 1 | 7841 -> 7470 (-371, -4.73 %) | 6300 -> 5960 (-340, -5.40 %) | 1541 -> 1510 (-31, -2.01 %) |
| 2 | 7470 -> 7351 (-119, -1.59 %) | 5960 -> 5877 (-83, -1.39 %) | 1510 -> 1474 (-36, -2.38 %) |
| 3 | 7351 -> 7277 (-74, -1.01 %) | 5877 -> 5825 (-52, -0.88 %) | 1474 -> 1452 (-22, -1.49 %) |

Tuning-vs-hold-out gap (percentage points): 3.4 after round 1, 2.4 after round 2, 1.8 after round 3. It narrowed because rounds 2 and 3 added entries that fire across families (REVEAL-ERROR-RECOVERY: 60 hold-out dismissals), and because the over-fitted ASSERT-TYPE-LITERAL-RETENTION lost its hold-out hits when the bool-literal hole was closed (4 -> 0). The tuning number still overstates generalisation by 1.8 points.

### 3.4 Review queue by kind, baseline vs after (all programs)

| Kind | Baseline | After |
|---|---|---|
| only_mypy | 2759 | 2551 |
| reveal_mismatch | 2390 | 2103 |
| only_ty | 1833 | 1764 |
| concern_mismatch | 750 | 750 |
| runtime_miss | 69 | 69 |
| reveal_unpaired | 30 | 30 |
| crash | 10 | 10 |

### 3.5 Candidates

Candidates (plan decision (iv), Phase-2 parents) in the funnel: 2 programs copied to [run output] and 3 more recorded in the log only (section 6). Confirmed, filed, acknowledged: 0 / 0 / 0. The remaining queue holds 145 mypy false-negative rows for unbound names (section 5) that are candidates in principle but unverified.

### 3.6 Largest remaining tuning patterns (after round 3, from [campaign working file])

reveal gradual 456, uncomparable 444, different 403, ty_more_precise 299, only_mypy [assignment] 197, only_mypy [assert-type] 197, only_ty [type-assertion-failure] 157, only_ty [unresolved-reference] 129, only_mypy [arg-type] 118, concern_mismatch [assignment] 114. In round 1 the starting order was gradual 623, different 552, uncomparable 476, only_mypy [assignment] 370, only_mypy [assert-type] 228.

### 3.7 Other measurements per round

| Round | pytest | kb-selftest | Calibration (30 s checker timeout, `--no-pyright`, positives 194) |
|---|---|---|---|
| Start | 144 passed | 11 PASS | Stage-2 code: positives kept 117 / invisible 61 / dismissed 11 / excluded 5; 24 dismissed of 212 rows (13 of 18 negatives closed) |
| 1 | 157 passed | 13 PASS | positives identical; 28 of 216 (17 of 22 negatives closed) |
| 2 | 176 passed | 15 PASS | positives identical; 30 of 220 (19 of 26 negatives closed) |
| 3 | 201 passed | 15 PASS | positives identical; 32 of 220 (21 of 26 negatives closed); must-stay-live 2 live, 0 violated |

The same 11 positives are dismissed before and after (mypy-4554, 5289, 6079, 7984; ty-1090, 1172, 4713, 4786, 4817, 4835, 4872), all by pre-existing entries. **No real bug was newly dismissed by any change in this run.**

---

## 4. Pipeline changes and pattern decisions

### 4.1 Changes (file, what, why, test, effect on the queue)

| # | Commit | File(s) | What | Why | Test | Effect on queue |
|---|---|---|---|---|---|---|
| 1 | d171b92 | typediff/typenorm.py | Tokenise bytes literals and print them as `b"..."`; add `deep_widen` and `is_literal_retention` | mypy prints `Literal[b'a']`, ty/pyright `Literal[b"a"]`; the normaliser split `b` from the string and classed the pair UNCOMPARABLE (harness defect) | tests/test_stage3_round1.py | 14 findings disappeared (the pairs became equal), plus 2 cascade dismissals |
| 2 | fbf9b12 | typediff/kb.py, calibration/negatives/*, tests | New KB entry MYPY-FIRST-ASSIGNMENT-TYPE (DESIGN_DIVERGENCE, verify-gated by `mypy --allow-redefinition`); new ASSERT-TYPE-LITERAL-RETENTION; ANNOTATION-ONLY-READ accepts several undefined names | Recurring noise: mypy fixes a function-local name's type at first assignment; assert_type literal retention is open in the spec; `u(D_C, A_C)` stayed live although each name satisfied the entry | 13 tests in test_stage3_round1.py; kb-selftest 13 PASS | Round 1: -357 live (+182 first-assignment [171 tuning / 10 hold-out at round 1], +130 assert-type, +39 annotation-only) |
| 3 | 0cd8539 | typediff/kb.py (text) | Cite the conformance suite's "either is acceptable" note in the assert-type entry | Source for the one-sided literal claim | | none |
| 4 | c1d243b | typediff/kb.py, typenorm.py, calibration/must_stay_live/, tests | `has_bool_literal`: assert-type retention never matches a type containing `Literal[True/False]`; the same exclusion added to INFERENCE-DOWNSTREAM; pyright must be silent or report the same assert_type mismatch; ANNOTATION-ONLY-READ re-categorised KNOWN_LIMITATION, cites python/mypy#15416, #17373, #4019, #11342 | Reviewer round 1: ty folds `R((1,)) < (1,)` to `Literal[False]` while CPython prints `True`, and the pipeline closed it as "literal retention"; the entry text said the other tool is silent but pyright was never checked (75 of 130 dismissals had a pyright diagnostic) | tests/test_stage3_round2.py (incl. `test_constant_fold_program_stays_in_review` through the real pipeline) | Re-opened 66 (ASSERT 130 -> 64) and 10 (INFERENCE-DOWNSTREAM) findings; widened the queue on purpose |
| 5 | 9456642 | typediff/kb.py | New REVEAL-ERROR-RECOVERY (NOISE, auto, runtime_override on): one side exactly `Unknown` (ty) or `Any` (mypy), the other has no gradual part, and the same tool reports an error inside the `reveal_type` argument | A tool reveals its recovery type for an expression it just rejected; the error is its own finding and stays live | test_stage3_round2.py (4 unit + 1 real tools), negative reveal_error_recovery.py, kb-selftest | Round 2: +151 |
| 6 | 1b708d4 | typediff/typenorm.py | Intersections `A & X` / `A & ~X` refine `A`; `LiteralString` <: `str`; `type[X]` <: `type`; `Never` <: everything (invariance kept: `list[LiteralString]` vs `list[str]` stays different) | Spec literal.rst / special-types.rst; these were classed "different" | test_stage3_round2.py (2 tests) | +3 PRECISION-RUNTIME-CONSISTENT; 4 findings vanish (`int | Never` == `int`); pattern "different" 558 -> 403, ty_more_precise 189 -> 297 (a relabel, not a dismissal) |
| 7 | ba8fbe0 | typediff/kb.py | New MYPY-13807-ALIASED-CONDITIONS (KNOWN_LIMITATION, auto, runtime_override on): ty_more_precise reveal inside `if alias` / `if not alias` with the alias bound once before | mypy does not narrow through aliased conditions (python/mypy#13807, open feature request); pyright and ty agree | test_stage3_round2.py (positives, 6 negatives, flag, real tools), negative mypy_aliased_condition.py | Round 2: +38 |
| 8 | 69f5ff6 | typediff/kb.py | REVEAL-ERROR-RECOVERY never dismisses a statement on which CPython raised any exception | Audit found `reveal_type(super())` at module level raising RuntimeError | tests | first replay's 152 -> final 151 (+ none with exceptions on the statement) |
| 9 | 10dd9b1 | typediff/kb.py, typediff/calibration.py, typediff/cli.py, scripts/kbloop_calib_subset.py, tests, calibration/must_stay_live/mypy_stale_alias.py, negatives | (a) Stale-alias guard `_target_changed_between` for MYPY-13807; (b) the REVEAL-ERROR-RECOVERY example and negative no longer need pyright (`def g(a: int, b: str): reveal_type(a + b)`); (c) `typediff calibrate --must-stay-live` loads `calibration/must_stay_live/` and reports violated programs | Reviewer round 2: alias computed before `a.clear()` was still dismissed; negatives stayed open under `--no-pyright`; calibrate could not see the fold hole | test_stage3_round3.py (11 stale-alias cases, calibration loader and summary tests) | Round 3: +2 re-opened (tuning); negatives closed 19 -> 21 of 26 |
| 10 | a4147b3 | typediff/rules.py, typediff/kb.py, tests/test_evidence_fixA.py, test_stage3_round3.py | `attach_runtime_evidence`: a CPython NameError/UnboundLocalError on a name the reporting tool flags is STRONG evidence for the reporting tool, blame on the silent tool (was neutral/weak; `kb.runtime_contradiction` already said strong). New hint-only MYPY-UNBOUND-OPT-IN-CHECK (auto=False) shown only when the mypy opt-in toggle (`--enable-error-code possibly-undefined --enable-error-code used-before-def`) removes the discrepancy; `_verified_hints` in rules.py | Two code paths disagreed on NameError; user decision: option (a) + hint, no dismissal | 5 new tests, replaced the old "is_not_strong" test | **zero** (as predicted); with an LLM, strong evidence can now blame mypy for those rows |
| 11 | d924841 | typediff/kb.py | REVEAL-ERROR-RECOVERY also covers a reveal through a name bound at a statement the same tool rejected (`_error_at_binding_of_reveal_arg`) | 57 tuning + 23 hold-out gradual rows had a flagged binding (unpacking, `type()` call, undefined base) | 4 tests (both tools, narrowness, CPython exception, real tools) | Round 3: -76 (54 tuning in 30 programs, 22 hold-out in 12 programs) |
| 12 | docs commits (b4bf9e8, 7f2969d, d479c03, 13aae01, 528bd1a and the final commits of this stage) | [campaign directory] | logs, stats, audits, helper scripts, reviewer verdicts | | | none |

kb-selftest ended at 15 PASS, 0 FAIL; pytest at 201 passed.

### 4.2 Pattern decisions with per-tool verdicts

Verdict vocabulary: DESIGN_DIVERGENCE, KNOWN_LIMITATION, FALSE_NEGATIVE (the tool misses something CPython or the spec confirms), INCORRECT_INFERENCE, "no bug". "Candidate" means kept live and not dismissed.

| Pattern (tuning rank at start) | ty verdict | mypy verdict | Decision |
|---|---|---|---|
| reveal gradual 623: ty `Unknown` / mypy `Any` after the same tool's own error | no bug (error-recovery type) | no bug (mirror case) | **dismiss** via REVEAL-ERROR-RECOVERY (iii, noise). The sub-families "clean" (no error anywhere; 59+ mypy, 2 ty tuning) and "unrelated earlier error" stay live |
| reveal different 552 / uncomparable 476 / ty_more_precise 178 | no bug where it matches pyright and its own mdtest | no verdict possible as a class; 98 % / 94 % of the rows carry an origin-expectation comment, so a rule would be circular | **live**. Only fixable part was the normaliser (rows 1 and 6 of 4.1) |
| pattern 3 sub-case: bytes literal spelling | no bug | no bug | harness defect fixed in typenorm |
| only_mypy [assignment] 370 (function-local redefinition with a new type) | no bug (matches pyright; documented declared-type / inferred-union model) | DESIGN_DIVERGENCE (docs: one declared type per name; vanishes with `--allow-redefinition`) | **dismiss** the undeclared-name, pyright-silent subset via MYPY-FIRST-ASSIGNMENT-TYPE. Declared-name groups and the 52+ pyright-agrees rows stay live (candidate ty FALSE_NEGATIVE) |
| only_mypy [assign] shape: mypy flags `b = 1` where `b: A` and `A` is defined later | correct (NameError at runtime; its silence follows from its own unresolved-reference) | KNOWN_LIMITATION (python/mypy#948, UPSTREAM-MYPY-948) | no new rule: only 25 tuning / 4 hold-out rows |
| only_mypy [assert-type] 228 / only_ty [type-assertion-failure] 185: literal retention in inferred TypeVar solutions | DESIGN_DIVERGENCE (spec literal.rst leaves it open) | DESIGN_DIVERGENCE where it widens | **dismiss** only the one-sided literal subset (ASSERT-TYPE-LITERAL-RETENTION), after the bool-literal and pyright hardening. Narrowing differences (`Literal[10,20,30]` vs `Literal[10,30]`) stay live |
| assert_type tuple-comparison rows from pyright's own suite (about 197 / 157) | no bug evidence (matches the suite) | DESIGN_DIVERGENCE (typeshed `tuple.__lt__ -> bool`) | **live** (version skew: the installed pyright fails the same assertion). ORIGIN-MISMATCH hint for these rows is a next step |
| ty `Literal[False]` vs `bool` on a tuple subclass overriding `__lt__` | **INCORRECT_INFERENCE candidate** (constant folding; CPython True) | silent is correct | kept visible; never dismissed (must_stay_live) |
| only_ty [unresolved-reference] 154 | correct (CPython NameError, pyright agrees) | FALSE_NEGATIVE for 145 of 163 mypy-silent rows (annotation-only reads, forward references in bases / bodies / decorators); KNOWN_LIMITATION default-off for 18 (opt-in `possibly-undefined` finds them) | **live**; hint-only entry added for the 18; ANNOTATION-ONLY-READ (python/mypy#15416, #17373, #4019, #11342) keeps dismissing the annotation-only read with `runtime_override=False` |
| ty reveals through an alias of a condition (ty_more_precise) | correct, more precise (pyright agrees) | KNOWN_LIMITATION (python/mypy#13807) | **dismiss** the unchanged-alias form via MYPY-13807-ALIASED-CONDITIONS; stale or non-matching variants stay live |
| only_mypy [arg-type] 118, concern_mismatch [assignment] 114, only_ty [invalid-assignment] 94, [invalid-argument-type] 86 | correct where pyright agrees | FALSE_NEGATIVE candidates where pyright agrees; not investigated (not bug hunting) | **live**, no rule: a rule would hide ty false negatives that pyright also reports |
| runtime_miss `'NoneType' object is not callable` (19 rows, 8 with a stub-bodied callee) and `type 'X' is not subscriptable` (6 + 3) | not examined | not examined | **live**: closing them would dismiss rows that carry CPython crash evidence |
| mypy class-base forward reference (`class C(B)` before `class B`) | correct (flags it, like pyright; CPython NameError) | FALSE_NEGATIVE candidate (mypy test-suite program may rely on this on purpose) | candidate kept live, copied to [run output] |

---

## 5. Pipeline weaknesses and recommended next improvements

### 5.1 False dismissals (the pipeline was wrong)

Found by the reviewer or by my own audits, all fixed in this run:

1. **Constant-fold hole** in ASSERT-TYPE-LITERAL-RETENTION: 62 tuning dismissals were `Literal[True/False]` vs `bool`, i.e. ty evaluating a comparison, not retaining a written literal. The tuple-subclass program shows a runtime value contradicting the fold. The same hole existed in INFERENCE-DOWNSTREAM through its probe-literal branch (10 more findings). Fixed (row 4).
2. **Entry text contradicting the matcher**: the assert-type docstring said the other tool is silent, but pyright was never consulted; 75 of 130 dismissals had a pyright diagnostic. Fixed (row 4).
3. **Stale alias**: `is_none = a.x is None; a.clear(); if not is_none: reveal_type(a.x)` was dismissed. Fixed (row 9), 2 tuning findings re-opened.
4. **Dismissal on a statement with a CPython exception**: `reveal_type(super())` (RuntimeError). Fixed (row 8).
5. **ANNOTATION-ONLY-READ dismisses runtime-crash evidence**: `runtime_override=False` means 100 of its dismissals sit on programs where CPython raised a NameError / UnboundLocalError. Reviewed in round 2 and left in place as a tracked mypy limitation (python/mypy#15416 and others); policy for NameError evidence was decided by the user in round 3 (strong evidence, no dismissal change). It is still the single largest "blind" closing rule for runtime crashes.

Not fixed (reviewer round 3, `approved=false`; none was a confirmed false dismissal):

6. **REVEAL-ERROR-RECOVERY binding clause has no causality check** (`_error_at_binding_of_reveal_arg` accepts any ERROR diagnostic on an earlier statement binding a name read in the reveal). No false dismissal found in the 76 new ones (30 audited). Recommended: a negative test where the earlier error is unrelated to the binding's type, or restrict to error codes that produce a recovery type.
7. **Chained dismissals**: some of the 76 are closed because ty flagged a binding whose error is itself dismissed by ANNOTATION-ONLY-READ (e.g. testNarrowingFromObjectToOptional D2, testSelfTypeGenericClassNoClashInstanceMethod D3). Record the chain in the finding notes.
8. **`attach_runtime_evidence` NameError branch** records strong bug evidence with `blame='unknown'` when both tools have diagnostics on the row. Add a test, or do not emit strong evidence without a blamed tool.
9. **`kbloop_sample.py` cannot list dismissed findings** (it skips `tier == dismissed`), so every audit of a dismissal rule needed a custom script ([campaign working file], r2_audit.py, r3_audit.py). Add `--dismissed-by ENTRY`.

### 5.2 Invisible bugs (the ty-vs-mypy diff cannot see them)

- Calibration (194 maintainer-labelled open reports; ty 123, mypy 71): **61 are invisible** to the differential (ty 30, mypy 31), 117 are kept, 11 are dismissed by pre-existing entries and 5 are excluded. A differential cannot see a bug that both tools share. This is a property of the method, not a regression; it did not change in this run.
- Findings where **both tools agree and both are wrong** never appear. BOTH-GRADUAL closes 458 findings on the assumption that two gradual answers are equivalent.
- Dismissals by pre-existing entries that hide real bugs in calibration: mypy-4554, 5289, 6079, 7984; ty-1090, 1172, 4713, 4786, 4817, 4835, 4872 (11 positives). These are known and unchanged.
- **Candidate ty false negatives hidden inside the queue**: the 52+ only_mypy [assignment] rows where pyright agrees with mypy. They are live but unexamined.
- **A silent tool is not always visible as a discrepancy**: `reveal_type(Later)` before `class Later` makes ty reveal `Unknown` with no diagnostic while CPython raises NameError. The row appears only because mypy reveals the class.

### 5.3 Noisy rules and measurement problems

- **Origin-expectation programs dominate the queue.** 85-95 % of reveal-mismatch rows come from harvested ty mdtests, mypy test-suite cases or pyright samples that exist to show one tool's inference. 98 % (558) of pattern "different" and 94 % (444) of "uncomparable" carry an expectation comment. The existing ORIGIN-ORACLE hints are circular ("the origin tool says so") and cannot close anything.
- **Version skew**: pyright-suite assert_type expectations are not reproduced by the installed pyright 1.1.414, so ty and mypy disagree on rows where the origin tool fails too.
- **Tuning-set bias**: entries designed from tuning samples hit hold-out at a lower rate (round 1: 5.40 % vs 2.01 %). The gap was 1.8 points at the end.
- **The 50 % target looks unreachable with oracle-backed rules on this corpus.** Three rounds of supported rules removed 7.5 % of the tuning queue; each round removed less than the one before (4.73 %, 1.59 %, 1.01 % of the overall queue). The reviewer asked for a user decision: keep the target, restate it, or stop with documented pivot options. The log records no such decision.
- **`calibrate --no-pyright`** cannot exercise entries that need pyright (ANNOTATION-ONLY-READ); five negatives stay "open" for that reason or older ones: kb-ANNOTATION-ONLY-READ, kb-JOIN-VS-UNION-CALLABLE, kb-MDTEST-TODO, kb-MYPY-15182-NEW-RETURNS, neg-generic_isinstance. The negatives metric also cannot hold programs that must stay live; `calibration/must_stay_live/` and the new `--must-stay-live` option fix that.
- **Stale numbers in documentation**: the internal plan prose (4,849 programs, 27 seeds / 16 with findings, "pyright" unpinned) and the README calibration baseline (ty 0/80, mypy 4/76 on an older issue set; same code today gives ty 7/123, mypy 4/71) do not match the current corpus. `docs/kb-loop-split` is for the older 6089-program corpus.
- **Shell tooling**: the permission layer rejected a bash-style `source` activation in fish, and command output arrived late or empty in several sessions. Every result was written to a file and read back.
- **Process loss**: the first corpus run died at 2850/5129 when its host call ended. The runner is resumable and nothing was lost, but the run should be detached from the start.

### 5.4 Recommended next improvements, ranked

1. Decide the target: keep >50 % (needs a fundamentally different oracle), restate it, or stop here.
2. Per-construct reasons for the "clean" gradual rows (59+ mypy `Any`, unannotated parameters, dynamic `type()` namespaces).
3. Hint-only ORIGIN-MISMATCH for assert_type rows where the origin tool also fails them (about 60 rows; zero queue effect, useful for judging).
4. Reveal-level first-assignment entry (96 tuning reveal rows behind a dismissed first-assignment, 1-3 in hold-out; widens the tuning/hold-out gap; `--allow-redefinition` alone does not close them because `finally` blocks still differ).
5. Fix the open reviewer items 6-9 above.
6. Check the 145 true mypy unbound false negatives in the playground and decide whether to file after duplicate checks.
7. Re-run `typediff calibrate` with pyright on the final versions (needed for §8 'Calibration').

---

## 6. Candidates and incidental findings

**No genuinely new, confirmed bug was found.** This was not a bug hunt. Everything below is INCIDENTAL, unverified in the playground, **not filed and not drafted**.

### 6.1 Copied to [run output] (git-ignored, regenerable from seeds/harvested)

| File | Source | Observation | Confidence |
|---|---|---|---|
| [run output] | mypy-suite case testForwardBaseDeferAttr | `class C(B)` with `B` defined later: CPython NameError; ty and pyright flag it; mypy silent. Possible mypy FALSE_NEGATIVE. Duplicate check by body-text search found nothing. The mypy suite relies on forward bases deliberately, so it may be accepted behaviour | low |
| [run output] | pyright sample typeIs11 line 20 | after `assert type(value) == type(sample)` with `value: Any`, ty's assert_type reports `Any` where pyright and mypy answer the sample's type. Possible ty INCORRECT_INFERENCE in a narrowing construct. Not investigated | low |

### 6.2 Recorded in the log, kept as calibration data or notes

**ty constant folding on a tuple subclass (INCIDENTAL, strongest of the set).** Reproducer: `calibration/must_stay_live/ty_constant_fold_tuple_subclass.py` (the same program was first run as [temp file]).

```python
class Restricted(tuple[Literal[1]]):
    def __lt__(self, other: tuple[Literal[1], ...], /) -> bool: return True
r = Restricted((1,)) < (1,)
print(r)
assert_type(r, bool)
```

| Checker | Output |
|---|---|
| mypy 2.4.0 | silent |
| ty 0.0.84 | `error[type-assertion-failure]`: type `Literal[False]` does not match asserted type `bool` |
| pyright 1.1.414 | 0 errors |
| CPython 3.13 | prints `True` |

Duplicate check (read-only): `gh search issues` on astral-sh/ty for "tuple comparison" returned only ty#2140 (closed, `__eq__` narrowing); "constant folding" and "__lt__ tuple subclass" returned nothing; astral-sh/ruff "tuple comparison ty" nothing; python/mypy "assert_type tuple comparison" nothing; microsoft/pyright "tuple comparison" returned #7733, #3864, #7132, all closed and unrelated ([campaign working file]). Verdict: ty INCORRECT_INFERENCE candidate (unsound folding of a comparison, same stance as ty#2140 for `__eq__`); mypy and pyright behave correctly. Confidence: medium that this is a real ty issue (the runtime contradicts the inferred type); low that it is worth a maintainer's time (a deliberately constructed, artificial subclass). UNVERIFIED-PLAYGROUND.

Other notes (not copied to hits):
- ty `reveal_type(Later)` before `class Later` at module level reveals `Unknown` with no diagnostic; CPython raises NameError; mypy reveals the class ([campaign working file]). Possible ty FALSE_NEGATIVE (missing unresolved-reference). Not investigated. Low confidence.
- 145 live mypy-silent only_ty [unresolved-reference] rows where even the opt-in checks do not make mypy report the name (annotation-only reads, forward references in class bases, bodies and decorators). Reproduced on a minimal program: `def f(): x: int; reveal_type(x)` gives ty `unresolved-reference`, pyright "x is unbound", mypy reveals `int`, CPython UnboundLocalError. Duplicates exist: python/mypy#15416, #17373, #4019 (all open) and #11342 (closed as a duplicate of #686). So this is a **known** mypy limitation, not new.

Funnel for candidates: discrepancies 10597 -> review queue 7277 -> candidates 2 in [run output] + 1 log-only constant-fold + 1 log-only `reveal_type(Later)` -> confirmed 0 -> filed 0 -> acknowledged 0.

---

## 7. Not verified

- **Every playground check** (triage checklist item 6): UNVERIFIED-PLAYGROUND for all patterns and all candidates. Reproduction was done only with the pinned local checkers and CPython 3.13, not with mypy-play, the ty playground or the pyright playground, so version- or option-specific behaviour on the latest releases is untested.
- **discuss.python.org**: not searched at all. The spec questions (literal retention, redefinition, narrowing through aliases) were answered from the typing spec text in the cached docs corpus only (literal.rst, directives.rst, special-types.rst, concepts.rst, narrowing.rst) and from the mypy and ty documentation.
- **Duplicate searches** used GitHub search over issue bodies for a handful of phrases per pattern ([campaign working file], [campaign working file]). They were read-only, with no write, and are not exhaustive. A negative result means "no hit for these queries", not "no duplicate".
- **Calibration** was run in an approximated mode (`--no-pyright`-equivalent subset script, 4 chunks, positives fetched on the day). The full `typediff calibrate` with pyright and the `calibration/RESULTS.md` recall on 156 known bugs were not re-run. The pyright version printed nothing for `--version`; the pin is evidenced by pip metadata.
- **All dismissals are audited only by sampling**: 18 random rows per round for the main rules, 30 of 76 for the binding clause, the full set only for the targeted properties (CPython exception on the statement: none; toggle passed: all 182 first-assignment dismissals).
- **The reviewer never approved.** All three reviewer verdicts are `approved=false`; the loop ended at the 3-round limit. Reviewer items 6-9 of section 5.1 are open.
- **Hold-out is not truly independent**: its entries were designed after reading tuning samples, and 13 programs now in tuning were in the teammate's older hold-out.
- The `-l` stray file and `findings/2026-10-27-llm-run/` were left untouched and uncommitted. `runs/`, `seeds/harvested` and `calibration/positives.json` are git-ignored; the numbers in this report can be reproduced from them with the commands in section 1.
- GitHub: only read-only API calls (search, issue fetch, REST list of issues for positives, no authentication in the calibration fetch). Nothing was pushed, filed, commented or modified.

---

## Final summary

Branch: [campaign working file] (local, not pushed).

| Review queue | Baseline | Final | Shrink |
|---|---|---|---|
| Overall | 7841 | 7277 | 7.19 % |
| Tuning | 6300 | 5825 | 7.54 % |
| Hold-out | 1541 | 1452 | 5.78 % |

Target (> 50 %): not met on either set.

Commit list (`git log --oneline main..campaign/day2-p1`, oldest at the bottom; the last commit adds this list to the report):

```
4055e85 docs: day-2 P1 final run report
5c4a525 chore: add remaining [campaign working file] helper scripts and probe outputs
1e860b7 docs: add reviewer verdicts and review docs for rounds 1-3, round-1 run markers
528bd1a docs: log stage 3 round 3 ...
d924841 feat: REVEAL-ERROR-RECOVERY also covers a gradual reveal through a name the same tool flagged at its binding
a4147b3 fix: NameError on a flagged name is strong evidence in both code paths ...
10dd9b1 fix: stale-alias guard for MYPY-13807, pyright-independent REVEAL-ERROR-RECOVERY negative, ...
13aae01 docs: log stage 3 round 2 ...
69f5ff6 fix: REVEAL-ERROR-RECOVERY never dismisses a statement CPython raised on (any exception type)
ba8fbe0 feat: MYPY-13807-ALIASED-CONDITIONS KB entry
1b708d4 fix: typenorm treats intersections, LiteralString, type[X] and Never as refinements
9456642 feat: REVEAL-ERROR-RECOVERY KB entry
c1d243b fix: close the constant-fold hole in assert_type retention, require pyright agreement, ...
d479c03 docs: log stage 3 round 1 ...
0cd8539 docs: cite the conformance suite's 'either is acceptable' note in ASSERT-TYPE-LITERAL-RETENTION
fbf9b12 feat: KB entries for assert_type literal retention and mypy first-assignment typing; ...
d171b92 fix: normalise bytes literal spelling and add literal-retention helper in typenorm
b4bf9e8 docs: log stage 2 corpus run and split baselines
7f2969d chore: stage 1 setup and day 1 run log
```

Report path: `results/days/day2-report.md`
