# Day 5 step 1: crash closure audit trail, variant prompts, wider C1 matcher, inbox accounting

Four pipeline fixes on `campaign/day5-p2` (5 commits over `campaign/day4-p2`). Crash findings are now auto-closed only by a `known_upstream` crash entry, and the closing entry is stored in a new `Finding.closed_by` field; the dataset's same-signature shortcut no longer closes crashes. `generate --n N` (N > 1) appends a "Variant k of N" line to the user prompt so the N prompts differ in text. The `call_attr_own_type` predicate behind TY-4148 / MYPY-22361 was rewritten to cover every `__call__` attribute cycle, and an inbox checker (`inbox_status`, `scripts/inbox_check.py`) explains and now detects the Day-4 270-prompt / 271-answer mismatch. ty#4656 is confirmed to be a design difference, not a bug entry.

Watch for: the same variant line is not applied to the `seeds --mutate K` loop, which still sends K identical prompts (confirmed, out of the stated scope); the Day-4 report itself was not amended, so its wrong numbers (25 rejections, "14 unexplained" closures, "neither entry closed any finding") still read as true outside the run log (confirmed); the widened matcher is whole-program and name-based, so a program with a C1-shaped class plus a different stack-overflow trigger would still be closed as TY-4148 (likely, mitigated by the tool+signature gate).

**Verdict**: APPROVED

## High-level view

Crash closure now has one path with a recorded reason. `match_crash` (tool, signature regex, mandatory AST predicate) is the only thing that can dismiss a crash, and it writes the entry id, url, signature and predicate name into `closed_by`. A same-signature record in a shared dataset leaves the crash live with a `SAME-SIGNATURE-AS` note, which fixes the failure mode where distinct bugs sharing `ty:signal-SIGABRT:stack-overflow` were silently merged. No "explained cause" closing path exists; the entry match is the only basis, which is the stricter reading of the requirement.

The variant line is a prompt-text change only. It is added when `--n > 1` for every operator (not just `feature_crossover`), `n == 1` is byte-identical to before, and cache keys for `--n >= 2` prompts change.

The C1 inconsistency was a matcher gap, not a pipeline gap. The predicate now builds a graph of classes whose `__call__` attribute type leads back to themselves, adds subclasses, and requires a call on such an instance or on a name annotated with a type that contains one. The Day-4 replay changed exactly the six expected findings (three programs, ty and mypy each) and nothing else.

The 270/271 mismatch was one answer written under a key with a dropped character, plus 24 preflight-retry prompts on top of 246 first-pass prompts. The fix is detection (`inbox_status`, exit 1 on orphans and malformed keys); nothing renames or repairs files.

ty#4656 is a `prior_stances` entry with stance `intended`, is absent from `entries`, and the pipeline dismisses the pattern through `kb:TY-SELF-UPPER-BOUND` (DESIGN_DIVERGENCE). A regression test now pins that.

<details>
<summary>Issues (6)</summary>

1. **Variant line missing from `seeds --mutate K`** (confirmed) — the loop in `cmd_seeds` calls `generate(...)` K times with identical arguments and `seed=0`, so all K prompts share one cache key and yield the same variant. Pass `variant=(k+1, args.mutate)` or document that `--mutate` is single-variant.
2. **Day-4 report not amended** (confirmed) — `campaign/day4-report.md` still states 25 preflight rejections, "14 unexplained" closures, "neither entry closed any finding" and "inbox not traced". The corrections exist only in `campaign/day5-run-log.md`. Add an errata block or fix the figures in the Day-5 report.
3. **Variant line scope differs from the step wording** (confirmed) — the line is added for all operators when `n > 1`, not only `feature_crossover`. This matches the Day-4 report (non-crossover prompts also had duplicates: 148 files, 103 unique), so keep it, but state it in the Day-5 report.
4. **Subclass override not checked** (confirmed in code, impact likely low) — a subclass of a family class joins the family even if it defines `def __call__`, and `typed` names are collected program-wide without scoping. Both widen the match beyond a proven crash shape; the tool+signature gate limits the damage. Add a control test for a subclass overriding `__call__` with a method.
5. **Whole-program matcher can mask a second bug** (likely) — `requires` inspects the whole source, so a program holding a C1 shape and an unrelated `stack-overflow` trigger is closed as TY-4148. The replay shows C2/C3 programs were not caught; reduction before closure would remove the exposure. Keep an eye on `closed_by` counts in later days.
6. **Cache invalidation for `--n >= 2`** (confirmed, informational action) — answers prepared for old `--n 2` prompts are never reused. Make sure Day-5 gen-pass scripts regenerate prompts and call `scripts/inbox_check.py` after each pass, as the log recommends.

