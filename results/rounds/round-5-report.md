# Round 5 report

This report covers Round 5. The pipeline wrote nothing to GitHub: no issue, PR or comment was created, and the only GitHub access was read-only (`gh search`, `gh issue view`, `gh release list`). Counts come from the stored per-program reports and statistics of the round. Rates were computed while writing the report, and where a figure was not captured the report says so.

Tool versions (unchanged): mypy 2.4.0, ty 0.0.84, pyright 1.1.414, CPython 3.13.16, target Python 3.13.

Two sets of Round-5 numbers exist and both are shown. The first set comes from the judge run. After the decisions the same 250 reports were replayed under the final KB.

## 1. Funnel, Round 5 vs Round 4

| Measure | Round 4 | Round 5 (judge run) | Round 5 (after the replay) |
|---|---|---|---|
| programs run | 246 | 250 (`{ok: 250}`, `kbloop_run` 71 s, `--jobs 14`) | 250 |
| composition | 196 mutated + 50 fresh | 200 mutated (50 hits x 4) + 50 fresh | same |
| discrepancies | 175 | 154 | 154 |
| tool crashes | 40 (33 programs) | 42 | 42 |
| auto-closed (dismissed) | 73 | 60 | 86 |
| live | 142 | 136 | 110 |
| programs with a live finding | 83 | 105 | 87 |
| live crash findings | 16 | 20 | 18 |
| triage patterns | 29 | 29 (for the 136 live findings) | not re-run |

Check: Round 5, 154 + 42 = 196 findings = 136 live + 60 dismissed = 110 live + 86 dismissed. Round 4, 175 + 40 = 215 = 142 + 73.
Dismissal categories: DUPLICATE 44, DESIGN_DIVERGENCE 14, KNOWN_LIMITATION 2.
Round-5 live by kind (judge run): reveal_mismatch 46, only_mypy 44, only_ty 22, crash 20, reveal_unpaired 4. After replay: 36, 34, 21, 18, 1.

Per-program rates (computed here):

| Rate | Round 4 | Round 5 (judge run) |
|---|---|---|
| discrepancies per program | 175 / 246 = 0.71 | 154 / 250 = 0.62 |
| tool crashes per program | 40 / 246 = 0.16 | 42 / 250 = 0.17 |
| live findings per program | 142 / 246 = 0.58 | 136 / 250 = 0.54 |
| programs with a live finding | 83 / 246 = 33.7 % | 105 / 250 = 42.0 % |
| share of findings auto-closed | 73 / 215 = 34.0 % | 60 / 196 = 30.6 % |

With the final KB the Round-5 figures become 110 / 250 = 0.44 live per program, 87 / 250 = 34.8 % of programs with a live finding, and 86 / 196 = 43.9 % auto-closed.
The judge-run closure share is lower than Round 4 because the new entries were added after the run, in a second step, not before the judge run.
The Round-4 data replayed under the Round-5 step-1 matcher already gave live 136 and dismissed 79, so the like-for-like Round-4 baseline for the
pipeline fixes is 136 live, and for the interim entries is 110 live on the Round-5 data.

Parents: 51 files in `seeds/parents/` at the end (`check_hits.py 0.80`: 0 with problems, 0 near-duplicates). Each of the 8 `d4p_*` parents produced 4 Round-5 mutants.

## 2. What the four pipeline fixes changed

