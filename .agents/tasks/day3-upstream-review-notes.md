# Day 3 upstream entries: reviewer notes, pass 2 (head 4c3f4cc, branch campaign/day3-p2)

Verdict: **approved = true**. The blocking E6/TY-4899 item from pass 1 is fixed; four non-blocking items remain.

## Pass-1 items, status
- Blocking, E6 not closed on this host (`ty:signal-SIGKILL`): fixed. TY-4899 now accepts SIGKILL, the
  `paramspec_self_callable_init` shape gate is unchanged, and the new tests show no other ty entry accepts SIGKILL and
  control E3 stays unmatched. In my seeds run E10 came out as SIGKILL and E1/E2/E6 as `ty:timeout` under 3 parallel jobs;
  all five close with TY-4899, so the entry no longer depends on host memory.
- PYRIGHT-11961 regex: now exactly `pyright:internal:RangeError`; bare `pyright:internal` has a negative test.
- `stance: open` removed from the closed crash entries TY-4883 and PYRIGHT-11960.
- TY-3765 prior statement regex tightened; a test confirms `x: int | None` no longer gets the note.
- MYPY-21937 chain exhaustiveness: documented as a known limit in the note (accepted, non-blocking).

## Gates I re-ran
- `pytest tests -q`: 355 passed (baseline 201).
- `typediff --python-version 3.13 kb-selftest`: 20 PASS, no FAIL.
- `scripts/upstream_day3_check.py --jobs 3` (each reproducer and control through the real pipeline,
  fresh `--out` per file, `TYPEDIFF_LLM=null`): `violations: 0`. Reproducers close with the right id; D1/D7/D10/D11 close
  with TY-4900 for ty and MYPY-22360 for mypy; controls C4/C5/C6, E4/E5/E7/E9, B3/B5/B6, D4/D8, A3/A8/A10 produce no
  crash finding; ty overflow on A1/A4, mypy A7, pyright A9 and the mypy_B hang stay `confirmed`; mypy_B is not claimed by
  MYPY-22343. Discrepancy probes: bug-04 stays at REVIEW (MYPY-19889 is a prior only); probe-bug01 attribute and
  variable-index controls produce no discrepancy and `del` (D4) stays at REVIEW; probe-bug03 Final/method/Plain/Producer
  controls are not dismissed.
- Replay scan of `runs/day2/out3` (5086 reports, 10 crashes): `match_crash` on each gives exactly the report's 4 closures
  (seed-6ec46aeec17d and seed-7eb92c7ac931 TY-4883, seed-d088506c023d TY-4882, seed-fe4d8323a2d7 MYPY-22344); the other 6
  crashes stay live; no SIGKILL or pyright crash exists in that corpus, so the pass-2 changes cannot alter the replay.

## Matcher breadth
Read every crash `requires` function and the five discrepancy `requires` functions in kb.py. Crash entries are
tool-keyed, fully anchored on the signature, and require an AST shape, so the same program closes TY-4900 for ty and
MYPY-22360 for mypy and never the reverse. Nothing in the pass-2 diff widens a matcher except the intended SIGKILL
alternative. The kind-crash extension is small and gated on `symptom == CRASH` plus a loader skip in `kb.py`; existing
discrepancy and `abnormal_exit` findings take the old path. The only behaviour change for existing findings is that
two already-dismissed ones (probe-bug06 D3, bug-02-ty-flag-or-assert-type D1) now carry a TY-876 duplicate reason instead
of a design-divergence reason; both stay dismissed and the report lists it.

## Categories, statuses, URLs (GitHub read-only, `gh api`)
ty#4882/4898/4899/4900/876, mypy#22343/22344/22360/22361/22339/20969/21937/19889 and pyright#11961/11851/11859 open
(mypy#21937 reopened); ty#4883, ty#4884, pyright#11960 closed completed; ty#3765 closed duplicate; ty#4656 closed
not_planned and not duplicated. Fixed-after-pin issues remain entries with the fix reference in the note; priors are
MYPY-19889 and TY-3765 only; pyright#11851/#11859 are reported as not representable with the reason.

## Non-blocking
1. The report is stale in three spots after iteration 2 (PYRIGHT-11961 regex in the table, TY-3765 statement
   description, and the bullet saying `stance: open` was left on closed crash entries).
2. An empty untracked file `-l` sits in the repo root; delete before merging.
3. MYPY-21937 does not check chain exhaustiveness (documented).
4. The Day-2 replay was not re-run after iteration 2; my scan shows no effect.
