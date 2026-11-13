# Day 10 report (pipeline fix, least-used operators and areas, generation, judge, morning decisions, verification)

> Paths written as `[campaign working file]`, `[run output]` or `[agent working file]` point to scratch files of the original campaign that are not part of this repository.

Branch [campaign working file], local only. Nothing was pushed; no issue, PR or comment was written on GitHub. The run log and verification file record only read-only `gh search issues|prs`, `gh issue view`, `gh release list`, an author listing, and web fetches (mypy docs, a ty test file). This report step added read-only `gh issue view` (24 issues), `gh pr view` (ruff#30074), one `gh api .../timeline` read and one author listing ([campaign working file], `gh_pr_30074.out`, `gh_events_4934.out`, `author.out`). No pin was changed (`phase7/results/pins.out`: Python 3.13.16, ty 0.0.97, mypy 2.4.0, pyright 1.1.414).

Every number below was read from [campaign working file], [campaign working file], [campaign working file], [campaign working file], [campaign working file], [campaign working file], [campaign working file] or from [campaign working file] (produced for this report from the saved [run output] JSON and the replays saved by phase 5 in [run output]; the generation and the judge were not re-run). Day 9 figures come from `results/days/day9-report.md` and [campaign working file]. Rates were computed here from those counts ([campaign working file], output `phase7/results/calc.out`); where a figure was not captured I say so.

Pins: mypy 2.4.0, ty 0.0.97, pyright 1.1.414, CPython 3.13.16, target Python 3.13. Same as Day 9. ty 0.0.99 (still the newest release on 2026-11-06 per `gh release list`), mypy 2.4.1 and mypy master 2.5.0+dev.879da562 were used for verification only ([campaign working file] section 1).

Day 9 vs Day 10 is not like for like. Both runs have 250 programs and both judge runs used `--pyright-only`, so "live without `only_pyright`" is the count comparable to Days 1 to 6. The KB changed twice between the runs (section 4), and the generation mix changed on purpose (eight least-used operators, 10 crash-family programs instead of 22, five areas with no program, section 3). To separate the KB effect, the Day 9 reports were re-judged on the final Day-10 KB (section 2, middle columns).

## 1. What was run

| Phase | What | Result |
|---|---|---|
| 1 (`63cd5b2`) | Pipeline: KB entry `TY-CONTEXTMANAGER-ITERATOR-DEPRECATED` (ty `deprecated` on `@contextmanager` / `@asynccontextmanager` with an `Iterator` return) | 688 passed (655 + 33), 20 PASS / 0 FAIL, `check_hits.py 0.80` 40 files / 0 problems; replay of Day 9: 25 findings changed, live 224 to 199 |
| 2 (`e00125d`) | Morning plan [campaign working file]: crash probe of 60 ty targets, 1 parent promoted, 2 retired, plan for 250 programs, scripts [campaign working file], dry run | `pending=250 written=0`; 250 distinct prompt keys, 0 shared with Days 3 to 9; [run output] 40 to 39 |
| 3 (`c0e6f01`) | [campaign working file] 0 / 1, 50 headless worker sessions (`claude-haiku-5.5`) | `pending=0 written=250`; `inbox_check.py`: `prompts=250 (retry prompts=0) answers=250 answered=250 pending=0 orphan_answers=0 malformed_keys=0` |
| 4 (`550c478`) | Judge `kbloop_run.py ... --jobs 14 --pyright-only`, `TYPEDIFF_LLM=null` | `250/250 ok`, 75 s, rc 0 |
| 5 (`334ff8c`) | Morning decisions on parents and KB | 0 promoted, 3 retired ([run output] 39 to 36), 1 KB entry `MYPY-8595-METACLASS-CALL`, 42 tests, 730 passed |
| 6 (`c6c5a9a`) | Verification: 10 strong programs plus 3 extra groups (13 rows) | STILL-BUG-NEW 2 (drafts 11 and 12), DUPLICATE 6, NOT-A-BUG 5 |
| 7 | This report and `results/FINAL-SUMMARY.md` | section 9 |

Generator model: 50 worker sessions, all `modelId claude-haiku-5.5`; `effortLevel medium` in 48, no `effortLevel` field in 2 (`sess_10b72232`, `sess_968d74ee`; Day 9: 49 of 50). 0 sessions mention Opus, `gpt-*` or `sol-5.6` (`check_gen_sessions.py`, run log Phase 3 item 5).

Operator check before the judge (run log Phase 3 item 4): the two instruction operators in `H_new` (12 programs): 8 define `__exit__` or `__aexit__`, 6 have an annotation-only or instance-assigned dunder (regex heuristics). The eight bare-name operators have no instruction to check, so `parent_similarity.py` measured the distance from each mutant to its parent: below 0.80 in 124 of 127 mutants outside `R_reserve` and in 16 of 24 reserve mutants (140 of 151). This measures that the program changed, not that the named operator was applied.

Memory: lowest `MemAvailable` during the judge run 7,017,424 kB (6.69 GiB; Day 9: 7.65 GiB, Day 8: 9.40 GiB), no oom-kill line in `journalctl`. `--jobs 14` was kept.

## 2. Funnel, Day 9 vs Day 10

| | Day 9 judge run | Day 9 reports on the final Day-10 KB | Day 10 judge run | Day 10 reports on the final KB |
|---|---|---|---|---|
| programs | 250 | 250 | 250 | 250 |
| discrepancies | 335 | 335 | 247 | 247 |
| tool crash events | 4 | 4 | 0 | 0 |
| findings (live + dismissed) | 339 | 339 | 247 | 247 |
| auto-closed | 115 | 141 | 75 | 79 |
| live | 224 | 198 | 172 | 168 |
| live without `only_pyright` | 180 | 154 | 142 | 138 |
| programs with a live finding | 129 | 113 | 101 | 99 |
| ... without `only_pyright` | 103 | 87 | 91 | 89 |
| live crash findings | 0 | 0 | 0 | 0 |
| strong-evidence live findings | 10 (8 programs) | n/r | 11 (10 programs) | 8 (`group_yield_replayed.out`) |

Sources: Day 9 judge column [campaign working file] and `day9-report.md` section 2. Day 9 on the final KB: `phase7/results/stats_replayed_day9.out` (the Day-9 reports replayed by phase 5: 25 changed by `TY-CONTEXTMANAGER-ITERATOR-DEPRECATED` in phase 1, 1 more by `MYPY-8595-METACLASS-CALL` in phase 5, live 224 to 199 to 198; the stats file shows 25 `CONFIG_ARTIFACT` and 1 `MYPY-8595` dismissal). Day 10 judge column [campaign working file]. Day 10 final KB: `phase7/results/stats_replayed.out` (phase 5 replay: 4 changed, all by `MYPY-8595-METACLASS-CALL`, live 172 to 168). The `[all]` and `[tuning]` blocks of the stats files are identical; `[holdout]` has 0 programs. n/r = not recorded (the per-program count of strong evidence was not computed for the replays).

Rates (computed here):

| | Day 9 judge | Day 9 on final KB | Day 10 judge | Day 10 on final KB |
|---|---|---|---|---|
| discrepancies per program | 335 / 250 = 1.34 | 1.34 | 247 / 250 = 0.99 | 0.99 |
| tool crashes per program | 4 / 250 = 0.02 | 0.02 | 0 | 0 |
| live findings per program | 224 / 250 = 0.90 | 198 / 250 = 0.79 | 172 / 250 = 0.69 | 168 / 250 = 0.67 |
| live per program without `only_pyright` | 180 / 250 = 0.72 | 154 / 250 = 0.62 | 142 / 250 = 0.57 | 138 / 250 = 0.55 |
| programs with a live finding | 129 / 250 = 51.6 % | 113 / 250 = 45.2 % | 101 / 250 = 40.4 % | 99 / 250 = 39.6 % |
| ... without `only_pyright` | 103 / 250 = 41.2 % | 87 / 250 = 34.8 % | 91 / 250 = 36.4 % | 89 / 250 = 35.6 % |
| share auto-closed | 115 / 339 = 33.9 % | 141 / 339 = 41.6 % | 75 / 247 = 30.4 % | 79 / 247 = 32.0 % |

Reading: on the same KB the live rate fell from 0.79 to 0.67 per program (0.62 to 0.55 without `only_pyright`). The KB change alone moves the Day-9 reports from 0.90 to 0.79, so about half of the drop between the two judge runs (0.90 to 0.69) is the entry that closed 25 rows and the other half is the Day-10 programs. I did not run the Day-10 programs on the Day-9 KB and did not split the remainder by operator, so I cannot say how much of the 0.79 to 0.67 comes from the mix. For scale, the same reports re-judged on the final KB give 0.61 for Day 8 (152 / 250; 0.53 without `only_pyright`) and 0.33 for Day 7 (75 / 224; 0.28 without), from `stats_replayed_day8.out` and `stats_replayed_day7.out`.

Day 10 dismissed by category ([campaign working file], judge run): DESIGN_DIVERGENCE 47, CONFIG_ARTIFACT 12, DUPLICATE 9, NOISE 6, KNOWN_LIMITATION 1 (Day 9: DESIGN_DIVERGENCE 96, DUPLICATE 10, KNOWN_LIMITATION 6, NOISE 2, SPEC_AMBIGUITY 1). By entry: PRECISION-RUNTIME-CONSISTENT 22, LITERAL-WIDENING 14, TY-CONTEXTMANAGER-ITERATOR-DEPRECATED 12, DISPLAY-EQUIVALENT 6, ASSERT-TYPE-LITERAL-RETENTION 5, UPSTREAM-TY-876 5, UPSTREAM-TY-4212 4, UPSTREAM-MYPY-22339 2, UPSTREAM-MYPY-21937-REVEAL 2, MYPY-SKIPS-UNREACHABLE 1, TY-SELF-UPPER-BOUND 1, JOIN-VS-UNION 1. On the final KB the list gains MYPY-8595-METACLASS-CALL 4 (KNOWN_LIMITATION 1 to 5, dismissed 75 to 79). No crash closure: the Day-10 run had 0 tool crash events, so the crash entries (TY-4148, TY-4898, MYPY-22360 and others) fired 0 times, against 4 on Day 9 and 15 on Day 8.

Live by kind, Day 9 judge, Day 10 judge, Day 10 final KB: reveal_mismatch 48 / 55 / 53, only_mypy 45 / 37 / 36, only_pyright 44 / 30 / 30, only_ty 69 / 40 / 39, reveal_unpaired 12 / 5 / 5, concern_mismatch 2 / 4 / 4, runtime_miss 4 / 1 / 1, crash 0 / 0 / 0. The Day-9 reports on the final KB have only_ty 44, so the fall in `only_ty` from 69 to 40 is 25 rows of the new entry plus 4 rows of Day-10 differences. `TY-CONTEXTMANAGER-ITERATOR-DEPRECATED` closed 12 of the 75 Day-10 dismissals (16.0 %); it is the third most frequent entry.

`only_pyright` runtime relations ([campaign working file]): 30 findings, `runtime_supports` 13, `runtime_contradicts` 17 (Day 9: 22 / 22 of 44). All 13 supports rows are tier `review`, confidence 0.7, source `gate`, in 10 programs. Their verdicts are in section 5 (D10-12): 9 are draft 10, 3 are the documented dunder trade-off, 1 follows a decorator error that all tools report. 0 of the 30 have strong bug evidence.

Strong runtime evidence on a live finding (judge run): 11 findings in 10 programs (10 `RUNTIME/strong`, 1 `SELF_CONTRADICTION/strong`). Verdicts in section 5: 0 new bugs by themselves (5 duplicates, 4 not-a-bug, 1 mixed that gave draft 12).

## 3. Per group and per area

Day 10 groups are the subdirectories of [run output] that hold a mutant's parent ([campaign working file]), plus `fresh` for programs without `__mut` in the name. They differ from the Day-9 groups, so there is no row-by-row comparison. The columns are `phase7/results/group_yield.out` (script [campaign working file], adapted from the Day-9 one; the totals 250 / 101 / 247 / 172 / 11 / 75 / 0 equal [campaign working file]). Unlike Day 9, the discrepancy column is read from each report's `discrepancies` list, not derived. "Live" and "strong" are findings, not programs. These are judge-run figures (before `MYPY-8595-METACLASS-CALL`); the replay changes only `N_class` (live 9 to 7, strong 2 to 0) and `fresh` (live 43 to 41, strong 2 to 1). Live per program is computed here.

| Group (operators, parents) | Programs | Programs with a live finding | Discrepancies | Crash events | Live | Strong | Dismissed | Live per program |
|---|---|---|---|---|---|---|---|---|
| C_pyright_range (crash family: `scope_relocation` 2, `descriptor_property`, `decorator_wrapping`, `union_widen`, `gradual_injection`; 1) | 6 | 4 | 6 | 0 | 6 | 0 | 0 | 1.00 |
| C_tvt (crash family: `generic_nesting` 2, `union_widen`, `gradual_injection`; 1) | 4 | 4 | 15 | 0 | 15 | 2 | 0 | 3.75 |
| H_new (`exit_swallow_flip` 6, `dunder_instance_shadow` 6; 2) | 12 | 9 | 33 | 0 | 17 | 0 | 16 | 1.42 |
| N_class (`inheritance_diamond` 16, `descriptor_property` 8; 8) | 24 | 6 | 10 | 0 | 9 | 2 | 1 | 0.38 |
| N_flow (`scope_relocation` 16, `gradual_injection` 8; 8) | 24 | 12 | 39 | 0 | 25 | 2 | 14 | 1.04 |
| N_types (`literal_injection` 16, `union_widen` 8; 8) | 24 | 6 | 20 | 0 | 7 | 1 | 13 | 0.29 |
| N_wrap (`generic_nesting` 16, `decorator_wrapping` 8; 8) | 24 | 7 | 12 | 0 | 9 | 1 | 3 | 0.38 |
| O_overload (`overload_reorder`; 3) | 9 | 9 | 11 | 0 | 11 | 1 | 0 | 1.22 |
| R_reserve (`scope_relocation`, `union_widen`, `literal_injection`, `gradual_injection`, 6 each; 6) | 24 | 17 | 31 | 0 | 30 | 0 | 1 | 1.25 |
| fresh (no operator) | 99 | 27 | 70 | 0 | 43 | 2 | 27 | 0.43 |
| total | 250 | 101 | 247 | 0 | 172 | 11 | 75 | 0.69 |

Group notes (`group_yield.out`, live by kind per group, run log Phase 5):

* The four `N_*` groups (the eight least-used operators, 96 programs): 50 live, 0.52 per program, 6 strong. Fresh programs gave 0.43. `N_flow` is the best (1.04: reveal_mismatch 12, only_mypy 8, only_ty 4, reveal_unpaired 1); `N_types` the worst (0.29, with 13 dismissed). The strong rows of these groups were all rediscoveries or not-a-bug (section 5): `N_class` 2 (D10-2), `N_flow` 2 (D10-3, D10-5), `N_types` 1 (D10-10, which gave draft 12), `N_wrap` 1 (D10-9).
* `C_tvt` has the highest rate (3.75) from a parent that was retired in phase 5: its 2 strong rows are D10-6 and D10-8 (the TypeVarTuple-default `TypeError`, python/typing#2211). `C_pyright_range`: 6 live (only_pyright 4, reveal_mismatch 2), 0 pyright `RangeError`.
* `H_new` (second round of the two Day-9 instruction operators on the two promoted parents): 17 live (only_pyright 12, only_ty 3, only_mypy 2), 16 dismissed, 0 strong. 12 of the 17 live are `only_pyright`. Several `runtime_supports` rows of D10-12 sit in this group (mutants of `d9p_context_managers_swallowed_name_possibly_unbound` and of `d8p_dunder_dispatch_annotation_only_call`); the split of the 13 rows by group was not computed.
* `R_reserve` (parents chosen because they had a live finding on Day 9, so a high rate is expected): 1.25 per program (Day 9: 1.42, Day 8: 1.50). Draft 11 came from this group (parent `rsv_generics_variance_3c28536f`).
* `O_overload`: 11 live in 9 programs (only_mypy 8), 1 strong (D10-4, not a bug).
* Per parent (`group_yield.out`, "per parent / fresh"): `d9p_context_managers_swallowed_name_possibly_unbound` 13 live / 10 dismissed in 6 programs; `d3p_typevartuple_unpack_paramspec_default_after_tvt` 15 live in 4; `s3r1_ty_type_equality_narrowing_any` 10 live in 3; `rsv_generics_variance_3c28536f` 12 live in 4; `d3p_generics_callable_attr_contravariant` 0 live, 4 dismissed in 3 (the revisit test, section 6).

Per area (the `# area:` line of each program; [campaign working file] for programs, programs with live, live, live without `only_pyright`; discrepancies, strong and dismissed from the "per area dir" block of `group_yield.out`; live per program computed here):

| Area | Programs | With live | Live | Live without `only_pyright` | Live per program | Strong | Dismissed |
|---|---|---|---|---|---|---|---|
| context_managers | 32 | 12 | 22 | 8 | 0.69 | 0 | 20 |
| dunder_dispatch | 14 | 11 | 18 | 15 | 1.29 | 0 | 6 |
| typevartuple_unpack | 7 | 5 | 16 | 16 | 2.29 | 2 | 8 |
| generics_variance | 14 | 7 | 15 | 15 | 1.07 | 0 | 5 |
| narrowing_user | 16 | 7 | 15 | 15 | 0.94 | 1 | 7 |
| overloads | 17 | 11 | 15 | 14 | 0.88 | 1 | 2 |
| callables | 17 | 8 | 12 | 12 | 0.71 | 0 | 2 |
| abstract_classes | 18 | 6 | 11 | 6 | 0.61 | 1 | 0 |
| typeddict | 15 | 8 | 11 | 8 | 0.73 | 1 | 9 |
| narrowing_builtin | 3 | 3 | 7 | 7 | 2.33 | 0 | 0 |
| paramspec_concatenate | 19 | 6 | 7 | 7 | 0.37 | 1 | 1 |
| descriptors_properties | 6 | 4 | 6 | 2 | 1.00 | 0 | 0 |
| gradual_any | 18 | 5 | 5 | 5 | 0.28 | 0 | 0 |
| constructors_metaclasses | 8 | 2 | 4 | 4 | 0.50 | 3 | 6 |
| enums_literals | 3 | 2 | 3 | 3 | 1.00 | 1 | 7 |
| self_classmethods | 11 | 3 | 3 | 3 | 0.27 | 0 | 1 |
| inheritance_mro | 14 | 1 | 2 | 2 | 0.14 | 0 | 0 |
| final_classvar | 14 | 0 | 0 | 0 | 0.00 | 0 | 1 |
| protocols | 4 | 0 | 0 | 0 | 0.00 | 0 | 0 |
| total | 250 | 101 | 172 | 142 | 0.69 | 11 | 75 |

The two newest areas (`context_managers`, `dunder_dispatch`): 46 programs, 40 live (23.3 % of the 172, computed here), 23 programs with a live finding, 26 dismissed, 0 strong. Day 9 had 50 programs, 48 live in the same two areas (0.96 per program; Day 10 0.87). `context_managers` has 20 dismissed findings next to its 22 live ones; the `deprecated` entry closed 12 of the 75 Day-10 dismissals, but how many of those 12 are in this area was not computed. `final_classvar` (14 programs) and `protocols` (4) gave 0 live findings; `inheritance_mro` 2 in 14 and `self_classmethods` 3 in 11 are also near zero. Five areas had no fresh program by plan (`match_statement`, `recursive_aliases`, `dataclasses`, `tuples_unpacking`, `async_generators`; [campaign working file] section 3), so the Day-8 large sources `recursive_aliases` and `match_statement` were not sampled (`match_statement`, `recursive_aliases` and `dataclasses` also had 0 programs on Day 9, so this is the second day in a row for those three).

## 4. What changed since Day 9

Code and KB (all in `typediff/kb.py`; `known_upstream.json` is unchanged since the Day 9 commit `42a7af8`: 39 entries, 7 prior stances):

* **`TY-CONTEXTMANAGER-ITERATOR-DEPRECATED`** (commit `63cd5b2`; `CONFIG_ARTIFACT`, `auto`, `runtime_override=False`). It targets the Day-9 weakness "25 of 224 live findings are one ty `deprecated` warning". The cause was read, not guessed: the typeshed bundled with mypy 2.4.0 has no `@deprecated` marker on the `Iterator` overload of `contextmanager`, and ty 0.0.97 reports the newer stub's marker (`.venv/.../mypy/typeshed/stdlib/contextlib.pyi` line 87; same wording as pyright#11402). The matcher fires only when every ty diagnostic of the discrepancy has code `deprecated` and exactly the stub's message for `contextmanager` / `asynccontextmanager`, the statement is a `def` whose decorator list holds the decorator the message names on the line ty reported, and the return annotation is a subscript of `Iterator` (or `AsyncIterator` for `asynccontextmanager`). A user `@deprecated` function is not closed. Effect: **25 Day-9 rows closed** (replay of the 250 reports, 339 findings compared, 25 changed, all `review/gate` to dismissed, live 224 to 199, 30/30 identical in the verify sample), **12 Day-10 rows closed** in the judge run itself. Day 8 replay: 0 changed; Day 7: 0 by this entry; Day 5: 0 by this entry, with 2 of 30 verify-sample mismatches caused by 5-day-old saved tool output (not a clean replay, not chased). 33 tests (`tests/test_day10_pipeline.py`: 10 positives, controls that stay live, entry schema, 3 real-tools tests).
* **`MYPY-8595-METACLASS-CALL`** (commit `334ff8c`; `KNOWN_LIMITATION`, `auto`, `runtime_override=False`). python/mypy#8595 "Metaclass __call__ ignores return type" is closed with the maintainer comment "unlikely this will be ever supported"; #14122 is the open feature request. The matcher fires when the statement reaches a class whose metaclass `__call__` is annotated with a type that does not mention the class (not `Any`, `Self`, a TypeVar) and the tools differ in exactly that way (`reveal_mismatch` with mypy giving the class, `only_mypy` with only `[assert-type]`, `only_ty` with only invalid return / assignment / argument naming the class and the annotation). Effect: **4 Day-10 rows closed** (replay: 247 compared, 4 changed, live 172 to 168), **1 Day-9 row** (199 to 198), 0 on Day 8 and Day 7. It was added after the judge run, so the Day-10 judge numbers do not include it. 42 tests (`tests/test_day10_morning.py`: 9 positives, controls, schema, 2 real-tools tests).
* Tests 655 to 730 (+33 +42); `kb-selftest` stays at 20 entries (neither new entry has an `example`; the real-tools tests cover them). `kb.py` has 47 `KBEntry(` occurrences at the Day-9 report commit and 49 at HEAD.
* Not added on purpose: an entry for mypy's "Can only replace ParamSpec .." message (3 live rows of 172; the message also fires for programs whose parameter list is wrong, and its parent was retired).

Day-9 weaknesses (`day9-report.md` section 7) and their state:

| Day-9 weakness | State on Day 10 |
|---|---|
| ty `deprecated` on `@contextmanager`: 25 of 224 live findings, no rule | fixed (`63cd5b2`): 25 closed on Day 9 reports, 12 on Day 10 |
| `runtime_supports` for `only_pyright` cannot tell a documented trade-off from a defect (20 of 22 rows were non-bugs) | unchanged. Day 10: 13 rows, 9 are draft 10 (a real mypy gap at confidence 0.4), 3 the trade-off, 1 a cascade. No rule distinguishes them |
| queued matchers `TY-NONFINAL-PATTERN`, `ASSERT-NEVER-ALL-REJECT`, wider `JOIN-VS-UNION`, `MYPY-8595` | `MYPY-8595` done; the other three still not implemented; D10-4 is another instance of `ASSERT-NEVER-ALL-REJECT`'s family |
| new operators checked by regex only | partly: `parent_similarity.py` now measures distance for the eight bare-name operators (140 of 151 mutants changed by more than 0.20), but "the operator was applied" is still not measured |
| duplicates the KB does not close reappear live | partly: mypy#8595 closed (5 rows); mypy#21937 Flag narrowing, mypy#948, python/typing#2211 and the "Can only replace ParamSpec" rows still reappear |
| drafts 6 to 10 unfiled, no playground link | drafts 6 to 9 are now filed (section 5); draft 10 and the new drafts 11 and 12 are not, and have no playground link |

## 5. Candidates and verdicts ([campaign working file])

Run with the pins plus ty 0.0.99, mypy 2.4.1 and master, pyright 1.1.414 (latest). ty 0.0.97 and 0.0.99 gave the same diagnostics in 30 of 30 reduction results, with two exceptions (the display of one `invalid-assignment` message, and one diagnostic that 0.0.99 no longer gives). The interrupted earlier run of phase 6 was re-run from scratch for all 30 programs: 30 of 30 identical to the saved summaries.

Strong-evidence programs (10 programs, 11 findings):

| Id | Candidate | Verdict |
|---|---|---|
| D10-1 | mypy reveals `Box` for `kind(n)` where the metaclass `__call__` returns `str` (`constructors_metaclasses/gen1_37b4e5f8`, fresh) | DUPLICATE python/mypy#8595 (closed 2020-03-27); open #14122 is the request. CPython, ty, pyright say `str`. Now closed by `MYPY-8595-METACLASS-CALL` |
| D10-2 | same with `-> int` (`..conformance__constructors_call_metaclass__mut1_2cca6936`, 2 strong, `N_class`) | DUPLICATE python/mypy#8595 (mypy `Bottom` and `[assert-type]` on all three versions) |
| D10-3 | mypy reveals `Literal[I.B]` for an `IntFlag` after `if c == I.A: return`, and treats the `else` of an `is` chain and `case _` over `Flag` members as unreachable (`enums_literals/d4v_ty_flag_or_else_never__mut0_d156e44d`, `N_flow`) | DUPLICATE python/mypy#21937 (open, reopened, bug); fix PR #21942 open. ty side is the Flag item of ty#876 (open) |
| D10-4 | ty reveals `Never` for `sq.area(3)` after `assert describe(3) == 4`, runtime 12 (`overloads/..overloads_definitions__mut1_59eaed87`, `O_overload`) | NOT-A-BUG (design). Not overload-specific: `def g(x: object) -> str` then `assert g(3) == 4` does the same. ty infers `str == Literal[4]` as `Literal[False]`, so the code after the assert is unreachable and every name there is `Never` with no diagnostic. Follows ty#3419 (closed completed); related open ty#4051, ty#3162. The phase-5 note that the overload order caused it was wrong |
| D10-5 | mypy narrows `type(value) == type(sample)`, ty does not (`narrowing_user/s3r1_ty_type_equality_narrowing_any__mut1_14fa674d`, `N_flow`) | NOT-A-BUG (design). The program gives the class a metaclass whose `__eq__` returns `True`; ty's own test file `narrow/type.md` documents no narrowing for this reason |
| D10-6 | `class Pair(Generic[*Ts, D])` with a defaulted `TypeVar`: CPython `TypeError`, checkers differ in wording (`typevartuple_unpack/..mut0_b16712de`, `C_tvt`) | NOT-A-BUG. All three tools report the class statement; the runtime error is expected |
| D10-7 | CPython `NameError` for `def scale(self, k) -> Shape` inside `class Shape(ABC)`; mypy silent (`abstract_classes/gen1_5c366404`, fresh) | DUPLICATE python/mypy#948 (open); related open #17610, #9932. ty and pyright are right, mypy 2.4.0, 2.4.1 and master do not report it |
| D10-8 | `class Callback[*Ts, **P = [bool]]` raises `TypeError`, no checker says so (`..paramspec_default_after_tvt__mut1_b0772641`, `C_tvt`) | DUPLICATE python/typing#2211 (open) for the runtime error; mypy's rows are draft 5 (python/mypy#22375). New variant with the same cause: `Foo[int]` on `class Foo[*Ts, **P = [float, bool]]` gives no mypy error but `foo.args()` is `tuple[()]` |
| D10-9 | `label('t2', 6)` through `@with_tag` (`Concatenate[str, P]`): `SELF_CONTRADICTION`, "mypy accepts the call" (`..generics_paramspec_components__mut0_66a0b5b8`, `N_wrap`) | NOT-A-BUG, a harness false positive. All three tools reject the call; mypy's `call-arg` on the same line was not paired with the discrepancy. mypy's wording (it names `name`, not `width`) comes from `_detect_missing_positional_arg`, a heuristic from mypy PR #20591 |
| D10-10 | `class Config(TypedDict, closed=True)` on 3.13: CPython `TypeError`, ty `unknown-argument` (`typeddict/..typedDict10__mut1_5eeeb41b`, `N_types`) | ty NOT-A-BUG (ty is right; ty#4031 closed, fixed); mypy DUPLICATE python/mypy#21747 (open); pyright **STILL-BUG-NEW, draft 12** (confidence 0.35): `closed=True` and `extra_items=int` are accepted for `pythonVersion` 3.12, 3.13, 3.14 and 3.15 |

Counts for the 10 programs (11 findings): DUPLICATE 5 (D10-1, 2, 3, 7, 8), NOT-A-BUG 4 (D10-4, 5, 6, 9), mixed 1 (D10-10). New bug by the strong row itself: 0.

Additional groups verified in phase 6:

| Id | Candidate | Verdict |
|---|---|---|
| D10-11 | 5 live `reveal_unpaired` rows with medium evidence "mypy treats reachable code as unreachable" | NOT-A-BUG. The programs use an unsound `TypeIs[list[T]]`, a `cast` followed by a contradicting `assert`, or a user `TypeIs` that lies; mypy and pyright print no reveal (unreachable) and ty prints `Never`, no tool disagrees about reachability (ty#4051, ty#3162) |
| D10-12 | 13 `only_pyright` rows with `runtime_supports` (10 programs) | 9 rows already drafted (draft 10: possibly-unbound after a `with` whose `__exit__` returns `bool`; the `async with` form was checked and needs no new draft); 3 rows NOT-A-BUG (D9-9 trade-off: `len(x)` 2, `iter(x)` 1); 1 row NOT-A-BUG (cascade of a reported decorator error) |
| D10-13 | live `only_ty` rows in `generics_variance` mutants: ty rejects `lambda x: ...` for `Sink[T]` with `def __call__(self, value: T)`, mypy is silent | ty and pyright NOT-A-BUG (right); mypy **STILL-BUG-NEW, draft 11** (confidence 0.5): mypy rejects `def named_x(x: int)` but accepts `lambda x`, `lambda x, /` and `lambda y, z=0`, and rejects `lambda *, value`; CPython raises `TypeError` for `sink(value=1)`; mypy 2.4.0, 2.4.1 and master identical |

Correction made in this step: phase 6 and draft 11 first said "21 `only_ty` rows" for D10-13. The saved reports give 3 + 3 + 4 = 10 live `only_ty` findings in the three named mutants and 12 in all four mutants of `rsv_generics_variance_3c28536f` (`phase7/results/gv_rows.out`); `ty check` prints 3, 3, 4 and 2 diagnostics for the four files (`ty_count_gv.out`). The origin of 21 is not known. The verdict rests on the hand reduction (`l1.py` to `l7.py`), not on the count. Draft 11 (text and table row), the Day-10 paragraph at the top of [campaign working file] and a note in [campaign working file] now say 10.

Totals over D10-1 to D10-13: **STILL-BUG-NEW 2** (draft 11 mypy, draft 12 pyright), DUPLICATE 6 (D10-1, 2, 3, 7, 8 and the mypy half of D10-10), NOT-A-BUG 5 (D10-4, 5, 6, 9, 11), D10-12 is the already drafted draft 10 plus the D9-9 trade-off.

What produced what:

* Neither new draft came from a strong-evidence row alone. Draft 12 came from a strong row (D10-10, `N_types`, a mutant of a harvested pyright test), but the strong discrepancy was ty's; the bug is the pyright half. Draft 11 came from a live family of `only_ty` rows in the `R_reserve` group, not from the strong set. Both have confidence below 0.6 (0.5 and 0.35).
* Net new bugs: 2 drafts (Day 9: 2, Day 8: 1, Day 7: 2). Both were appended to `results/bugs.md` with `<PLAYGROUND LINK>` placeholders. Nothing is filed by this campaign's agents.
* Filing state (author listing of the drafting account `DerekLaymn`, re-run for this report; matches the 2026-11-06 listing in the drafts file): drafts 1 to 9 are filed (ty#4933, ty#4934, mypy#22377, ty#4941, mypy#22375, ty#4958, pyright#11984, mypy#22385, mypy#22386). Draft 10 and drafts 11 and 12 are not.
* Verification effort ([campaign working file] section 4): 204 `gh search` queries (python/mypy 108, astral-sh/ty 53, microsoft/pyright 26, astral-sh/ruff 13, python/typeshed 2, python/typing 2), 23 `gh issue view` reads, 0 NOT VERIFIED after 3 retries each.

## 6. Parents and hits

Phase 2 and phase 5 (run log, `phase2/results/`, `phase5/`):

* Phase 2: **promoted 1**, `d9p_context_managers_swallowed_name_possibly_unbound` (from `gen0_b82d2e9e`, draft 10; first parent of `context_managers`, highest similarity to any hit 0.33). **Retired 2**: `d6p_typevartuple_unpack_pep695_paramspec_default_mypy_subscript` (4 mutants, 19 live, 0 strong, 0 dismissed, rediscovery of draft 5) and `d5p_descriptors_one_decorator_dunders_pyright_rangeerror` (3 mutants, 1 live row, 0 pyright crashes).
* Phase 5: 11 strong findings in 10 programs reproduced alone (10 of 10) with highest similarity to any hit 0.62, 0.52, 0.46, 0.41, 0.39, 0.38, 0.32, 0.31, 0.31, 0.27 (none at or above 0.80). **Promoted 0**. **Retired 3**: `d3p_generics_callable_attr_contravariant` (the revisit test: 3 programs, 0 live, 4 dismissed, also 0 live on Day 9), `d4v_ty_alias_loop_backedge` (3 programs, 7 live, all the parent's own mypy `[operator]` row) and `d3p_typevartuple_unpack_paramspec_default_after_tvt` (4 programs, 15 live, 2 strong, second day of rediscovery only).
* [run output]: 40 at the start of Day 10, 39 after phase 2, 36 after phase 5 (`ls [run output]` gives 36; `ls [run output]` also lists `__pycache__`, 37 entries). [run output]: 25. `check_hits.py 0.80` for this report: 36 files, 0 with problems, no near-duplicate pair (`phase7/results/hits.out`).

## 7. Weaknesses

* **No live crash findings and no crash events on Day 10.** The crash entries had nothing to do. The two crash families that were mutated (`C_pyright_range`, `C_tvt`, 10 programs) produced no pyright `RangeError` and no ty or mypy crash. The campaign's crash finds (drafts 1 and 7) came on Days 3 to 7.
* **Strong evidence did not find a new bug.** Of 10 strong programs, 5 are duplicates, 4 are not bugs, 1 is a mixed row. Three of the 10 were invalid programs or rows where the tool that disagrees with CPython is right (D10-6, D10-7, D10-10 for ty). Two harness weaknesses were found: the `SELF_CONTRADICTION` row of D10-9 fires although mypy rejects the call (mypy's `call-arg` is not paired), and the unpaired rows of D10-11 are dismissed by the KB hint but still counted as medium evidence. Neither was fixed (outside phase 6's scope).
* **Most live findings were not examined.** At most 39 of the 172 live rows were examined individually (11 strong + 5 medium + 13 `only_pyright` supports + 10 in the draft-11 family; the sets can overlap, for example the Flag program is in both the strong and the medium set; the overlap was not computed). The rest were read only as triage clusters. The largest clusters were not reduced: 28 `reveal_mismatch | uncomparable`, 30 `only_pyright` (17 `runtime_contradicts`), 12 `only_ty invalid-argument-type` from `dunder_dispatch`, 7 `only_mypy operator`, 6 `overload-cannot-match`, 4 `overload-overlap` ([campaign working file]).
* **Known duplicates the KB does not close** reappear live: mypy#21937 (Flag narrowing; a KB entry would also close the `d4v_ty_flag_or_else_never` rows), mypy#948, python/typing#2211, the 3 "Can only replace ParamSpec" rows, ty#4051 `Never` reveals.
* **Queued matchers still not implemented:** `TY-NONFINAL-PATTERN` (13 live rows of ty `callable()` narrowing in 3 Day-9 programs), `ASSERT-NEVER-ALL-REJECT`, wider `JOIN-VS-UNION`, reveal after an invalid type form, mypy `Attribute function "__call__" ... does not accept self argument` for annotation-only dunders (3 live rows).
* **The eight bare-name operators are only measured by distance.** 140 of 151 mutants are more than 0.20 away from their parent; whether `union_widen` or `gradual_injection` did what its name says is not checked. Their yield: 0.52 live per program against 0.43 for fresh programs, 0 new bugs from the strong set, 1 draft (12) from one `N_types` mutant.
* **Low-yield areas:** `final_classvar` 0 live in 14 programs, `protocols` 0 in 4, `inheritance_mro` 2 in 14, `self_classmethods` 3 in 11, `gradual_any` 5 in 18.
* **Draft 11's count was wrong in the first write-up** (21 against 10); the correction was found by re-reading the saved reports. Other counts copied from earlier phases were not all re-derived: only the 21 was checked, because it ends up in text the authors would paste.
* The `runtime_supports` rule for `only_pyright` fired on 1 of 21 `only_pyright` findings on Day 8, 22 of 44 on Day 9 and 13 of 30 on Day 10. The only real defect found among those rows is the mypy gap of draft 10.
* Day-9 and Day-10 comparison is confounded by the mix (section 2); the split was measured only for the KB side.

## 8. Not verified

* Drafts 10, 11 and 12 on a playground (placeholders open). No playground (ty, mypy, pyright) was used for any draft 3 to 12; drafts 1 and 2 were verified by the authors.
* ty `main`, pyright `main`, mypy PR branches (for example PR #21942); none was built.
* The mypy causes in D10-3, D10-9 and D10-13 (`narrow_type_by_identity_equality`, `_detect_missing_positional_arg`, `infer_lambda_type_using_context`) are read from mypy master source, not shown by instrumentation; why the callback-protocol check accepts the lambda names was not debugged.
* The origin of the number 21 in the first phase-6 text (section 5).
* 133 or more of the 172 live findings (section 7); the 12 `only_ty invalid-argument-type` rows of `dunder_dispatch`, the 28 `uncomparable` reveals, 17 of 30 `only_pyright` rows.
* Whether the eight bare-name operators applied what their names say; the Day-10 programs were not replayed on the Day-9 KB, so the mix versus KB split of the live-rate fall beyond the 25 + 1 rows is unknown.
* The effect of `MYPY-8595-METACLASS-CALL` in a fresh judge run (it was added after the judge run and measured by replay only: 4 + 1 rows).
* Day-5 replay of the `TY-CONTEXTMANAGER-ITERATOR-DEPRECATED` change (2 of 30 verify-sample mismatches from old saved tool output); Day 6, Day 3 and Day 4 were not replayed on the final KB.
* Quality of the 250 generated programs beyond the preflight, the operator checks and the triage read; the 2 sessions without an `effortLevel` field.
* The `gh` author listing shows the accounts as GitHub reports them; whether those accounts are the authors' was not checked here.
* Day-6 candidates 2 (ty recursive alias solution) and 3 (mypy memory blow-up) were not revisited.

## 9. Final checks (run for this report)

* `.venv/bin/python -m pytest tests -q` -> **730 passed** in 87.69 s, rc 0 (`phase7/results/pytest.out`).
* `.venv/bin/typediff --python-version 3.13 kb-selftest` -> **20 PASS, 0 FAIL**, rc 0 (`phase7/results/kb.out`, `kb-pass-count.out` 20, `kb-fail-count.out` 0).
* `[campaign working file] 0.80` -> 36 files; 0 with problems (`phase7/results/hits.out`).
* Files added by this step: `results/days/day10-report.md`, `results/FINAL-SUMMARY.md`, [campaign working file] (scripts [campaign working file], [campaign working file], `group_yield.py`, `gv_rows.py`, results). Edited: `results/bugs.md` (the count in draft 11, three places) and [campaign working file] (one correction paragraph). `results/days/day7-report.md` and [campaign working file] carry uncommitted edits from earlier failed runs and were left alone; untracked local files were not touched.