| Fix | Change | Effect in the numbers |
|---|---|---|
| 1a crash-closure audit | `Finding.closed_by` records entry id, url, signature, `requires` predicate; the same-signature dataset shortcut no longer closes crashes (it leaves a `SAME-SIGNATURE-AS` note); `kbloop_stats` prints `crash closures by closing reference` | Round 5 judge run: 22 `rule:crash:signal` closures, every one with a reference: MYPY-22361 6, TY-4148 6, TY-4898 4, MYPY-22360 3, TY-4882 2, MYPY-22344 1 (22 = 6+6+4+3+2+1). No `NO-REFERENCE` closure. Round 4 had 24 with the reference only in free text. Re-reading the Round-4 reports showed all 24 were entry-backed, so the Round-4 claims "14 unexplained closures" and "TY-4148 / MYPY-22361 closed none" were wrong: those two entries closed 8 findings in Round 4 (4 programs x 2 tools) |
| 1b variant k of n | `generate --n N` (N > 1) appends "Variant k of n" to the user prompt | Round 4: 246 prompts, 152 unique bodies (94 duplicates). Round 5: `inbox_check` reports 250 prompts, and my hash count of the prompt files gave 250 distinct bodies. Note: Round 5 used `--n 1` for most groups, so the count shows the fix did not break anything, but it is not a controlled before/after of the `--n 2` case. `seeds --mutate K` still sends identical prompts (review issue 1, not fixed) |
| 1c C1 entry gap | `call_attr_own_type` follows `__call__` attribute cycles (mutual pairs, chains, ClassVar, unions, subclasses); second step also follows `c = C(); c()` | Round-4 replay: live 142 -> 136, dismissed 73 -> 79, 6 findings changed (3 programs x ty/mypy), all now closed by TY-4148 / MYPY-22361; no C1 shape stays live. Round 5: TY-4148 6 and MYPY-22361 6 closures in the judge run, 7 and 7 after the widening (one more program, seed-0bc328316b4c) |
| 1d inbox accounting | `inbox_status` + `scripts/inbox_check.py` report orphan answers and malformed keys. Cause of Round-4's 270/271: 246 first-pass + 24 retry prompts, and one answer written under a key with a dropped character | Round-4 inbox: `prompts=270 answers=271 orphan_answers=1 malformed_keys=1`, exit 1. Round-5 inbox: `prompts=250 (retry prompts=0) answers=250 answered=250 pending=0 orphan_answers=0 malformed_keys=0`, exit 0. Round-4 preflight rejections corrected from 25 to 24 (9.8 %). Round 5 had 0 retry prompts |

Run-log gen passes for Round 5: pending 250 -> 236 -> 216 -> 196 -> 180 (answers arriving), then 139 -> 0 with written 250. The file records the pass lines
but not the grouping of the two answer batches, so I do not report more than that.

## 3. Round-5 results after the replay

Entries added or widened (all with the issue body read via read-only `gh`): `MYPY-21937-REVEAL` (new), `TY-876` (also `~F.X`), `MYPY-22339` (also a public property setter),
`MYPY-16830` and `MYPY-16830-REVEAL` (new, enum value aliases), `TY-4148` / `MYPY-22361` (local binding). Replay: `verify-sample: 30/30 identical`, 26 findings changed
(crash 2, MYPY-16830 10, MYPY-16830-REVEAL 7, TY-876 3, MYPY-21937-REVEAL 3, MYPY-22339 1), each hand-checked.

## 4. Candidates and evidence (UNVERIFIED unless stated)

| Candidate | Evidence | Status |
|---|---|---|
| pyright `RangeError: Maximum call stack size exceeded` (typeUtils.ts) on a descriptor with class-body decorators on `__get__`/`__set__` | 2 live findings in Round 5; a smaller reproducer crashes pyright 1.1.414, re-run by hand; mypy and ty give ordinary arg-type errors; CPython runs. Promoted to `seeds/parents/` | UNVERIFIED, no verification checklist; duplicate search incomplete (PYRIGHT-11961 is a different trigger; old closed RangeError issue bodies not read). pyright on PyPI is still 1.1.414, so no newer release to retest |
| ty protocol-flatten stack overflow (C2) | 9 findings in the `ty:signal-SIGABRT` pattern, 8 of them C2 per the grouping by parent | Round-4 verification verified Round 4, draft exists, not filed |
| mypy reflected operator on metaclasses (`A * B`, `A + B`, `A @ B`) | 8 live findings, runtime evidence strong | Round-4 verification draft, not filed |
| ty alias narrowing across a loop back edge | part of the 22 stale-alias findings | Round-4 verification draft, not filed |
| mypy silent on inconsistent generic bases (`type(...)`, `types.new_class`, and a plain `class` statement) | 4 live findings; mypy checks no inconsistent generic bases | UNVERIFIED, no mypy issue found by search, candidate for a later report |