</details>

<details>
<summary>Details</summary>

### Crash closure through `closed_by`, not the dataset shortcut

`Pipeline._judge` runs `match_crash` first for CONFIRMED/CANDIDATE crash findings. On a hit it dismisses the finding and now also sets `closed_by = "<id> <url> signature=<sig> requires=<fn>"`; the existing `DUPLICATE of ...` review note is kept, so old consumers still work. After the prior-stance cap, the dataset lookup splits: a crash with a same-signature record stays CONFIRMED and gets `SAME-SIGNATURE-AS <record>: NOT closed ...`; non-crash findings keep the old dismissal. `decided_by` remains `rule:crash:signal` on closures, so the entry can only be read from `closed_by` or the note.

The change is a behavioural narrowing for runs with a shared dataset (`typediff run`, `typediff seeds`). `scripts/kbloop_run.py` passes `dataset=None`, so the Day-4 campaign never used the shortcut; the log's re-read of all 36 Day-4 crash findings confirms every one of the 24 closures was entry-backed. The 14 closures the Day-4 report called unexplained are MYPY-22360 x4, MYPY-22344 x3, MYPY-22343 x2, TY-4898 x3 and TY-4882 x2. The reclassification therefore corrects the report; it does not change pipeline behaviour for the campaign.

`scripts/kbloop_stats.py` adds a "crash closures by closing reference" line. It reads `closed_by`, falls back to the `DUPLICATE of <url> (<ID>)` note for older reports and prints `NO-REFERENCE` otherwise, which makes an unauditable closure visible. After the replay it totals 30 (28 signal + 2 panic), equal to the 24 old closures plus the 6 new ones.

No "reproducible explained cause" path was built; the entry match is the only closing basis, which is the stricter reading of "known_upstream crash entry or explained cause, else live".

### Variant k of n

`generate(..., variant=(k, n))` appends `GENERATOR_VARIANT` ("Variant k of n: independent variants of this request are written separately; make this one differ from the others.") to the user prompt only when `n > 1`. `cmd_generate` passes `(k + 1, --n)`. The instruction "make this one differ from the others" nudges the model toward diversity. That is the intent from the Day-4 report (94 of 246 prompts carried no new information), but it does alter what the model is asked, beyond just making cache keys distinct. The other half of Day-4 recommendation 1, de-duplicating identical prompt bodies before asking for answers, is not part of this change.

The `seeds --mutate K` loop (`cmd_seeds`, around cli.py line 132) calls `generate` K times with the same arguments and no seed. The prompt, and therefore the `FileLLM`/cache key, is identical each time, so K mutations collapse to one answer. The run log notes that this path was not touched. It is the same defect the variant line fixes for `generate`, so it is worth a follow-up.

### Wider `call_attr_own_type` for TY-4148 and MYPY-22361

The old predicate accepted `__call__` annotated with the class itself, `Self`, or `X | None` of those, and calls on names annotated exactly as that class. The new one builds edges from each class to the classes named in its `__call__` annotation (through `|`, `Union`, `Optional`, `ClassVar`, `Final`, `Self`), keeps the classes that reach themselves, adds subclasses, and requires `X()()` or a call on a name whose annotation contains a family class. That covers mutual pairs, three-class chains, `ClassVar`, `"B | None"` pairs, subclasses and a union-typed parameter (the three live Day-4 programs). The evidence that these shapes crash both tools is `campaign/day4/verify-v1.md` section 4, which exists, plus the Day-4 crash signatures of the three programs. The no-cycle look-alikes (`__call__: int`, a chain ending in a non-callable, `list["C"]`, a `__call__` method, never-called, unrelated type) have control tests, and the notes in `known_upstream.json` were updated to drop the old "NOT matched" sentence.

