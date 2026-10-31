# kb-loop handoff (newest entry on top)

## Entry 2: Round 1, after calibration + narrowing (all code committed except scripts/kbloop_calib_subset.py, committed with this entry)

### State
- Commits on kb-loop (not pushed): c324ac6 handoff+replay, 42e5b45 spec-narrowing exclusion, then "suite-header requirement for origin oracle and MYPY-948". pytest 22 targeted tests pass after narrowing; full suite was 118 passed before the last narrowing (re-run before finishing); kb-selftest: all PASS.
- Round-1 baseline (runs/round1/out): live 9908 (tuning 7939, hold-out 1969).
- First re-adjudication (runs/round2/out, before narrowing): live 8694 (tuning 6953, hold-out 1741) = -12.3% / -12.4% / -11.6%. ORIGIN-ORACLE-REVEAL dismissed 1025, UPSTREAM-MYPY-948 184, SUITE-ALLOW-EMPTY-BODIES 11. Replay equals a full checker re-run on a random 100 (100/100 identical).
- Final re-adjudication with narrowed entries: runs/round2b/out (6044 reports written; the verify-sample line in /tmp/kbloop/replay2.log was still pending). Numbers: run `python scripts/kbloop_stats.py runs/round2b/out --json runs/round2b/stats.json`.

### Calibration (positives were fetched: 211 cases; baseline file had 166 rows)
- First pass (typediff_out/calibration/calibration_rows.jsonl) showed NEW dismissals of known real bugs caused by this round: ty#4841 (ORIGIN-ORACLE-REVEAL treated the reporter's own `# revealed:` comment as suite expectation) and mypy#7935 (UPSTREAM-MYPY-948 hid the real bug behind a forward-reference artefact).
- Fix (committed): both entries now require the harvester header (`# origin: ruff mdtest` / `# origin: python/mypy`). Tests added. NOT YET CONFIRMED by re-run.
- Other newly dismissed positives, from entries that predate this round, not yet checked against baseline code: ty#4872 (rule:undefined-name), ty#4835 (BOTH-GRADUAL), ty#4817 and ty#4713 (MYPY-OPTIONAL-CHECK), ty#4786 (LITERAL-WIDENING). ty#1172 and ty#1090 were "kept" in the old baseline but are dismissed by the old TY-SELF-UPPER-BOUND / UPSTREAM-TY-1090 entries (which exist because of those very issues).
- Baseline-code check: baseline source extracted to /tmp/kbloop/basesrc (git archive 0f1d39b typediff). Run: `cd .worktrees/kb-loop; PYTHONPATH=/tmp/kbloop/basesrc python /tmp/kbloop/basesrc/kbloop_calib_subset.py /tmp/kbloop/calbase ty-4872 ty-4835 ty-4817 ty-4786 ty-4713` (verify with `python -c "import typediff;print(typediff.__file__)"` under that PYTHONPATH that the baseline package is loaded).

### Next steps
1. Confirm replay2 finished (`tail /tmp/kbloop/replay2.log`), run stats for round2b.
2. `python scripts/kbloop_calib_subset.py /tmp/kbloop/calnew ty-4841 mypy-7935 ty-4872 ty-4835 ty-4817 ty-4786 ty-4713` (current code) and the baseline-code run above; both need to not newly dismiss ty-4841/mypy-7935.
3. Write docs/kb-loop-log.md round-1 section and docs/kb-loop-candidates.md (candidate bugs, ranked round-2 list), run full pytest + kb-selftest, commit, send_message success saying round 1 is complete.

## Entry 1: Round 1, mid-way (after commit "feat: origin oracle, MYPY-948 and suite-empty-bodies KB entries ...")

### 1. DONE so far
- Round determination: `.agents/tasks/kbloop-review.json` did not exist, so this is ROUND 1. User decision: do exactly ONE round, then finish. Round 2 is only a ranked list in `docs/kb-loop-candidates.md` (NOT yet written).
- Corpus: 6089 programs (29 hand seeds + 6060 harvested), full corpus, no sampling. 6044 ran, 45 rejected by preflight (non-stdlib imports etc.), 0 timeouts/errors. Wall time 4010 s with 14 jobs.
- Driver scripts (committed): `scripts/kbloop_run.py` (parallel, resumable), `scripts/kbloop_split.py` (hold-out), `scripts/kbloop_stats.py`, `scripts/kbloop_patterns.py`, `scripts/kbloop_sample.py`, `scripts/kbloop_replay.py` (re-adjudicate from saved reports, `--rerun-runtime`, `--verify-sample 100`).
- Hold-out: fixed-seed stratified 20% (1218 programs) in `docs/kb-loop-split/holdout.txt`; tuning set 4871 in `tuning.txt`. KB entries were written only from tuning-set samples.
- BASELINE numbers (round1/out, before any KB change): all: programs 6044, discrepancies 13096, live 9908, dismissed 3213. Tuning: programs 4837, live 7939, dismissed 2537. Hold-out: programs 1207, live 1969, dismissed 676. Tool crashes: 25 (ty timeouts 4+, mypy timeouts 3, abnormal exits 9...).
- Code changes (all committed on kb-loop): `typediff/origin.py` (origin oracle), `typediff/replay.py`, KB entries ORIGIN-ORACLE-REVEAL (auto), ORIGIN-ORACLE-NOTE (hint), ORIGIN-MISMATCH (hint), MYPY-SUITE-ALLOW-EMPTY-BODIES (auto, verify toggle `--allow-empty-bodies`), UPSTREAM-MYPY-948 (known_upstream.json + `unquoted_forward_ref` matcher); `triage --only/--exclude`.
- Pipeline defects found and fixed (with regression tests):
  - D1 variadic `tuple[A, *tuple[B, ...], C]` treated positionally by `inhabit.py` -> false strong "does NOT inhabit" evidence.
  - D2 typing aliases/special forms (Hashable, Mapping, C[int]) probed as instances vs `type[...]` -> false strong evidence.
  - D3 `_stub_callee` ignored operators/subscripts that call stub-bodied dunders (`A() + B()` -> None) -> false strong evidence.
  - D4 subclass of a TypedDict counted as nominal class (`state.py`) -> false "dict outside TD2".
  - D5 `TYPE_CHECKING` probed as an operand (False at runtime by definition).
  - D6 runtime harness `compile()` inherited the harness's own `from __future__ import annotations`, so CPython "succeeded" on unquoted forward references that raise NameError on 3.13 (fix: `dont_inherit=True`). Needs the CPython result re-run for the corpus (done via `--rerun-runtime`).
  - (not fixed, listed for candidates) mypy-origin programs are checked without the suite's defaults (allow_empty_bodies); pyright-only `reveal_type(x, expected_text=...)` kwargs; ~300 ty-origin ORIGIN-MISMATCH reveal cases (version skew / mdtest python-version not honoured).
