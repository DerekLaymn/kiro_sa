# Day 8 report (pipeline changes, generation, judge, morning decisions, verification)

> Paths written as `[campaign working file]`, `[run output]` or `[agent working file]` point to scratch files of the original campaign that are not part of this repository.

Branch [campaign working file], local only. Nothing was pushed; no issue, PR or comment was written on GitHub (the run log and verification file record only read-only `gh search issues|prs`, `gh issue view`, `gh pr view`, `gh release list`, and a web fetch of the typing spec). No pin was changed. Every number below was read from [campaign working file], [campaign working file], [campaign working file], [campaign working file] or [campaign working file] (Day 7 figures from `results/days/day7-report.md` and [campaign working file]). Rates and the per-group discrepancy column were computed here from those counts; where a figure was not captured I say so. The final test run in section 9 was executed for this report.

Pins: mypy 2.4.0, ty 0.0.97, pyright 1.1.414, CPython 3.13.16, target Python 3.13. Same as Day 7. ty 0.0.98 (2026-11-05) and mypy 2.4.1 / master were used for verification only.

Day 7 vs Day 8 is not like for like. The KB and the harness changed before the Day-8 judge run (section 4), the generation mix differs (section 3), and Day 8 has 250 programs against 224. Both judge runs used `--pyright-only`, so the "without `only_pyright`" line is the comparable live count to Days 1 to 6.

## 1. What was run