Two over-matching edges remain without control tests. A subclass joins the family without checking whether it overrides `__call__` with a method, and called names are collected program-wide by identifier, so `x` annotated as a family class in one function marks every `x()` call. The predicate also reads the whole program, not a reduced repro, so a program holding a C1 shape plus a different stack-overflow trigger would still be closed as TY-4148 or MYPY-22361. `match_crash` still requires the tool and the crash signature, which limits this to programs that really crash with that signature. The replay shows C2 (protocol flatten, 5 ty findings), C3 (salsa panic, 4) and the pyright RangeError program stayed live, so today's data has no such collision.

### Inbox accounting: 270 prompts, 271 answers, 246 programs

The log traces the mismatch to 246 first-pass prompts plus 24 retry prompts (text contains "rejected by the preflight lint") = 270, and one answer, `e6673866643ecc8.answer.json`, written under a key with a dropped character (prompt `e66738668643ecc8`). `FileLLM` reads only `<key>.answer.json`, so it ignored that answer and the prompt stayed pending until re-answered under the right key. This corrects the Day-4 rejection count to 24 of 246 (9.8 %) and pass-1 `pending=25` to 24 rejected + 1 unanswered.

`inbox_check.py` exits 1 on orphan answers or malformed keys; the log records it flagging the Day-4 inbox (`orphan_answers=1 malformed_keys=1`). The tool detects only; it does not repair or rename, so a mistyped key still costs a pass unless the gen-pass scripts call it.

### ty#4656 is a design difference, not a bug entry

`typediff/data/known_upstream.json` has no `entries` item for ty#4656. It appears once, as `prior_stances` id `TY-4656`, stance `intended`, note "closed as intended behaviour (design divergence), not a bug". `kb.py` dismisses the pattern as `TY-SELF-UPPER-BOUND` with `Dismissal.DESIGN_DIVERGENCE`, citing ty#4656 as a design divergence and ty#4673 as the display bug. The new regression test asserts the absence from `entries`, the `intended` stance, and the DESIGN_DIVERGENCE dismissal.

### Verification evidence

The run log records the full suite twice, first on the working tree and again on committed HEAD `3263e9f`: `408 passed` (373 baseline plus 35 new tests), exit 0, and `typediff --python-version 3.13 kb-selftest` at 21 PASS / 0 FAIL, exit 0. The requested gate figure is 373 passing; 408 includes those 373 and adds the new tests, so the condition holds. The replay evidence is a 246-report Day-4 replay with a 20/20 sample matching a full re-run and exactly six changed findings. HEAD is `29129ab`, which only appends to the run log (one line), so the recorded results apply to the reviewed code. I did not re-run any suite.

</details>

<details>
<summary>File map</summary>

Full diff: `git diff campaign/day4-p2..campaign/day5-p2`.

- `typediff/models.py`: `Finding.closed_by` field.
- `typediff/pipeline.py`: set `closed_by` on entry closure; same-signature shortcut skips crashes and adds a note.
- `typediff/dataset.py`: persist `closed_by` in dataset records.
- `typediff/crash_upstream.py`: `call_attr_own_type` rewritten as a class graph with `_type_leaves`.
- `typediff/data/known_upstream.json`: TY-4148 and MYPY-22361 notes updated.
- `typediff/generator.py`, `typediff/prompts.py`, `typediff/cli.py`: `variant` parameter, `GENERATOR_VARIANT`, `cmd_generate` wiring.
- `typediff/llm.py`: `inbox_status`.
- `scripts/inbox_check.py`: new inbox checker.
- `scripts/kbloop_stats.py`: closing-reference summary line.
- `tests/test_pipeline_day5.py`, `tests/test_generate_variants.py`, `tests/test_inbox_check_day5.py`, `tests/test_upstream_day4.py`: new and adjusted tests.
- `tests/data/upstream_day5/*.py`, `tests/data/upstream_day4/ty4148_mutual_pair.py` (renamed): C1 test programs.
- `campaign/day5-run-log.md`: run log and verification record.

</details>