- Tests: `python -m pytest tests -q` = 118 passed (before the last scripts edit). `typediff --python-version 3.13 kb-selftest` = all PASS (10 entries with examples).

### 2. IN PROGRESS
Replay of the whole round-1 corpus into `runs/round2/out` (log `/tmp/kbloop/replay.log`, started with
`cd .worktrees/kb-loop; source /tmp/kbloop/venv/bin/activate; export TYPEDIFF_LLM=null; python scripts/kbloop_replay.py runs/round1/out runs/round2/out --jobs 14 --rerun-runtime --verify-sample 100`).
Next 3 steps:
1. When the log says `verify-sample: 100/100 identical`, run `python scripts/kbloop_stats.py runs/round2/out --json runs/round2/stats.json` and compare with `runs/round1/stats.json` (tuning vs hold-out).
2. Calibration safety check: `calibration/positives.json` is NOT cached; try `typediff --python-version 3.13 --no-pyright calibrate --fetch --timeout 30` (network), else run the negatives only and compare to `calibration/results/calibration_rows.jsonl`. Record in the log; any positive newly dismissed => narrow/remove the responsible entry.
3. Write `docs/kb-loop-log.md` round-1 section, `docs/kb-loop-candidates.md` (candidate bugs + ranked round-2 list), run pytest + kb-selftest, commit, send_message success.

### 3. DECISIONS
- Origin oracle dismisses only reveal diffs where the origin tool matches its suite's comment, the other tool differs, relation is `gradual` with the other tool less precise (or a precision relation where the origin side is the more precise); never different/uncomparable; runtime_override on. Source: typing spec concepts (Any) + the suite's own expectation.
- UPSTREAM-MYPY-948: I read https://github.com/python/mypy/issues/948 (open; labels feature, topic-quoted-annotations) and #3088 (closed as duplicate of #948). Docs read: https://mypy.readthedocs.io/en/stable/runtime_troubles.html (forward references).
- MYPY-SUITE-ALLOW-EMPTY-BODIES: evidence read: mypy v2.4.0 `mypy/test/testcheck.py` line 166 (`options.allow_empty_bodies = not testcase.name.endswith("_no_empty")`) and https://mypy.readthedocs.io/en/stable/error_code_list.html (empty-body). Only ONLY_MYPY kind (concern_mismatch cannot be verified by the toggle).
- Deliberately NOT done: assert_type mismatch patterns (415 findings, need a pyright-majority view), pyright `expected_text` (59), mypy `tuple[()]` augmented assignment, mypy-vs-ty `no-redef`, `valid-type` patterns: no readable upstream issue/doc yet.

### 4. OPEN ISSUES
- Reveal `different` (645) and `uncomparable` (401) with ty-origin matching: not dismissed, only explained by ORIGIN-ORACLE-NOTE.
- ty `Unknown` where mypy's suite blessed a concrete type is dismissed as imprecision (gradual); round 2 should review these as completeness candidates.
- Candidate bug repros: see `docs/kb-loop-candidates.md` (to be written).

### 5. HOW TO RESUME
1. `cd /home/micropp/Documents/kiro_sa/.worktrees/kb-loop; source /tmp/kbloop/venv/bin/activate; export TYPEDIFF_LLM=null` (recreate venv with `uv venv --python 3.13 && pip install -e .` plus mypy 2.4.0, ty 0.0.84, pyright 1.1.414 if missing).
2. `git log --oneline | head` to see the last commit; `runs/round1/out` = baseline reports, `runs/round2/out` = re-adjudicated.
3. Finish steps listed under IN PROGRESS.
4. Redirect every command to a file under /tmp/kbloop/ and read it back (the bash tool often drops stdout).
5. Final message must state "round 1 complete" so the reviewer can gate exit; do not start round 2.
