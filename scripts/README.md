# Scripts

Helpers that are not part of the `typediff` command. Run them from the repository root with the project's virtual
environment active (`pip install -e ".[tools,test]" -c constraints.txt`). Scripts do **not** read `.env`; export the
variables first (`set -a; . ./.env; set +a`) if you need an API key.

## Reproduction

| Script | What it does |
|---|---|
| `reproduce.sh` | One-command check of a fresh checkout: tool versions (`doctor`), the test suite, `kb-selftest`, and the deterministic judge on the seeds. No API key. `SKIP_TESTS=1`, `WITH_REPLAY=1`, `JOBS`, `STRICT_PINS=1`, `WORK` and `PYTHON` change its behaviour; the header of the script lists them and the expected numbers. |
| `replay_day10.sh [WORK_DIR]` | Replays the last generation round (250 programs) from the 250 stored model answers in `examples/replay/day10/`, then judges the programs with no LLM. Default output: `runs/replay-day10/`. |

Details: [docs/reproducibility.md](../docs/reproducibility.md).

## Corpus runs and statistics

| Script | What it does |
|---|---|
| `harvest_seeds.py` | Collects seed programs from the test suites of python/typing (conformance), ruff (ty mdtests), mypy, pyright and typeshed into `seeds/harvested/` (git-ignored). Needs network access and `git` 2.25 or newer; records the commit of every source in `PROVENANCE.json`. `--sources` and `--out` select what to harvest. |
| `kbloop_run.py OUT SEED_DIR... --progress FILE` | Parallel, resumable judge run over seed directories, deterministic stage only (target Python 3.13). One report per program in `OUT`, no shared dataset (so no order-dependent duplicates). `--jobs`, `--timeout`, `--sample N`, `--pyright-only` are the main options. |
| `kbloop_replay.py OLD_OUT NEW_OUT` | Re-judges the saved reports of a finished run with the current KB and rules, without re-running the checkers. `--verify-sample K` re-runs `K` programs fully and asserts that the replay gives identical results. |
| `kbloop_stats.py RUN_DIR` | Counts for a run: programs, discrepancies, auto-closed, live, with the tuning and hold-out split. |
| `kbloop_patterns.py RUN_DIR` | Volume-ranked table of the live patterns, with cheap discriminators. |
| `kbloop_sample.py RUN KIND CODE` | Prints examples of one live pattern. |
| `kbloop_split.py SEEDS OUT` | Fixed-seed 20 % hold-out split of a seed corpus (`docs/kb-loop-split/` holds the split used). KB entries are tuned on the tuning set only. |
| `kbloop_calib_subset.py OUT ID...` | Re-runs selected calibration cases with the current KB. |

## Checks and inputs

| Script | What it does |
|---|---|
| `inbox_check.py DIR` | Accounts for a file-bridge directory: prompts, answers, pending prompts, answers without a prompt. Exit 1 on an orphan or malformed key. |
| `check_hits.py [THRESHOLD] [DIR]` | Validates the parent programs (default `seeds/parents/`): header, area key, compiles, passes the preflight lint, runs under CPython, no near-duplicates above the threshold (default 0.80). |
| `upstream_day3_check.py` | Sends every reproducer and control of `tests/data/upstream_day3/` through the real pipeline and prints which KB entry closed each one. Uses `.venv/bin/typediff`. |
| `public_issues.py` | Downloads public GitHub issues of a repository without an API key and searches them offline (`download`, `search`). Needs network access. |
