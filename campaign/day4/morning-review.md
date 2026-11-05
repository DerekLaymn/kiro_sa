# Day 4 morning: two upstream entries and eight promoted parents

The morning4 step promoted 8 Day-3 programs into `runs/hits/` as `d4p_*` parents, removed two near-duplicate hits, and added two `known_upstream.json` entries. `TY-4148` is a crash entry for ty's stack overflow on a self-typed `__call__` attribute. `TY-876-ARGTYPE` is a mypy-only `[arg-type]` row for the open Flag item in ty#876. A replay of the 160 saved Day-3 reports shows 48 live findings drop to 43.

Watch for: the two entries are shape matchers with no root-cause check. A different ty stack overflow in a program that also has a self-typed `__call__` attribute and a call would be closed too (possible, author lists it). The ty#876 entry could close a Flag-combination program where ty is silent for another reason (possible, author lists it).

**Verdict**: APPROVED

## High-level view

The parents are well-formed and the bodies are byte-for-byte the Day-3 sources. The two entries are narrow, tested, and verified against live issues. The replay reproduces exactly as claimed, with 5 closed findings and no side effects.

<details>
<summary>Issues (0 blocking)</summary>

No blocking issues. Non-blocking notes are listed under Details.

</details>

<details>
<summary>Details</summary>

## Promoted parents in runs/hits

I ran my own checker (venv python 3.13) over all 49 `.py` files in `runs/hits`. Every file has exactly one `# area:`, `# hypothesis:`, `# origin:` triple in the first three lines, in that order. All 49 area values are in `typediff.strategy.AREAS`, all compile, and `generator.preflight(src, "3.13")` reports no ERROR (only WARNs on older d3p files). For the 8 `d4p_*` files I compared the non-comment code lines with the file named in `# origin:` and all 8 are identical, so bodies are preserved. `runs/hits` has 50 entries because of a git-ignored `__pycache__` directory. `runs/` is ignored, so the parents are not part of the commits, as expected.

Near-duplicates: with the author's `check_hits.py` at 0.70 the pairs are 0.76 (`d4p_metaclass_or_reflected_ror` ~ `d4v_metaclass_reflected_op`, `|` vs `*`), 0.72 (`d3p_enums_literals_intenum_true_aliases_one` ~ `d4p_enums_intenum_true_alias_one`) and 0.70. None reach 0.80, the author's cut-off, and the two dropped files are in `runs/hits-dropped/`. The 0.72 pair is a parent and its own mutant, kept deliberately, so it is a possible redundancy rather than a defect (non-blocking).

## TY-4148 (crash entry)

Matches only when the tool is ty, the signature is exactly `ty:signal-SIGABRT:stack-overflow`, and `call_attr_own_type` holds (a class annotating `__call__` as itself, `Self`, or a union containing either, plus an instance call). The matcher is shared with the existing MYPY-22361 entry. Tests cover the exact issue program, two Day-3 programs, `Self`/`| None` variants, five signature-gate negatives, three shape negatives, and two controls that must stay live: the mutual-pair form and the protocol-flatten overflow (the confirmed NEW ty bug). I read ty#4148 with `gh issue view`: it is OPEN with the exact two-line program. I re-ran ty 0.0.84 on four Day-3 programs plus both controls with `--python-version 3.13`; all four close-candidates overflow the stack and the protocol-flatten control still overflows, which the entry correctly does not match. It cannot close a CPython-crash finding because crash entries look only at the checker's crash, and all four reports have runtime status `success`. No kb-selftest example exists because crash entries build no KB entry (documented in the JSON `_doc`, same as the older crash entries). Note: the shape check is syntactic (author's section 6), so an unrelated ty overflow in a program with this shape would be mis-closed (possible, low probability).

## TY-876-ARGTYPE (only_mypy)

Needs a mypy `[arg-type]` message of the form `has incompatible type "F"; expected "Literal[F.x]"` where F is a Flag/IntFlag class of the program, and a bitwise combination of two F members in the statement (directly or via a variable). New field `demote_on_exception` steps the entry aside when CPython raised a strong type-related exception in the same statement; the test shows the demotion note. kb-selftest has `PASS KB:UPSTREAM-TY-876-ARGTYPE`. I read ty#876: OPEN, with the unchecked item "Handling of `enum.Flag`". I ran ty, mypy and pyright on four variants. Without `assert combined.value == 3` ty reports the error as mypy and pyright do, so no discrepancy exists; with the assert ty is silent (Never after Flag expansion) and mypy and pyright both report. That matches the entry's explanation and confirms the closure is correct for the Day-3 program. Gap (possible, non-blocking): the matcher does not require pyright to agree with mypy, so a mypy-only report with ty and pyright both silent would also close.

## Replay

My run of `scripts/kbloop_replay.py runs/day3/out runs/day4/replay-d3-review --jobs 14 --verify-sample 30` gives: 160 programs, verify-sample 30/30 identical, live 43 (36 programs, crash findings 2), dismissed 25, `kb:UPSTREAM-TY-876-ARGTYPE: 1`, `rule:crash:signal: 16`. This equals the author's final numbers. The diff against `replay-d3-base` shows exactly 5 changed findings: crash C2 of seeds 0032056ba741, 3e7d6fb5688c, 6cb04c1e6fbc, 887c42f07fb0 (confirmed to dismissed DUPLICATE of ty#4148) and D1 of seed-e4277cc03f53 (review to dismissed by TY-876-ARGTYPE). So TY-4148 closes 4 of 48 and TY-876-ARGTYPE closes 1 of 48. My replay differs from the author's replay dir only in the ordering of tool names in one note ("ty, mypy" vs "mypy, ty"), not in any verdict. All five reports have runtime status `success`, and the other crash on each of the 4 programs (mypy C1) was already closed by MYPY-22361, so no different-tool bug was closed. The remaining NEW bugs (protocol-flatten overflow seed-d8c0c3a3b3ad, ty salsa panic seed-c47eb01468dc, mypy metaclass rows) are still live.

## Tests

Recorded: pytest 373 passed, kb-selftest 21 PASS (`campaign/day4-morning.md` section 4, `day4-run-log.md`). Spot-check only: `test_upstream_day4.py`, `test_upstream_day3.py`, `test_stage3_round2.py`, `test_stage3_round3.py` give 211 passed, which includes the must-stay-live calibration tests; `kb-selftest` prints 21 PASS and no other lines.

## Minor, non-blocking

An untracked file named `-l` sits in the repo root (shown by `git status`); it looks like an accidental redirect and should be deleted. It is not part of the morning4 commits.

</details>

<details>
<summary>File map</summary>

`typediff/data/known_upstream.json` (two entries), `typediff/kb.py` (`_flag_combo_literal_arg`, `demote_on_exception`), `tests/test_upstream_day4.py` and `tests/data/upstream_day4/*` (new tests and fixtures), `tests/test_upstream_day3.py` (two expectations updated), `campaign/day4-morning.md`, `campaign/day4m/*` (helper scripts). Diff: `git diff 3383e2f HEAD`.

</details>
