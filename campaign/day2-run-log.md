# Day-2 P1 run log (append-only)

Format: `[Plan §<section> / <phase or day> / <named step>] what, command, result`. Venv binaries are called by absolute path (fish; no activate). `TYPEDIFF_LLM=null` throughout, 0 LLM calls.

[Plan §3 / branch setup / create branch] Created local branch off main. `git checkout -b campaign/day2-p1 main`. OK. Untracked `-l` and `findings/2026-10-27-llm-run/` left alone.

[OFF-PLAN, tooling] First version-check command (sourced bash-style venv activation in fish) was rejected by the user's permission layer; parent session said to call venv binaries by absolute path instead. Done from here on. No pipeline change.

[Plan §4 Setup / P0 / verify versions] `.venv/bin/python --version; .venv/bin/python -m pip list`. Result: Python 3.13.16, ty 0.0.84, mypy 2.4.0, pyright 1.1.400 (WRONG pin), typing_extensions 4.16.0, pytest 8.3.5, typediff 0.1.0 editable from repo (importable, no reinstall needed).

[Plan §4 Setup / P0 / pin pyright] KNOWN ISSUE: DESIGN.md/calibration pin pyright 1.1.414. `.venv/bin/python -m pip install pyright==1.1.414` (output campaign/pip-pyright.txt). Result: pip list now shows pyright 1.1.414. Final versions: Python 3.13.16, ty 0.0.84, mypy 2.4.0, pyright 1.1.414. (`pyright --version` printed nothing to the captured output; the pip metadata is the evidence.)

[Plan §4 Setup / P0 / fetch docs] `typediff fetch-docs > campaign/s1-fetch-docs.txt`. Exit 0. All sources "ok"; corpus: 862 chunks in ~/.cache/typediff/docs.

[Plan §4 Setup / P0 / KB self-test] `typediff --python-version 3.13 kb-selftest > campaign/s1-kb-selftest.txt`. Exit 0. 11 lines, 11 PASS, 0 non-PASS.

[Plan §4 Setup / P0 / pytest baseline] `.venv/bin/python -m pytest tests -q > campaign/s1-pytest.txt`. Result: 144 passed in 29.89s, 0 failed.

[Plan §3 Day 1 / P0 / check known_upstream.json] Read `typediff/data/known_upstream.json`. entries (dismiss as DUPLICATE/DESIGN_DIVERGENCE): TY-1090 (open), TY-4212 (intended), TY-2255 (open), MYPY-9658 (open), MYPY-948 (open). prior_stances (never dismiss, only cap at REVIEW): TY-4656 (intended), TY-4152 (open), TY-4673 (open), TY-1172 (open). Id/url list in campaign/s1-upstream-ids.txt. Nothing added in Stage 1.

[Plan §3 Day 1 / P1 / hand seeds] `typediff --python-version 3.13 seeds seeds/ > campaign/s1-seeds-run.txt` (TYPEDIFF_LLM=null). Result: "done: 29 programs, 0 LLM calls". Counted from the per-program lines with campaign/s1-count.py: 35 discrepancies, 25 live (review-queue) findings, 14 of 29 programs with live findings, 0 crash lines. (Plan §1 text says 27 seeds/16 with findings; the seed set now has 29, so numbers differ from the plan prose.)

[Plan §3 Day 1 / P1 / harvest] `.venv/bin/python scripts/harvest_seeds.py > campaign/s1-harvest.txt`. Exit 0. Kept per source: conformance 136 of 145; ty mdtests 2682 of 3575; mypy 1210 of 1770; pyright 1045 of 1446; typeshed 56 of 74. Total 5129 files in seeds/harvested (verified with find; also per-area folders, gradual_any largest at 2544). ty mdtests skipped by env: python-platform 60, 3.10 197, 3.11 251, 3.12 803, 3.14 138, 3.15 28, 3.8 1, 3.9 28. Differences from the plan's 4,849 (130/3,509/1,210): the script now also harvests pyright and typeshed and filters ty mdtests by python-version; plan §1 numbers are stale.