Reclassified in Round 5 (not bugs, or not new):

* **ty#4656 (Self parameter on inherited methods): design difference, not a bug.** It is `prior_stances` `TY-4656` (stance `intended`) and the pipeline dismisses the pattern through
  `kb:TY-SELF-UPPER-BOUND` (DESIGN_DIVERGENCE). It is not in `entries`. A regression test (`test_ty4656_is_a_design_difference_not_a_bug_entry`) pins this. No Round-5 finding involves it.
* **Round-4 section 5 items** (step 2): `gen7_a8725dda.py` / `gen3_504999f8.py` (`tuple[*Ts, *Us]` is an invalid annotation in all three tools; the differing reveal is error recovery) excluded as a design difference;
  the enum-named ty panic is a ParamSpec `self: Callable[P, T]` program closed by TY-4899; the type-call generic-base program is a duplicate of an existing hit and the gap is "mypy does not check generic bases at all".
  The `self_call_union__mut1` program became a regression test rather than a parent. Only the pyright RangeError program was promoted.
* Duplicates (entries): enum alias rows (mypy#16830 / #21117), Flag `else` reveal (mypy#21937), `~F.X` (ty#876), property-setter variance (mypy#22339), `c = C(); c()` crash (ty#4148 / mypy#22361).
* Pinned-version artefacts: ty salsa panics (C3; fixed in ty 0.0.85; 8 findings in the triage pattern, 9 per the grouping by parent), old-style `Generic[*Ts, D]` (rejected by ty 0.0.97).
* Declared-type narrowing on assignment (`gen3_01446d71`, `gen6_0adac9f0`, `gen5_92e53331`), ParamSpec `self` mutants and the recursive-alias `...` rows: design differences, left live because no documented reference exists.

## 5. Remaining pipeline weaknesses

* `seeds --mutate K` has no variant line. The Round-4 report was not amended, so its wrong numbers still read as true there (review issue 2); this report and the.
* The widened C1 predicate is whole-program and name-based: a program with a C1-shaped class and a different stack-overflow trigger would still be closed as TY-4148 (tool + signature gate mitigates it).
* New entry matchers are syntactic: `enum_value_alias` ignores `auto()` and custom `__new__`; `flag_is_chain` does not check that the chain covers every member.
* The runtime-evidence rule reads `...` in recursive-alias reveals as a variadic tuple, giving false "strong" evidence (a normaliser change is still open).
* Triage is based on the judge run, so it was computed before the interim entries; the live count shown there (136) is above the final 110.
* The ParamSpec/dunder-call panics (C3) persist because the ty pin is 0.0.84; bumping the pin was recommended on Round 4 and not done.
* The pyright duplicate check is title-level for old closed RangeError issues.

## 7. Not verified

- Every candidate in section 4 is unverified: no verification checklist, no reduction, no run on newer releases (pyright has none; ty/mypy not re-run in this step).
- Family and parent grouping of the 110 live findings is by file name, not by reading each program.
- The triage patterns were not regenerated after the replay, so no post-replay pattern count exists.
- Whether the Round-5 prompt distinctness (250 of 250) is caused by the 1b variant line: most Round-5 groups use `--n 1`, so a `--n 2` before/after comparison was not made.
- Why 0 preflight rejections occurred in Round 5 against 24 in Round 4 was not investigated.
- The oomd count covers the last 6 h only and does not prove that no memory-pressure event happened earlier.
- Quality of the generated programs' answers was not reviewed beyond the preflight.
