# Round 7 report (Parts A to D: KB policy, pyright-only kind, generation, judge, verification)

This report covers Round 7. The pipeline wrote nothing to GitHub: no issue, PR or comment was created, and the only GitHub access was read-only (`gh search`, `gh issue view`, `gh release list`). Counts come from the stored per-program reports and statistics of the round. Rates were computed while writing the report, and where a figure was not captured the report says so.

Pins: mypy 2.4.0, ty 0.0.97, pyright 1.1.414, CPython 3.13.16, target Python 3.13. Same pins as Round 6. ty 0.0.98 (released 2026-11-05) was installed beside the pin for verification only.

Round 6 vs Round 7 is not like for like. The generation mix changed on purpose (fewer crash-family programs, `C_callback` dropped, seven areas that had no parent added), the Round-7 run has 224 programs instead of 250, and the Round-7 judge ran with the new opt-in `only_pyright` kind. The comparable live count is the "without `only_pyright`" line.

## 1. What was run

| Part | What | Result |
|---|---|---|
| A | KB: 4 narrow entries (`TY-2171`, `TY-2171-ASSERT`, `TY-2792`, `TY-2792-READONLY`), 2 calibration programs moved from `must_stay_live/` to `known_duplicates/` | 479 passed, 20 PASS / 0 FAIL |
| B | opt-in `only_pyright` finding kind, 4 more parents retired, generation plan | 498 passed after review fixes, 20 PASS / 0 FAIL, `check_hits.py 0.80` 45 files / 0 problems |
| C | generation passes 0 / 1 / 2, 46 model sessions (`claude-haiku-5.5`, effort `medium`), judge `kbloop_run.py ... --jobs 14 --pyright-only` | `224/224 ok`, 61 s; `inbox_check.py` exit 0 (`prompts=225 (retry prompts=1) ... orphan_answers=0 malformed_keys=0`) |
| C | tests, KB self-test, hits check | 498 passed (71 s), 20 PASS / 0 FAIL, 42 files / 0 problems |
| D | reduction, version matrix (ty 0.0.97 and 0.0.98, mypy 2.4.0 / 2.4.1 / master, pyright 1.1.414), duplicate searches | 6 candidates verified, 2 new drafts |

Part C ran without `kbloop_replay` because the KB did not change in Part C. Part D changed no code.

Generator model: all 46 model sessions used `claude-haiku-5.5`; 45 of 46 also recorded effort `medium` (the 46th has no such line, the flag was on the command line). No other model id in the 30 retained `GenerateAssistantResponse` log lines.

Memory: lowest available memory during the judge run 10221 MB (Round 6: 9954 MB); 0 `oom-kill` / `systemd-oomd` events since 01:30 IST. `--jobs 14` was not reduced.

## 2. Funnel, Round 6 vs Round 7

| | Round 6 judge run | Round 6 after the Round-6 replay | Round 6 after the Part A replay (194) / Part B flag (231) | Round 7 judge run |
|---|---|---|---|---|
| programs | 250 | 250 | 250 | 224 |
| discrepancies | 259 | 259 | 259 + 37 `only_pyright` with the flag | 151 |
| tool crash events | 62 | 62 | 62 | 31 |
| findings (discrepancies + crashes) | 321 | 321 | 321 (358 with the flag) | 182 |
| auto-closed | 103 | 109 | 127 | 75 |
| live | 218 | 212 | 194 without the flag, 231 with it | 107 (88 without `only_pyright`) |
| programs with a live finding | 127 | 122 | 110 without, 123 with | 68 (60 without `only_pyright`) |
| live crash findings | 23 | 23 | not recorded for the replay | 1 |

The "358 with the flag" is 321 + 37 and was computed here; the.

Rates (computed here):

| | Round 6 judge run | Round 6 after Part A replay | Round 7 |
|---|---|---|---|
| discrepancies per program | 259 / 250 = 1.04 | 1.04 | 151 / 224 = 0.67 |
| tool crashes per program | 62 / 250 = 0.25 | 0.25 | 31 / 224 = 0.14 |
| live findings per program | 218 / 250 = 0.87 | 194 / 250 = 0.78 | 107 / 224 = 0.48; without `only_pyright` 88 / 224 = 0.39 |
| programs with a live finding | 127 / 250 = 50.8 % | 110 / 250 = 44.0 % | 68 / 224 = 30.4 %; without `only_pyright` 60 / 224 = 26.8 % |
| share auto-closed | 103 / 321 = 32.1 % | 127 / 321 = 39.6 % | 75 / 182 = 41.2 % |

