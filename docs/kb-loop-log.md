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