| Phase | What | Result |
|---|---|---|
| 1 | Pipeline: ParamSpec `self_annotated_dunder_call` family triaged, 4 reductions e1 to e4; KB entries and matchers; harness records caught exceptions; display-noise canonicaliser; 82 new tests, then 24 more after review (iteration 2) | 604 passed, 20 PASS / 0 FAIL, `check_hits.py 0.80` 42 files / 0 problems |
| 2 | Morning plan [campaign working file], crash-parent probe, reserve of 26 programs, scripts [campaign working file], dry run | `pending=250 written=0` on the dry run; no generation |
| 3 | [campaign working file] 0 / 1 / 2, 51 headless worker sessions (`claude-haiku-5.5`, effort `medium`) | `pending=0 written=250`; `inbox_check.py` exit 0 (`prompts=251 (retry prompts=1) answers=251 answered=251 pending=0 orphan_answers=0 malformed_keys=0`) |
| 4 | Judge `kbloop_run.py ... --jobs 14 --pyright-only`, `TYPEDIFF_LLM=null` | `250/250 ok`, 72 s, exit 0 |
| 5 | Morning decisions on parents and KB | 0 promoted, 2 retired, 0 KB entries, `check_hits.py 0.80` 40 files / 0 problems |
| 6 | Verification of 9 candidates (13 strong findings in 11 programs, class F, one `only_pyright` row, ParamSpec reductions) | 3 STILL-BUG-NEW, 2 DUPLICATE, 3 NOT-A-BUG, 1 no new bug (inside it, e4 is a duplicate of ty#3666) |
| 7 | This report | see section 9 |

Generator model: all 51 worker sessions in the session logs have `"modelId": "claude-haiku-5.5"` and `"effortLevel": "medium"`; none mentions opus, gpt-* or sol-5.6 (run log item 31). Day 7 had 46 sessions.

Memory: lowest `MemAvailable` during the judge run 9852200 kB (9.40 GiB), first sample 11131856 kB (Day 7: 10221 MB lowest); 0 lines matching `oom|out of memory|killed process` in the journal for the window (3505 lines), no `systemd-oomd` entries. `--jobs 14` was kept.

## 2. Funnel, Day 7 vs Day 8

| | Day 7 judge run | Day 7 reports replayed on the Day-8 KB | Day 8 judge run |
|---|---|---|---|
| programs | 224 | 224 | 250 |
| discrepancies | 151 | not recorded | 208 |
| tool crash events | 31 | not recorded | 16 |
| findings (discrepancies + crashes) | 182 | 182 | 224 |
| auto-closed | 75 | 107 | 69 |
| live | 107 (88 without `only_pyright`) | 75 (63 without) | 155 (135 without) |
| programs with a live finding | 68 (60 without) | 48 (without: not recorded) | 104 (92 without) |
| live crash findings | 1 | not recorded | 1 |

The middle column is the Phase-1 replay with `--pyright-only --rerun-runtime` (`--verify-sample 30`, 30/30 identical; run log item 11). It shows what the Day-8 KB alone does to the Day-7 programs: 32 of 182 findings changed, all `review/gate` to dismissed (DISPLAY-EQUIVALENT 16, CALLABLE-SELF-RECEIVER 12, CALLABLE-SELF-ATTR-STORE 2, UPSTREAM-PYRIGHT-11382 1, UPSTREAM-TY-2792-READONLY 1), then 0 further tier changes with `--rerun-runtime`. The `findings` figure of 224 for Day 8 is 208 + 16, computed here; it agrees with live + dismissed (155 + 69).

Rates (computed here):

| | Day 7 | Day 7 on Day-8 KB | Day 8 |
|---|---|---|---|
| discrepancies per program | 151 / 224 = 0.67 | n/r | 208 / 250 = 0.83 |
| tool crashes per program | 31 / 224 = 0.14 | n/r | 16 / 250 = 0.06 |
| live findings per program | 107 / 224 = 0.48 | 75 / 224 = 0.33 | 155 / 250 = 0.62 |
| live per program without `only_pyright` | 88 / 224 = 0.39 | 63 / 224 = 0.28 | 135 / 250 = 0.54 |
| programs with a live finding | 68 / 224 = 30.4 % | 48 / 224 = 21.4 % | 104 / 250 = 41.6 % |
| ... without `only_pyright` | 60 / 224 = 26.8 % | n/r | 92 / 250 = 36.8 % |
| share auto-closed | 75 / 182 = 41.2 % | 107 / 182 = 58.8 % | 69 / 224 = 30.8 % |
| strong-evidence live findings per program | 5 / 224 = 0.02 | n/r | 13 / 250 = 0.05 |

(n/r = not recorded.) The live rate went up from Day 7 (0.39 to 0.54 per program, comparable count), although the KB is stronger: the Day-7 programs on the Day-8 KB give 0.28. So the Day-8 programs yield more live findings than the Day-7 programs do under the same KB, and section 3 shows where (per area, `overloads` 6 to 26 live, `tuples_unpacking` 7 to 18). I did not run the Day-8 programs on the Day-7 KB, so I cannot split the rise into mix and KB. The auto-closed share fell (41.2 % to 30.8 %); the closed crash events halved (30 on Day 7, 15 on Day 8).

Day 8 dismissed by category: DESIGN_DIVERGENCE 35, DUPLICATE 21, NOISE 8, KNOWN_LIMITATION 3, SPEC_AMBIGUITY 2 (Day 7: DUPLICATE 37, DESIGN_DIVERGENCE 28, SPEC_AMBIGUITY 7, KNOWN_LIMITATION 3, no NOISE). By entry: `rule:crash:signal` 15, LITERAL-WIDENING 12, TY-SELF-UPPER-BOUND 11, DISPLAY-EQUIVALENT 7, PRECISION-RUNTIME-CONSISTENT 6, UPSTREAM-TY-4212 4, UPSTREAM-MYPY-22339 4, JOIN-VS-UNION 3, ASSERT-TYPE-LITERAL-RETENTION 2, BOTH-GRADUAL 2, REVEAL-ERROR-RECOVERY 1, UPSTREAM-TY-4756 1, UPSTREAM-PYRIGHT-11382 1. Of the entries added in Phase 1, only DISPLAY-EQUIVALENT (7) and UPSTREAM-PYRIGHT-11382 (1) closed anything on Day 8 programs. CALLABLE-SELF-RECEIVER, CALLABLE-SELF-ATTR-STORE, UPSTREAM-TY-3666, MYPY-2455 and TY-4941 closed none, because the Day-8 mix has only 8 programs of the ParamSpec parent (all of them ty crashes) and no hash parent.

Auto-closed crashes: 15, by closing reference TY-4898 8, MYPY-22361 3, TY-4148 3, TY-4882 1. The 16 crash events are these 15 plus one live pyright `RangeError`.

Live by kind, Day 7 then Day 8: reveal_mismatch 43 / 67, only_mypy 23 / 48, only_pyright 19 / 20, only_ty 14 / 14, concern_mismatch 7 / 5, crash 1 / 1. The rise is in `reveal_mismatch` (+24) and `only_mypy` (+25).

`only_pyright` runtime relations ([campaign working file], run log item 35): `runtime_contradicts` 20, `runtime_supports` 1. Day 7 had 0 of 19 before the Phase-1 harness change, and 1 of 19 after it (run log item 11). The one Day-8 row is `seed-8af1b011a91f` D1; it was read in Phase 6 and is NOT-A-BUG (D8-8).

Strong runtime evidence on a live finding: 13 findings in 11 programs (Day 7: 5 findings).

## 3. Per group

Day 8 groups are the subdirectories of [run output] that hold a mutant's parent ([campaign working file]); they differ from the Day-7 groups, so there is no row-by-row comparison. Planned mix (run log item 29): 40 crash, 26 reserve, 18 pyright descriptors, 8 promoted parent, 120 fresh, 38 seed mutants. The discrepancy column is live + dismissed - crash events (derived here; the column sums to 208). "Live" and "strong" are findings, not programs. Per-group discrepancies were not captured by `group_yield.py`.

| Group | Programs | Programs with a live finding | Discrepancies (derived) | Crash events | Live | Strong | Dismissed | Live per program |
|---|---|---|---|---|---|---|---|---|
| A_pyright_range (2 parents) | 12 | 9 | 12 | 0 | 12 | 0 | 0 | 1.00 |
| A_ty_4898 (1) | 8 | 0 | 0 | 8 | 0 | 0 | 8 | 0.00 |
| A_ty_escape (4) | 8 | 1 | 1 | 7 | 1 | 0 | 7 | 0.12 |
| H_new (1) | 8 | 4 | 5 | 0 | 4 | 4 | 1 | 0.50 |
| N_seeds_a (3) | 6 | 4 | 8 | 0 | 8 | 0 | 0 | 1.33 |
| N_seeds_b (8) | 32 | 16 | 42 | 0 | 20 | 2 | 22 | 0.62 |
| P_pyright (3) | 18 | 6 | 17 | 1 | 9 | 4 | 9 | 0.50 |
| R_reserve2 (1) | 2 | 2 | 3 | 0 | 2 | 0 | 1 | 1.00 |
| R_reserve3 (8) | 24 | 22 | 41 | 0 | 36 | 2 | 5 | 1.50 |
| fresh | 132 | 40 | 79 | 0 | 63 | 1 | 16 | 0.48 |
| total | 250 | 104 | 208 | 16 | 155 | 13 | 69 | 0.62 |

Group notes (`group_yield.out` and run log item 36):

* The 16 crash events come from A_ty_4898 (8), A_ty_escape (7) and P_pyright (1, the live pyright `RangeError`); 15 are closed. The TY-4898 parent produced 8 ty crashes, all closed (reference `TY-4898`, DUPLICATE), 0 live. The escape watch on the retired TY-4148 / TY-4882 parents gave 7 closed crashes and 1 live non-strong `only_mypy` row (run log item 42); no escape.
* A_pyright_range: all 12 live findings are `only_pyright`; `d5p_*_rangeerror` parents 8 and 4 live, 0 strong. These are the neighbours of Day-7 draft 7, see D8-6.
* H_new (8 mutants of `d7p_tuples_unpacking_partial_unpack_except_ty`): 4 live, all 4 strong, all `reveal_mismatch`. This is the only group where every live finding has runtime evidence, and it is a rediscovery (D8-1).
* R_reserve3 (the pass-2 reserve, 24 programs): 36 live, the highest rate (1.50). 14 are `only_mypy`, 16 `reveal_mismatch`. The reserve was chosen from Day-7 programs that still had a live finding, so a high rate is expected.
* Per parent, the largest live counts: `rsv_overloads_d41747bd` 8 (2 strong), `d5p_descriptors_decorated_get_pyright_rangeerror` 8, `self_classmethods__self_param_inherited` 6 (2 strong), `rsv_abstract_classes_ae31b752` 6, `rsv_recursive_aliases_d5395259` 6. `typeddict__readonly_notrequired` gave 0 live, 9 dismissed; `paramspec_identity_applied_to_itself` 8 programs, 0 live, 8 dismissed.

Per area, the seven areas that had no parent before Day 7 (area directories, `group_yield.out`; Day 7 from its report section 6):

| Area | Day 7 programs | Day 7 live | Day 8 programs | Day 8 live | Day 8 dismissed | Day 8 live per program | Day 8 strong |
|---|---|---|---|---|---|---|---|
| match_statement | 16 | 21 | 26 | 21 | 0 | 0.81 | 0 |
| overloads | 16 | 6 | 26 | 26 | 8 | 1.00 | 3 |
| tuples_unpacking | 22 | 7 | 26 | 18 | 10 | 0.69 | 4 |
| dataclasses | 28 | 13 | 37 | 12 | 1 | 0.32 | 0 |
| abstract_classes | 10 | 2 | 12 | 6 | 0 | 0.50 | 0 |
| typeddict | 16 | 8 | 16 | 3 | 13 | 0.19 | 0 |
| final_classvar | 16 | 0 | 8 | 0 | 1 | 0.00 | 0 |
| total | 124 | 57 | 151 | 86 | 33 | 0.57 | 7 |

(Day 7 total live per program was 0.46.) `typeddict` live fell from 8 to 3 and its dismissed rose to 13, which matches the Day-7 replay on the Day-8 KB (typeddict 8 to 0 live, run log item 22). Live per program is a count of triage items, not of bugs. 14 of the 26 `overloads` live findings come from the three `rsv_overloads_*` reserve parents; the strong overloads findings turned out to be NOT-A-BUG (D8-3, D8-4). The other areas with live findings: recursive_aliases 18 programs / 27 live / 0 strong, descriptors_properties 36 / 24 / 4, self_classmethods 25 / 14 / 2.

## 4. What changed since Day 7

Phase 1 (code and KB, run log items 3 to 19):

* ParamSpec `self_annotated_dunder_call` family (16 Day-7 and 21 Day-6 live findings) triaged with four reductions; no new bug. Entries `CALLABLE-SELF-ATTR-STORE` (DESIGN_DIVERGENCE), `CALLABLE-SELF-RECEIVER` (SPEC_AMBIGUITY), `UPSTREAM-TY-3666` (DUPLICATE), `DISPLAY-EQUIVALENT` (NOISE). Family live 16 to 0 on the Day-7 replay.
* Duplicate matchers: `_stale_attr_context` treats a store into a data-descriptor attribute like a mutating call (TY-2792, TY-2792-READONLY), `PYRIGHT-11382`, `MYPY-2455` and `TY-4941` (class unhashable only through `__eq__`). The upstream-entry matcher accepts `"kind": "only_pyright"`.
* Harness: records every exception raised in a frame of the program (`raised`), used by `pyright_runtime_relation` and `handled_type_exception`. Two artefacts fixed: `...` in a mypy recursive-alias reveal, and a `runtime_miss` that follows a flagged, executed `# expect-error` line.
* Review iteration 2: staticmethod parameters are no receivers; the `runtime_miss` suppression needs a shared program name; `CALLABLE-SELF-ATTR-STORE` no longer cites ty#3666; `DISPLAY-EQUIVALENT` compares defaults strictly between ty and pyright but treats `...` or a bare `default_factory` name as equal (a user decision, run log item 17).
* Tests 498 to 604 (82 + 24 new). kb-selftest stays at 20 entries (no `example` field added).
* Phase-1 replays: Day 7 live 107 to 75; Day 6 (`--pyright-only`) 31 of 358 findings changed, live 231 to 199; Day 3, 4, 5 controls changed 2, 1 and 9 findings, each row read.

Phase 2 and 3: new scripts [campaign working file], 9 parent groups, 250 programs including the 26-program reserve (Day 7 left its reserve ungenerated), 40 crash-family programs.

Phase 5: promoted 0 (every strong program is a rediscovery of an existing parent or issue; the 11 candidates were re-run alone and all reproduce). Retired 2 (`d3p_paramspec_identity_applied_to_itself`: 0 live in 8 programs; `d3p_paramspec_self_annotated_dunder_call`: 0 live and 17 dismissed in its 7 Day-7 mutants under the final KB). [run output] 42 to 40; `check_hits.py 0.80`: 40 files, 0 problems. The retirement is reversible (`mv [run output]<name>.py [run output]`).

KB entries added in Phases 2 to 6: none. Three entries were queued but not implemented (section 7).

## 5. Candidates and verdicts ([campaign working file])

All run with the pins plus ty 0.0.98, mypy 2.4.1 and master, pyright 1.1.414 (latest). CPython 3.13.16.

| Id | Candidate | Verdict |
|---|---|---|
| D8-1 | ty reveals the old value in `except` after a nested unpacking target failed half-way (4 programs, 4 strong). CPython `'bad'`, ty `Literal[1]` / `Literal[0]`, mypy `int \| str`, pyright `Literal[1]` | STILL-BUG-NEW (ty), same root cause as unfiled draft 6; no new draft. New shapes: star target, attribute chain, `match` in the handler. ty 0.0.98 still has it |
| D8-2 | ty reveals `Never` for a read-only property after contradicting asserts, then skips the assignment error (2 programs, 3 strong) | DUPLICATE ty#2792 (open) |
| D8-3 | ty `invalid-return-type` for `return norm(v)` with a catch-all `T -> T` overload (2 programs, 2 strong) | NOT-A-BUG. The `T -> T` overload is the only one accepting the whole union, so spec step 2 picks it. ty and pyright follow the spec, mypy does union math first by design |
| D8-4 | mypy reveals `str` after `k: str = 'int'`, ty and pyright `int` (1 strong, against mypy) | NOT-A-BUG. mypy's binder erases the literal on assignment (`binder.py`) |
| D8-5 | ty accepts `x.add(Node())` for `add(self, c: 'Self')` on a subclass (2 strong) | DUPLICATE ty#4656 (closed, intended) |
| D8-6 | pyright `RangeError` on a decorated descriptor `__get__` (1 strong crash) | STILL-BUG-NEW (pyright), same root cause as unfiled draft 7; no new draft. Exit 2 on 1.1.414; PR #11965 and issue #11961 still open |
| D8-7 | mypy `[override]` on an overload item of `__post_init__` (class F, 6 findings, 0 strong) | STILL-BUG-NEW (mypy), **draft 8**, confidence 0.6. Reduced to 14 lines, mypy 2.4.0 / 2.4.1 / master reject, ty and pyright accept, CPython runs. Not debugged in mypy; duplicate search found no match |
| D8-8 | only pyright rejects `Desc.__delete__(Desc(), h, 1)` behind an untyped class-body decorator (the one `runtime_supports` row) | NOT-A-BUG for ty and mypy. ty does not infer return types by default (ty#4739); with `analysis.return-type-inference = "always"` ty reports it |
| D8-9 | ParamSpec `self_annotated_dunder_call` reductions e1 to e4 | No new bug; e4 DUPLICATE ty#3666 (open) |

Also read: an annotation-only `__call__: Callable[[], int]` (`d3p_callables_self_call_attr__mut0_5445453a`): CPython raises `TypeError`, ty and pyright accept `C()()`, mypy rejects with a different cause. Not drafted, confidence 0.4, not strong; candidate for a Day-9 look.

Net: 11 strong programs gave 1 new draft (draft 8, from the class-F lead, not from a strong finding), 2 extensions of unfiled drafts 6 and 7, 2 duplicates of open or closed upstream issues, 3 not-a-bug verdicts. Draft 8 was appended to `results/bugs.md` with a `<PLAYGROUND LINK>` placeholder; drafts 6, 7 and 8 are not filed (the author listing of the filing account shows ty#4656, #4884, #4899, #4933, #4934, #4941 and mypy#22339, #22360, #22375, #22377 only). Day 7 yielded two new drafts (6, 7).

Verification effort: 113 one-to-three-word `gh search` queries (ty 44, mypy 28, pyright 20, ruff 2 issue and 8 PR, mypy 5 PR, pyright 5 PR, python/typing 1), after a first batch of 62 longer queries was discarded because GitHub ANDs all words; 21 issue/PR views (one wrong number, mypy#4380) and 3 release lists.

## 6. Parents and hits

Promoted 0, retired 2, hits 42 to 40, `check_hits.py 0.80` 40 files / 0 problems with no near-duplicate pair (run log items 40 to 45, verification section 6). Highest similarity of a strong candidate to an existing hit: 0.86 (`d7p_..._mut0_d873ebcb`, to its parent) and 0.81 (`d4p_..readonly_prop_never__mut0_f116e46b`, to its parent), both above the 0.80 limit; the other nine are 0.27 to 0.74 and were not promoted for root-cause reasons (rule: same root cause and no new shape). No program was copied to [run output].

## 7. Weaknesses

* Three KB entries queued in Phase 2 are still not implemented: `TY-NONFINAL-PATTERN` (11 live Day-7 rows), `ASSERT-NEVER-ALL-REJECT` (6), and a wider `JOIN-VS-UNION` (3). The Phase-2 plan expected about 20 to 25 more live findings from these classes ([campaign working file] section 10). They still match live rows in the Day-8 triage (`concern_mismatch assert_never` 4 rows, `only_mypy arg-type ... describe(v)`, `reveal_mismatch` `& ~Name`). That is part of the Day-8 live count of 155.
* Two matchers are too narrow for known duplicates (run log item 46): `mentions_self` does not read a quoted `'Self'` annotation (2 live `only_mypy` findings of `3a63c673`, a ty#4656 duplicate), and `TY-2792-READONLY` requires the assignment in the scope of the stale narrowing (2 programs, 3 strong findings, D8-2). They are code changes, not entries, and were not made.
* The runtime-evidence rule gave 13 strong live findings, and none of them is a new bug of its own: 4 + 1 rediscoveries of unfiled drafts, 3 + 2 duplicates, 3 not-a-bug. Strong evidence from the runtime says the checker's type is wrong for the observed value, not that the checker is wrong by its own rules (D8-3, D8-4).
* `runtime_supports` for `only_pyright` fired once in 20 (and the one row is NOT-A-BUG). The Phase-1 harness change moved it from 0 to 1 of 19 on Day 7 and 0 to 5 of 37 on Day 6; the 0.7 weighting is still untested on a true positive.
* `handled_type_exception` is not tied to the subject of pyright's diagnostic; it only orders the review queue (priority 0.3 to 0.7). Left unchanged (run log item 18).
* `CALLABLE-SELF-RECEIVER` is deliberately broad inside programs that contain a `Callable`-annotated receiver. Unhashable set and dict displays with pyright `reportUnhashable` stay live and were not searched (run log, Phase 1 open points).
* Draft 8 has no playground link, and drafts 6, 7 and 8 are unfiled. D8-1 and D8-6 are rediscoveries of drafts 6 and 7, so they will keep appearing live (4 and 1 strong findings today) until the issues are filed and an entry exists.
* `recursive_aliases` (27 live, 0 strong, 0 dismissed) and `match_statement` (21 live, 0 dismissed) are large live sources; the logs record no read of the `recursive_aliases` live rows.
* Day-7 comparison is confounded by the mix and the KB; the split was not measured.

## 8. Not verified

* Drafts 6, 7 and 8 on a playground (placeholders open). No playground (ty, mypy, pyright) was used.
* ty `main`, pyright `main`, mypy PR branches and the branch of pyright PR #11965; none was built.
* The cause of D8-7 inside mypy (read in `checker.py` and the dataclasses plugin, not debugged). Confidence 0.6; the maintainers may call the per-item check intended.
* Whether ty and pyright intend annotation-only dunder members to count (the `__call__` lead, confidence 0.4).
* How the Day-8 live rate splits between KB and generation mix (section 2).
* Discrepancies per group, Day-7 live crash findings on the Day-8 KB replay, Day-7 programs with a live finding without `only_pyright` on that replay (not captured).
* Quality of the 250 programs beyond the preflight, the triage read and the Phase-5 per-area read (match_statement and dataclasses were read in full; other areas' live rows were not all read).
* `p_overloads_1de657a6`: pyright `str` for `norm(Any)` was seen once; the minimal `c10.py` gives `Unknown`, not pursued.
* Day-6 candidates 2 (ty recursive alias solution) and 3 (mypy memory blow-up) were not revisited.

## 9. Final checks at the end of Day 8

Run for this report on branch [campaign working file] at commit `ddf8dc5` (no code or KB change since Phase 1; outputs in [campaign working file]):

* `.venv/bin/python -m pytest tests -q` -> **604 passed** in 109.19 s, exit 0 (`pytest.out`). Phase 6 recorded 604 passed in 77.06 s; the run time differs, the count does not.
* `.venv/bin/typediff --python-version 3.13 kb-selftest` -> **20 PASS, 0 FAIL**, exit 0 (`kb.out`, `kb-counts.out`).
* `.venv/bin/python [campaign working file] 0.80` -> **40 files; 0 with problems**, no near-duplicate pair, exit 0 (`hits.out`).

Working tree notes: `results/days/day7-report.md` carries an uncommitted edit that is not mine (noted in run log items 1 and 52) and [campaign working file] shows as modified; neither is committed here. Untracked `-l`, `.kiro/` and `findings/2026-10-27-llm-run/` are left alone. Nothing was pushed.
