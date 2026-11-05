# Day 6 run log (Part A: verification)

Branch `campaign/day5-p2`, local only. Plan step followed: Part A of the Day 6 task (A1 verify drafts 3 and 4, A2 verify the `adbc14c6128a` Callback candidate, A3 update drafts and write `day6-verification.md`). Drafts 1 and 2 skipped on the user's word (verified on the ty playground).
This was the first iteration: `.agents/tasks/partA-review.json` did not exist (the directory lists only the earlier `day3` to `day5` review files).

Shell note: fish garbles stdout, so every command ran as `bash script.sh > out.txt 2>&1` and the output was read from the file. Scripts and raw outputs were first in `/tmp/d6/`, then copied to `campaign/day6/{repro,evidence}/`.

## Steps

1. Read `day3-issue-drafts.md`, `day5-ty97-bump.md`, `day5-report.md`. Note: the drafts file numbers the mypy metaclass bug as draft 3 and the ty Hashable bug as draft 4 (the task text has them the other way round); the file's numbering is used.
2. Versions (`evidence/00-versions.txt`): ty 0.0.97, mypy 2.4.0, pyright 1.1.414, `/tmp/d3v-latest` mypy 2.4.1, `/tmp/d3v-master` mypy 2.5.0+dev.879da562 (matches GitHub master HEAD sha 879da562, 2026-11-05T00:40:27Z), CPython 3.13.16. Latest ty release is 0.0.97 (no newer venv needed); latest mypy tag is v2.4.1; pyright on PyPI is 1.1.414 (`evidence/01-latest-versions.txt`).
3. Draft 4 (ty Hashable): reran `hash_bug.py`, controls `hash_ctrl.py`, `hash_extra.py` on CPython, ty 0.0.97, mypy x3, pyright (`evidence/10-`); ty 0.0.84 also run. Still accepted by ty; CPython raises. Duplicate search: ty issues and ruff PRs (8 phrases each, then 9 more phrases and title searches), read ty#4157, #4196, #3781, #4748, #4754 and ruff#27441, #29471, #26039, #26040, #26367. Two PR queries hit the GitHub search rate limit (HTTP 403) and were re-run after a 60 s sleep. No duplicate; ruff#26040 (closed, unmerged) names the case for union simplification only.
4. Draft 3 (mypy metaclass): reran `meta_bug.py` and `meta_ctrl.py` on all tools (`evidence/20-`). Same 2 errors on mypy 2.4.0, 2.4.1 and master. Instrumented `covers_at_runtime` on master (`probe_covers.py`): `False` for the class-object operands, `True` for the instance control (`evidence/21-`). Duplicate search: 25+ phrases on python/mypy issues and PRs plus 8 title searches; two 403 rate-limit failures were re-run. No duplicate.
5. Callback candidate: found the program under `runs/day5/gen/typevartuple_unpack/`; reduced to `class Callback[*Ts, **P = [bool]]: ...`; ran 11 variants on all tools (`evidence/30-`). Bisected ty 0.0.84 to 0.0.97 with `uvx --from ty==0.0.NN` (`evidence/33-`): flagged up to 0.0.93, silent from 0.0.94. Release notes for 0.0.94 point to ruff#29753; PR text says defaulted ParamSpecs are allowed on purpose (`evidence/34-`). Fetched the typing spec and PEP 696 sections: a defaulted ParamSpec may follow a TypeVarTuple. Runtime probe on CPython 3.13.16, 3.14.8 and 3.15.0: all raise `TypeError` for spec-valid classes (`evidence/31-`). Found python/typing#2211 (acknowledged runtime bug). mypy rejects the spec's own example at the subscript (`evidence/31-`, `32-`); public conformance results list the same failure; no mypy issue found.
6. Verdicts: draft 3 STILL-BUG-NEW; draft 4 STILL-BUG-NEW; Callback: ty NOT-A-BUG, CPython DUPLICATE (python/typing#2211), mypy STILL-BUG-NEW.
7. Updated `day3-issue-drafts.md` (header, table column, notes on drafts 1 to 4, new draft 5, "Not drafted" bullet), wrote `day6-verification.md`.
8. Committed locally on `campaign/day5-p2` in two commits (see `git log`). Nothing pushed.

## Not done / open

- ty `main` and the playgrounds were not used (placeholders `<PLAYGROUND LINK>` remain in drafts 3, 4, 5).
- No KB entry was added for the Callback finding (triage owner's decision).