The live rate fell from 0.78 (Round 6 on today's KB) to 0.39 per program (comparable count). Two things moved it: the mix (no `C_callback`, which gave 65 live findings on Round 6; only 40 crash-family programs, almost all closed) and the KB. The replay the Round-7 programs on the Round-6 KB or the Round-6 mix on the Round-7 programs, so I cannot say how much each contributed.

Round 7 dismissed by category: DUPLICATE 37, DESIGN_DIVERGENCE 28, SPEC_AMBIGUITY 7, KNOWN_LIMITATION 3. By entry: `rule:crash:signal` 30, LITERAL-WIDENING 13, BOTH-GRADUAL 7, UPSTREAM-TY-4212 4, PRECISION-RUNTIME-CONSISTENT 4, UPSTREAM-MYPY-22339 3, UPSTREAM-TY-4756 3, INFERENCE-DOWNSTREAM 3, JOIN-VS-UNION 3, MYPY-SKIPS-UNREACHABLE 2, ASSERT-TYPE-LITERAL-RETENTION 2, UPSTREAM-TY-2792-READONLY 1. None of the new TY-2171 / TY-2792 entries except the READONLY one fired on a Round-7 program.

Auto-closed crashes: 30, by closing reference MYPY-22361 13, TY-4148 13, TY-4898 3, TY-4882 1. The 31 crash events are these 30 plus one live pyright `RangeError`. Round 6 live crash findings were 23 (ty overflow 20, pyright 2, mypy SIGKILL 1); Round 7 has 1.

Live by kind (Round 7): reveal_mismatch 43, only_mypy 23, only_pyright 19, only_ty 14, concern_mismatch 7, crash 1.

Strong runtime evidence on a live finding: 5 findings (3 `partial_unpack_exception`, the pyright `RangeError`, the `readonly_prop_never` mutant). Round 6 had 47 programs with strong evidence on a live finding, a different unit (programs, not findings), and most of those were already-known families; I did not recompute the Round-7 figure per program.

## 3. Per group

The Round 6 table groups by generation group with discrepancies and crash events per group. Round 7 recorded live, dismissed and crash events per parent, not discrepancies. The discrepancy column is findings minus crash events (consistent with the totals: 151 = 182 - 31). Columns for programs with a live finding and programs with strong evidence per group were not captured, so they are left out.

| Group | Programs | Discrepancies (derived) | Crash events | Live | Dismissed |
|---|---|---|---|---|---|
| A_ty_4148 (3 parents) | 15 | 0 | 26 | 0 | 26 |
| A_ty_paramspec (2 parents) | 14 | 19 | 3 | 18 | 4 |
| A_ty_protocol_capped (1 parent) | 3 | 1 | 1 | 0 | 2 |
| P_pyright (5 parents) | 30 | 30 | 1 | 19 | 12 |
| N_seeds (9 seed mutants, 6 each) | 54 | 48 | 0 | 38 | 10 |
| fresh (areas incl. 70 `--n 10`, 8 recursive_aliases, others) | 108 | 53 | 0 | 32 | 21 |
| total | 224 | 151 | 31 | 107 | 75 |

Group notes: TY-4148 trio produced no live finding at all. In the paramspec pair, `self_annotated_dunder_call` gave 16 live / 1 dismissed and `identity_applied_to_itself` 2 live / 3 dismissed. `P_pyright`: `d5p_*_rangeerror` 6 and 2 live, `d3p_descriptors_decorated_get` 5, `d3p_generics_callable_attr_contravariant` 5, `d4p_descriptors_readonly_prop_never` 1. `N_seeds` live: overloaded_post_init 11, class_sequence_patterns 13, readonly_notrequired 6, variadic_tuples 3, partial_unpack_exception 3, kw_only_initvar_order 2; dataclass_transform, final_overrides and literal_flag_overload 0. These are live findings, not programs.

Crash-yield check from the plan: of the 29 `A_ty_4148` / `A_ty_paramspec` programs, 0 have a live ty crash finding (all ty crashes are closed by TY-4148, TY-4898, TY-4882). The plan said to move unspent crash budget if fewer than 3 did; there was none to move, since all 40 crash-family programs were generated in pass 1.

## 4. What Part A changed

The Round-6 report left about 19 known-duplicate findings live because two calibration programs were pinned as "must stay live". Part A turned that rule into narrow entries with tests.

* Replay of the 250 Round-6 reports (`kbloop_replay.py <out-dir> ... --verify-sample 30`, 30/30 identical): 321 findings compared, **19 changed**, all `review/gate` to `dismissed/DUPLICATE` except one `LITERAL-WIDENING` to `UPSTREAM-TY-2171`. By entry: TY-2792 8, TY-2792-READONLY 4, TY-2171 4, TY-2171-ASSERT 3.
* Live 212 to 194, dismissed 109 to 127, programs with a live finding 122 to 110.
* Controls: all 19 programs were read in full and every one is a member of the family. Eleven findings in the same families stay live on purpose (module-level helper changes the receiver; narrowing on a different attribute; other bugs). Replays of Rounds 3, 4 and 5 closed 36 rows (TY-2792 17, TY-2171 11, TY-2171-ASSERT 6, TY-2792-READONLY 2); every row was read and belongs to the two families. Draft 2 (alias, then a store at the end of the loop) is not closed.
* Effect on Round 7 itself: only one finding was closed by these entries (UPSTREAM-TY-2792-READONLY 1). The 19 were Round-6 shapes; the Round-7 mix has few of them.
* Tests: 479 passed after Part A (426 + 53). The two tests that pinned the calibration programs as "no dismissal may touch" now assert that every finding is DISMISSED by exactly the named entry.

## 5. What Part B changed (`only_pyright`)

Before, a pyright error that mypy and ty both missed could not become a finding. The opt-in kind `only_pyright` (`--pyright-only`) adds it.

* Round-6 replay, flag off: 321 findings, **0 changed** against the Part A replay. Flag on: the same 321 unchanged and **37 added** `only_pyright` findings in 23 programs; 0 `runtime_supports`, 37 `runtime_contradicts`, all `review/gate`. Live 194 to 231, programs with a live finding 110 to 123.
* Round-7 judge run: 19 live `only_pyright` findings in 12 programs, all `RUNTIME/weak ... supports neutral`; 0 `runtime_supports`. The branch that raises confidence when the runtime agrees with pyright has still not been seen on real data.
* Disposition of the Round-7 `only_pyright` findings (verification section 3, D7-4): 1 is a duplicate of pyright#11382 (`Gauge.level`), 10 findings in 6 programs share the self-parameter cause of draft 7, 6 findings in 3 programs belong to the ParamSpec self-annotated `__call__` family (not analysed), 2 fresh programs were not analysed. That is 19 in total as read in the verification file (1 + 10 + 6 + 2).
* `kbloop_stats.py` prints "live without only_pyright" so counts stay comparable with Rounds 1 to 6. On the Round-6 replay that line equals the flag-off run (194 / 110).

The `only_pyright` kind found one real new bug in Round 7 (draft 7, pyright `RangeError`, which is a crash and would have been found without the flag) and one duplicate. It has produced no new type-error bug of its own yet.

## 6. Yield in the new no-hit areas

Areas with no parent in `seeds/parents/` before Round 7: typeddict, overloads, match_statement, dataclasses, final_classvar, abstract_classes, tuples_unpacking. Figures per area directory (fresh and seed mutants together); live and dismissed are findings, not programs.

| Area | Programs | Live | Dismissed | Live per program | Strong |
|---|---|---|---|---|---|
| match_statement | 16 | 21 | 2 | 1.31 | 0 |
| typeddict | 16 | 8 | 8 | 0.50 | 0 |
| dataclasses | 28 | 13 | 0 | 0.46 | 0 |
| overloads | 16 | 6 | 3 | 0.38 | 0 |
| tuples_unpacking | 22 | 7 | 14 | 0.32 | 3 |
| abstract_classes | 10 | 2 | 1 | 0.20 | 0 |
| final_classvar | 16 | 0 | 1 | 0.00 | 0 |
| total | 124 | 57 | 29 | 0.46 | 3 |

Of the 107 live findings, 57 come from these areas. Only tuples_unpacking produced strong evidence (the `partial_unpack_exception` mutants). Live-per-program is a count of triage items, not of bugs: several of the match_statement and dataclasses items are display differences or correct mypy errors on mutants with wrong types (verification section 4). The one new bug from these areas is draft 6.

## 7. Candidates from Part D and verdicts

All run with the pins plus ty 0.0.98, mypy 2.4.1 and master, pyright 1.1.414 (latest).

| Id | Candidate | Verdict |
|---|---|---|
| D7-1 | ty (and pyright) reveal the old value in an `except` after a nested unpacking assignment failed half-way. CPython `'bad'`, ty 0.0.97 / 0.0.98 `Literal[1]`, mypy `int \| str` | STILL-BUG-NEW (ty), draft 6, confidence 0.5. Pyright shows `Literal[1]` for every variant, so it is not drafted |
| D7-2 | pyright `RangeError: Maximum call stack size exceeded` on a decorated descriptor `__get__` (exit 2 on 1.1.414); ty and mypy do not crash | STILL-BUG-NEW (pyright), draft 7, confidence 0.8. Not pyright#11961 / PR #11965 (different code path) |
| D7-3 | ty skips the read-only property assignment after a descriptor `__set__` | DUPLICATE ty#2792 |
| D7-4 | pyright `Clamped \| int` for a class-level data descriptor assigned in `__init__` | DUPLICATE pyright#11382 |
| D7-5 | ty `object + object` after `case (a, b)` with a non-final class in the subject | NOT-A-BUG (ty#1578 closed not planned; `@final` removes it) |
| H1 | mypy accepts a class with `__eq__` and no `__hash__` as `Hashable` (Round-6 candidate 1) | DUPLICATE python/mypy#2455 and #18622; open PR #19168 is the fix. This replaces the Round-6 "no duplicate found" |

Round 6 candidates 2 to 5 (ty recursive alias solution, mypy memory blow-up, pyright `RangeError`, new shapes for draft 1) were not re-examined except the pyright `RangeError`, which is now D7-2 with a reduction. Drafts 6 and 7 were appended to `results/bugs.md` with `<PLAYGROUND LINK>` placeholders. Nothing is filed.

Parents: promoted 1 (`d7p_tuples_unpacking_partial_unpack_except_ty.py`, highest similarity to any hit 0.43), retired 4 (TY-4148 trio and the TY-4882 protocol parent, all their findings dismissed). Hits: 45 before Part C, **42** after (`check_hits.py 0.80`: 42 files, 0 problems). Not promoted: the pyright `RangeError` mutant (same root cause as the two `d5p_*` parents) and the `readonly_prop_never` mutant.

## 8. Remaining weaknesses

* The ParamSpec `self_annotated_dunder_call` family gave 16 of the 107 live findings and is still unanalysed (neighbourhood of TY-4899). It is now the largest single live source after the new areas.
* `runtime_supports` for `only_pyright` has never fired on real data (0 of 19 on Round 7, 0 of 37 on the Round-6 replay). Whether the 0.7 weighting is right is untested.
* Closing a crash still needs a source-shape predicate; the TY-4148, MYPY-22361 and TY-4882 entries closed 30 of 31 crash events here, but the draft-1 expanding-receiver overflow (20 live crashes on Round 6) has no entry, and its parents were excluded from generation, so Round 7 says nothing about it.
* D7-3, D7-4 and H1 are duplicates that the KB does not close (no matcher for descriptor stores; single-tool findings are not covered by the dismissal rules). They will reappear live.
* The 26-program pass-2 reserve was not generated; the run is 224 of the 250 target. Only one program qualified as a parent.
* The runtime-evidence rule's artefacts from Round 5 and 6 (`...` read as variadic tuple; `runtime_miss` anchored on the wrong frame) are unchanged.
* Verification relied on `gh search`, which matches words, not meaning. "No duplicate" for D7-1 means two rounds of 8 and 10 term sets, for D7-2 9 term sets, with nothing matching.

## 9. Not verified

* Drafts 6 and 7 on a playground (placeholders open). No playground (ty, mypy, pyright) was used.
* ty `main`, pyright `main`, and pyright with PR #11965 applied; no such build was made.
* Pyright's reason for `Literal[1]` in D7-1 (my reading that `except` links only after call nodes was not checked in the source).
* The 6 `only_pyright` findings in the ParamSpec family, 2 fresh `only_pyright` programs (`4a2a192556ca`, `81f56b3b025b`), and 9 of the 10 decorated-descriptor `only_pyright` findings (only `seed-3c7159d68626` was checked).
* How much of the live-rate drop is KB versus generation mix (section 2).
* Strong-evidence program counts for Round 7 and per-group "programs with a live finding" (not captured).
* Quality of the 224 generated programs beyond the preflight and the triage read; the generator ran at `medium` effort, confirmed in 45 of 46 sessions.
* Round-6 candidates 2 (ty recursive alias solution) and 3 (mypy memory blow-up) were not revisited.
