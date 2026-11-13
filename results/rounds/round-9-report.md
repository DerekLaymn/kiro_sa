# Round 9 report (pipeline changes, new operators and areas, generation, judge, decisions, verification)

This report covers Round 9. The pipeline wrote nothing to GitHub: no issue, PR or comment was created, and the only GitHub access was read-only (`gh search`, `gh issue view`, `gh release list`). Counts come from the stored per-program reports and statistics of the round. Rates were computed while writing the report, and where a figure was not captured the report says so. Steps inside a round are numbered as phases: phase 1 pipeline changes, phase 2 planning (parent promotion and retirement, generation plan), phase 3 generation, phase 4 judge run, phase 5 decisions on parents and knowledge-base entries, phase 6 verification of candidates, phase 7 report.

Pins: mypy 2.4.0, ty 0.0.97, pyright 1.1.414, CPython 3.13.16, target Python 3.13. Same as Round 8. ty 0.0.99 (released 2026-11-06), mypy 2.4.1 and mypy master 2.5.0+dev.879da562 were used for verification only.

Round 8 vs Round 9 is not like for like. Both runs have 250 programs and both judge runs used `--pyright-only`, so "live without `only_pyright`" is the count comparable to Rounds 1 to 6. But the generation mix changed on purpose (two new areas, two new operators, six operators no earlier round used, 22 crash-family programs instead of 40, no program in five areas, section 3). The KB changed only by two matcher fixes (section 4); their effect on Round-8 programs is measured in section 2.

## 1. What was run

Round 9 generated 250 programs through the file bridge (`typediff --llm file:<dir> generate`), with the stand-in model `claude-haiku-5.5` at effort `medium` answering the prompts, judged them with `TYPEDIFF_LLM=null`, replayed the stored reports after each knowledge-base change, and read the remaining live findings. Pins are listed above. The counts the round relies on are in the funnel tables below. The generator used 50 model sessions (`claude-haiku-5.5`, effort `medium`). The judge run used `--jobs 14`; no out-of-memory kill occurred.

## 2. Funnel, Round 8 vs Round 9

| | Round 8 judge run | Round 8 reports replayed on the Round-9 KB | Round 9 judge run |
|---|---|---|---|
| programs | 250 | 250 | 250 |
| discrepancies | 208 | not recorded | 335 |
| tool crash events | 16 | not recorded | 4 |
| findings (live + dismissed) | 224 | 224 | 339 |
| auto-closed | 69 | 72 | 115 |
| live | 155 (135 without `only_pyright`) | 152 | 224 (180 without `only_pyright`) |
| programs with a live finding | 104 (92 without) | not recorded | 129 (103 without) |
| live crash findings | 1 | not recorded | 0 |

Sources: Round 8 column from `round-8-report.md` section 2. Middle column: Phase-1 replay (`kbloop_replay.py <out-dir> ... --pyright-only --rerun-runtime --verify-sample 30`, 30/30 identical to a full re-run): 224 findings compared, 3 changed, all `review/gate` to dismissed (`seed-9193b5cc679d` D1 and D2 by `kb:TY-SELF-UPPER-BOUND`, `seed-78dcbe5d81b6` D1 by `kb:UPSTREAM-TY-2792-READONLY`), live 155 to 152. Round 9: from the stats of the judge run. The 339 is 224 + 115 and the 72 is 69 + 3, both computed here. The discrepancy figure 335 is also 224 + 115 - 4 (computed here), which agrees with the stats line.

Rates (computed here):

| | Round 8 | Round 8 on Round-9 KB | Round 9 |
|---|---|---|---|
| discrepancies per program | 208 / 250 = 0.83 | n/r | 335 / 250 = 1.34 |
| tool crashes per program | 16 / 250 = 0.06 | n/r | 4 / 250 = 0.02 |
| live findings per program | 155 / 250 = 0.62 | 152 / 250 = 0.61 | 224 / 250 = 0.90 |
| live per program without `only_pyright` | 135 / 250 = 0.54 | n/r | 180 / 250 = 0.72 |
| programs with a live finding | 104 / 250 = 41.6 % | n/r | 129 / 250 = 51.6 % |
| ... without `only_pyright` | 92 / 250 = 36.8 % | n/r | 103 / 250 = 41.2 % |
| share auto-closed | 69 / 224 = 30.8 % | 72 / 224 = 32.1 % | 115 / 339 = 33.9 % |
| strong-evidence live findings per program | 13 / 250 = 0.05 (11 programs) | n/r | 10 / 250 = 0.04 (8 programs) |

(n/r = not recorded.) The live rate rose again (0.54 to 0.72 per program, comparable count). The KB change alone moves the Round-8 programs from 0.62 to 0.61, so the rise comes from the Round-9 programs, not from the KB. I did not run the Round-9 programs on the Round-8 KB and did not split the rise by operator, so I cannot say which part of the new mix produced it; section 3 shows where it sits by group and by area. The auto-closed share is nearly flat (30.8 % to 33.9 %); crash events fell from 16 to 4, as planned (crash-family programs 40 to 22).

Round 9 dismissed by category: DESIGN_DIVERGENCE 96, DUPLICATE 10, KNOWN_LIMITATION 6, NOISE 2, SPEC_AMBIGUITY 1 (Round 8: DESIGN_DIVERGENCE 35, DUPLICATE 21, NOISE 8, KNOWN_LIMITATION 3, SPEC_AMBIGUITY 2). By entry: PRECISION-RUNTIME-CONSISTENT 55, LITERAL-WIDENING 27, ASSERT-TYPE-LITERAL-RETENTION 6, MYPY-SKIPS-UNREACHABLE 5, `rule:crash:signal` 4, TY-CHECK-NOT-IMPLEMENTED 4, DISPLAY-EQUIVALENT 2, JOIN-VS-UNION 2, UPSTREAM-TY-4756 2, TY-SELF-UPPER-BOUND 2, then 1 each: UPSTREAM-MYPY-20969, UPSTREAM-TY-2792-READONLY, UPSTREAM-TY-2792, UPSTREAM-MYPY-22339, CALLABLE-SELF-RECEIVER, INFERENCE-DOWNSTREAM. One entry, PRECISION-RUNTIME-CONSISTENT, closed 55 of the 115 (Round 8: 6 of 69). The log does not say which programs these 55 come from; per group, `D_exit` has 56 dismissed findings (section 3), and the. Of the entries added in Round-8 Phase 1, CALLABLE-SELF-RECEIVER fired 1 time and DISPLAY-EQUIVALENT 2 times; CALLABLE-SELF-ATTR-STORE, UPSTREAM-TY-3666, MYPY-2455, TY-4941 and UPSTREAM-PYRIGHT-11382 are not in the dismissed-by-entry list, so they closed nothing.

Auto-closed crashes: 4, by closing reference MYPY-22360 3 and TY-4900 1. All 4 are in the `C_generic_rec` group (section 3). The 6 mutants of the two `d5p_*_rangeerror` parents gave no pyright crash, so Round 9 has no live pyright `RangeError`. Round 8 had 15 closed crashes and 1 live pyright `RangeError`.

Live by kind, Round 8 then Round 9: reveal_mismatch 67 / 48, only_mypy 48 / 45, only_pyright 20 / 44, only_ty 14 / 69, reveal_unpaired 0 / 12, concern_mismatch 5 / 2, runtime_miss 0 / 4, crash 1 / 0. The rise is in `only_ty` (+55) and `only_pyright` (+24). Of the 69 `only_ty`, 25 are one ty diagnostic: `deprecated` on `@contextmanager` with `-> Iterator[..]` (the `only_ty | deprecated` cluster; 11 % of the 224 live per. Without those 25 the live count is 199 (computed here). `reveal_unpaired` and `runtime_miss` did not appear in Round 8's stats line; by group (section 3) `reveal_unpaired` is 7 in `D_exit`, 3 in `H_dunder`, 2 in `fresh`, and `runtime_miss` is 3 in `C_tvt` and 1 in `fresh`.

`only_pyright` runtime relations: 44 findings, `runtime_supports` 22, `runtime_contradicts` 22. Round 8 had 1 of 21. All 22 are tier `review`, confidence 0.7, source `gate`. Their verdicts are in section 5 (D9-9, D9-10): 20 NOT-A-BUG (documented trade-off), 2 a mypy gap (draft 10).

Strong runtime evidence on a live finding: 10 findings in 8 programs (6 `reveal_mismatch`, 4 `runtime_miss`). Triage: 0 of the 44 `only_pyright` findings have strong bug evidence.

## 3. Per group and per area

Round 9 groups are the subdirectories of the judge output that hold a mutant's parent, plus `fresh` for programs without `__mut` in the name. They differ from the Round-8 groups, so there is no row-by-row comparison. The columns come from the per-group yield of the saved reports (totals 250 / 129 / 224 / 10 / 115 / 4 equal the funnel in section 2). "Live" and "strong" are findings, not programs. Discrepancies were not captured per group; the column is live + dismissed - crash events (derived here, sums to 335). Live per program is computed here.

| Group (operator, parents) | Programs | Programs with a live finding | Discrepancies (derived) | Crash events | Live | Strong | Dismissed | Live per program |
|---|---|---|---|---|---|---|---|---|
| C_generic_rec (variance_flip, recursion_deepening, bound_constraint_swap; 2) | 8 | 0 | 0 | 4 | 0 | 0 | 4 | 0.00 |
| C_pyright_range (dunder_instance_shadow 4, overload_reorder 2; 2) | 6 | 4 | 10 | 0 | 10 | 0 | 0 | 1.67 |
| C_tvt (recursion_deepening, invalid_type_form, bound_constraint_swap; 2) | 8 | 8 | 31 | 0 | 29 | 3 | 2 | 3.63 |
| D_exit (exit_swallow_flip; 7) | 21 | 18 | 84 | 0 | 28 | 0 | 56 | 1.33 |
| D_shadow (dunder_instance_shadow; 7) | 21 | 19 | 39 | 0 | 36 | 3 | 3 | 1.71 |
| H_dunder (dunder_instance_shadow 4, exit_swallow_flip 2; 1) | 6 | 6 | 14 | 0 | 11 | 0 | 3 | 1.83 |
| O_async (async_generator_wrap; 3) | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 |
| O_generics (variance_flip, bound_constraint_swap; 6) | 18 | 2 | 11 | 0 | 2 | 0 | 9 | 0.11 |
| O_overload (overload_reorder; 4) | 8 | 6 | 7 | 0 | 7 | 0 | 0 | 0.88 |
| O_protocol (protocol_vs_abc; 3) | 6 | 2 | 2 | 0 | 2 | 0 | 0 | 0.33 |
| O_version (python_version_flip; 3) | 6 | 0 | 1 | 0 | 0 | 0 | 1 | 0.00 |
| R_reserve (runtime_witness, feature_crossover, annotation_spelling_swap, qualifier_toggle; 6) | 24 | 22 | 34 | 0 | 34 | 0 | 0 | 1.42 |
| fresh (no operator) | 109 | 42 | 102 | 0 | 65 | 4 | 37 | 0.60 |
| total | 250 | 129 | 335 | 4 | 224 | 10 | 115 | 0.90 |

Group notes (the saved reports:

* `C_generic_rec`: 8 programs, 4 crash events, all closed (MYPY-22360 3, TY-4900 1), 0 live, 0 escapes. This was the escape test of the TY-4900 entry; its pass is the reason a parent was retired (section 6).
* `C_tvt`: highest rate (3.63). Live kinds: only_mypy 17, reveal_mismatch 8, runtime_miss 3, concern_mismatch 1. The 3 strong findings are the 3 `runtime_miss` rows: `class Callback[*Ts, **P = [bool]]` raises `TypeError` in CPython and no checker says so. All three are python/typing#2211 (D9-5 to D9-7). The parent `d6p_typevartuple_unpack_pep695_paramspec_default_mypy_subscript` gave 19 live, 0 strong, 0 dismissed in 4 programs and has not been read.
* `D_shadow` (`dunder_instance_shadow`): 36 live, 12 of them `only_pyright`; the 3 strong findings are 2 from the `total_ordering` parent's mutant (draft 9) and 1 from the reflected-metaclass parent's mutant (mypy#22377). Both are the parents' own findings, see section 5.
* `D_exit` (`exit_swallow_flip`): 28 live (only_ty 18, reveal_unpaired 7, reveal_mismatch 3), 0 strong, 56 dismissed. No draft came from this group. Draft 10 came from two fresh programs in the new area `context_managers`.
* `O_async` (9 programs) and `O_version` (6): 0 live. `O_generics` (18 programs): 2 live, 9 dismissed.
* `R_reserve`: 34 live in 24 programs (1.42; Round 8's reserve gave 1.50), 0 strong. The reserve parents were chosen because they had a live finding on Round 8, so a high rate is expected.
* `fresh`: 65 live, 4 strong (`gen1_c86958a8` 1, `gen1_4d7d067f` 2, `gen5_ade5dcc3` 1).
* Parent-level live counts: `d6p_typevartuple_unpack_pep695_paramspec_default_mypy_subscript` 19, `d8p_dunder_dispatch_annotation_only_call` 11 (6 programs; 8 without `only_pyright`), `d3p_typevartuple_unpack_paramspec_default_after_tvt` 10 (3 strong), `d4v_metaclass_reflected_op` 9 (1 strong), `d5p_descriptors_decorated_get_pyright_rangeerror` 9.

Per area (the `# area:` line of each program for programs, programs with live, live, live without `only_pyright`; dismissed and strong from the "per area dir" block of the saved reports; live per program computed here):

| Area | Programs | With live | Live | Live without `only_pyright` | Live per program | Strong | Dismissed |
|---|---|---|---|---|---|---|---|
| typevartuple_unpack | 16 | 10 | 34 | 34 | 2.13 | 5 | 21 |
| dunder_dispatch (new) | 28 | 22 | 32 | 24 | 1.14 | 0 | 3 |
| descriptors_properties | 19 | 15 | 26 | 17 | 1.37 | 0 | 3 |
| narrowing_builtin | 12 | 9 | 22 | 21 | 1.83 | 0 | 14 |
| context_managers (new) | 22 | 13 | 16 | 14 | 0.73 | 0 | 13 |
| constructors_metaclasses | 13 | 7 | 14 | 9 | 1.08 | 2 | 0 |
| narrowing_user | 18 | 7 | 12 | 12 | 0.67 | 0 | 28 |
| inheritance_mro | 13 | 6 | 10 | 5 | 0.77 | 2 | 0 |
| generics_variance | 27 | 5 | 9 | 9 | 0.33 | 0 | 13 |
| overloads | 10 | 8 | 9 | 9 | 0.90 | 0 | 0 |
| protocols | 16 | 6 | 9 | 5 | 0.56 | 0 | 0 |
| abstract_classes | 4 | 4 | 8 | 1 | 2.00 | 0 | 0 |
| self_classmethods | 7 | 6 | 7 | 4 | 1.00 | 0 | 9 |
| gradual_any | 19 | 5 | 6 | 6 | 0.32 | 1 | 5 |
| callables | 3 | 3 | 5 | 5 | 1.67 | 0 | 0 |
| tuples_unpacking | 3 | 2 | 4 | 4 | 1.33 | 0 | 5 |
| paramspec_concatenate | 3 | 1 | 1 | 1 | 0.33 | 0 | 0 |
| async_generators | 15 | 0 | 0 | 0 | 0.00 | 0 | 0 |
| enums_literals | 2 | 0 | 0 | 0 | 0.00 | 0 | 1 |
| total | 250 | 129 | 224 | 180 | 0.90 | 10 | 115 |

The two new areas: 50 programs, 48 live findings (32 + 16), 35 programs with a live finding (22 + 13), 0 strong, 16 dismissed. Of the 48, 10 are `only_pyright` (8 in `dunder_dispatch`, 2 in `context_managers`; computed from the without-`only_pyright` column). The new areas gave 21 % of the live findings (48 / 224, computed here) and, through draft 10, one of the two new bug drafts. The Round-8 comparison for the three areas that exist in both rounds: `overloads` 26 programs / 26 live on Round 8 and 10 / 9 on Round 9; `tuples_unpacking` 26 / 18 and 3 / 4; `abstract_classes` 12 / 6 and 4 / 8 (`round-8-report.md` section 3). `match_statement`, `recursive_aliases`, `dataclasses`, `typeddict` and `final_classvar` had 0 programs by plan, so the Round-8 large live sources `recursive_aliases` (27 live) and `match_statement` (21 live) were not sampled. The two largest Round-9 areas, `typevartuple_unpack` (34) and `dunder_dispatch` (32), are the same two that the plan aimed at.

## 4. What changed since Round 8

Phase 1 (code:

* W1: `mentions_self` reads quoted annotations (`'Self'`, `'list[Self]'`), skips `Literal[...]` and the metadata of `Annotated[...]`; the spec-desugar probe rewrites `Self` inside the string. W2: `TY-2792-READONLY` also looks at each enclosing scope, with the chain required only to precede the `def` that holds the statement. Not changed on purpose: a `__dict__` write is not treated as a mutating call, and `reveal_type(c.readonly)` rows stay live.
* New `typediff/operators.py`: operators that carry their own instruction (`dunder_instance_shadow`, `exit_swallow_flip`); the 21 older operators still produce `{"operator": op}`, so their prompts and file-bridge keys are byte-identical (test `test_generate_prompt_of_an_old_operator_is_unchanged`). New areas `dunder_dispatch` and `context_managers` in `typediff/strategy.py` (22 to 24 areas).
* Tests 604 to 655 (51 new in `tests/test_round9_pipeline.py`). kb-selftest stays at 20 entries. No KB entry was added in Phases 1 to 6.
* Replay of the Round-8 reports: 3 findings changed, live 155 to 152 (section 2). The Round-9 judge run is on this code and KB; nothing changed between Phase 1 and Phase 6, Phase 6 item 6). The two entries touched by W1 and W2 fired 2 times (TY-SELF-UPPER-BOUND) and 1 time (UPSTREAM-TY-2792-READONLY) on Round-9 programs; those entries also fired before Phase 1, so these counts do not isolate the two fixes.

Round-8 weaknesses (`round-8-report.md` section 7) and their state:

| Round-8 weakness | State on Round 9 |
|---|---|
| `mentions_self` does not read quoted `'Self'` (2 live findings) | fixed (W1), tests |
| `TY-2792-READONLY` needs the assignment in the narrowing scope (3 strong findings) | fixed (W2), tests |
| `TY-NONFINAL-PATTERN`, `ASSERT-NEVER-ALL-REJECT`, wider `JOIN-VS-UNION` queued, not implemented | still not implemented (decision D-2; the plan sent 0 programs to match_statement, recursive_aliases, dataclasses) |
| `runtime_supports` for `only_pyright` untested on a true positive | fired 22 of 44; none of the 20 dunder rows is a bug, the 2 `with` rows are a mypy gap (section 5) |
| drafts 6, 7, 8 unfiled, no playground link | unchanged; drafts 9 and 10 added, also unfiled |

Phase 2: promoted `d8p_dunder_dispatch_annotation_only_call` (Round-8 mutant `d3p_callables_self_call_attr__mut0_5445453a`, the annotation-only `__call__` lead) to `seeds/parents/`, 40 to 41. Crash probe: ty rc 134 on 11 of 59 files, rc 101 on 1; `d3p_generics_contravariant_recursive_generic_base` (TY-4900) was not in the Round-8 probe list and still crashes. The four Round-8 escape-watch parents were not mutated again; `C_pyright_range` was cut from 12 to 6 programs. 250 programs planned: 109 fresh (44 in the new areas, 65 in nine areas with no program on Rounds 7 and 8), 48 with the new operators (+4 inside the crash groups), 47 with the six operators no earlier round used (+10 inside the crash groups), 22 crash-family, 24 reserve. Of the 141 operator prompts, 109 (77 %) use an operator no earlier round used.

Phase 5: promoted 0, retired 1 (section 6). KB entries added: none. One queued, not implemented: `MYPY-8595` (KNOWN_LIMITATION; needs a named matcher in `typediff/kb.py`).

## 5. Candidates and verdicts

Run with the pins plus ty 0.0.99, mypy 2.4.1 and master, pyright 1.1.414 (latest). ty 0.0.97 and 0.0.99 gave identical output on all 30 reduction programs. All 8 strong programs reproduce when run alone.

| Id | Candidate | Verdict |
|---|---|---|
| D9-1 | mypy reveals `Widget` for a class whose metaclass `__call__` returns `int` (1 strong finding) | DUPLICATE python/mypy#8595 (closed, "unlikely this will be ever supported"); open #14122 is the feature request. CPython, ty, pyright say `int` |
| D9-2 | mypy reveals `tuple[int, str]` for a 4-tuple (2 strong) | NOT-A-BUG. `tuple[*Ts, *Us]` is invalid and all three tools reject the signature; the reveal follows the error |
| D9-3 | mypy reveals the opposite literal for `c1 < c2` and `c1 > c2` (2 strong) | STILL-BUG-NEW (mypy), **draft 9**. 18-line reduction without `total_ordering`; CPython `'lt' 7`, ty and pyright agree, mypy 2.4.0, 2.4.1 and master swap `int` and `str`. Cause read in master `checkexpr.py` `check_op_reversible`: the same-type branch is guarded by `op_methods_that_shortcut`, which has no comparisons. Duplicate search (13 issue and 6 PR queries on mypy, 2 each on ty and pyright) found nothing that describes it; the parent has been a live reveal mismatch since Round 2 and was never verified |
| D9-4 | mypy `int` for `A * B` where `RightMeta` subclasses `LeftMeta` (1 strong) | DUPLICATE python/mypy#22377 (open, filed 2026-11-05, draft 3) |
| D9-5 | `class Callback[*Ts, **P = [bool]]` raises `TypeError`, no checker says so (1 strong) | DUPLICATE python/typing#2211 (open); the checkers follow the spec, the runtime is wrong |
| D9-6 | same class, `..mut0_df958820` (1 strong) | DUPLICATE python/typing#2211; mypy's `Callback[int, str]` error is draft 5 (python/mypy#22375) |
| D9-7 | same shape with `Generic[*Ts, P]` and `ParamSpec(default=...)` (1 strong) | DUPLICATE python/typing#2211 |
| D9-8 | `n + 1` with a `str` passed through `Any` (1 strong) | NOT-A-BUG (gradual guarantee) |
| D9-9 | 20 `only_pyright` `runtime_supports` rows: `len(x)`, `list(x)`, `iter(x)` on a class whose dunder is annotation-only or instance-assigned | NOT-A-BUG, known trade-off. Pyright's message is "Could not bind method" in 19, `No overloads for "iter"` in 1. CPython raises `TypeError`; no checker rejects all five operations on `d1.py`. Documented in ty#4570 and ty#491 (open) and mypy#2113 (open since 2016). Not drafted, confidence below 0.3 |
| D9-10 | 2 `only_pyright` rows: a name bound in a `with` whose `__exit__` returns `bool`, used after the block (`context_managers/gen0_b82d2e9e`, `gen21_6ee04c3a`) | STILL-BUG-NEW (mypy `possibly-undefined`), **draft 10**, confidence 0.4. CPython `UnboundLocalError`; pyright reports it by default; ty reports it with the off-by-default `possibly-unresolved-reference` rule (so not a bug); mypy 2.4.0 and master do not, with or without `--enable-error-code possibly-undefined`, although its type checker does model swallowing (`Missing return statement`). Cause read in `partially_defined.py`, not instrumented |
| D9-11 | mypy `Need type annotation for "key"` for `self.key = key` with a constrained type variable (live row of `..mut0_df958820`) | DUPLICATE python/mypy#19618 (open) |

Counts: the 8 strong candidates (10 findings): STILL-BUG-NEW 1, DUPLICATE 5, NOT-A-BUG 2, FIXED 0. All 11 rows: STILL-BUG-NEW 2, DUPLICATE 6, NOT-A-BUG 3.

What produced what:

* Draft 9 is the `total_ordering` parent's own finding, found again by a mutant (`..mut0_73c4aa3f`, similarity 0.70 to its parent); the new operators did not create it. Draft 10 came from two fresh programs in the new area `context_managers`, not from an `exit_swallow_flip` program. The operator `dunder_instance_shadow` produced 20 `runtime_supports` rows; all 20 are the documented trade-off, so the operator found no bug of its own on Round 9. `exit_swallow_flip` found none (`D_exit`: 0 strong, no draft).
* Net new bugs: 2 drafts (Round 8: 1, Round 7: 2). Drafts 9 and 10 were appended to `results/bugs.md` with `<PLAYGROUND LINK>` placeholders. Drafts 1 to 5 are filed (ty#4933, ty#4934 closed, mypy#22377, ty#4941, mypy#22375, per the author listing of 2026-11-06, the saved reports); drafts 6 to 10 are not.
* Verification effort: 133 `gh search` queries of one to three words (issues 104, PRs 29), 12 `gh issue view`, 3 `gh release list`, one author listing.

## 6. Parents and hits

Phase 5:

* Candidates: 10 strong findings in 8 programs. Highest similarity to any file of `seeds/parents/`: 0.70 (`d3p_inheritance_mro_total_ordering_inherited_lt__mut0_73c4aa3f` to its parent), then 0.56, 0.53, 0.48, 0.43, 0.40, 0.36, 0.33; none at or above 0.80. **Promoted 0** (D9-1 duplicate of #8595, D9-2 invalid program, D9-8 gradual guarantee, the others rediscoveries of existing parents).
* **Retired 1**: `d3p_generics_contravariant_recursive_base` out of `seeds/parents/` (4 programs, 0 live, 1 closed crash; the `C_generic_rec` group had 0 escapes). Reversible with `mv`. Kept although mutated: `d3p_generics_callable_attr_contravariant` (3 programs, 0 live, 2 dismissed; "revisit if Round 10 gives 0 again"), `d3p_typevartuple_unpack_paramspec_default_after_tvt`, `d6p_typevartuple_unpack_pep695_paramspec_default_mypy_subscript`, `d4v_ty_attr_eq_narrow_unreachable`, both `d5p_*_rangeerror`, `d8p_dunder_dispatch_annotation_only_call`.
* `seeds/parents/`: 40 files at the start, 41 after the Phase-2 promotion, 40 after the retirement. `check_hits.py 0.80` after: 40 files, 0 with problems, no near-duplicate pair (section 9).

## 7. Weaknesses

* The `deprecated` diagnostic of ty on `@contextmanager` with `-> Iterator[..]` is 25 of the 224 live findings (11 %) and has no rule or entry. `STUB-SKEW` appears as a hint, but the experiment says the mypy flag does not explain ita).
* `runtime_supports` for `only_pyright` gives tier `review`, confidence 0.7 to 22 rows; 20 of them are a documented trade-off and the other 2 are a mypy gap at confidence 0.4. The weighting has now fired on real data and the result is mostly non-bugs. The rule has no way to tell a documented trade-off from a defect.
* Strong runtime evidence gave 10 findings in 8 candidates and 1 new bug (D9-3, 2 findings). The other 8 findings are 5 in duplicate candidates and 3 in not-a-bug candidates (computed here from section 5); D9-3 itself is an old parent finding. As on Round 8, strong evidence says the checker's type disagrees with the observed value, not that the checker breaks its own rules.
* Matchers and rules queued, not done: `TY-NONFINAL-PATTERN`, `ASSERT-NEVER-ALL-REJECT`, wider `JOIN-VS-UNION` (Round 8); `MYPY-8595` (one live finding in 250 programs); a rule for reveals after an invalid type form (`tuple[*Ts, *Us]`, 2 strong rows from one program); mypy `Attribute function "__call__" ... does not accept self argument` for annotation-only dunders (6 live `only_mypy` findings in the triage, same family as the Round-8 callable-self rows).
* Two triage clusters carry mypy's "Can only replace ParamSpec with a parameter types list or another ParamSpec, got ..." message: 7 and 3 live `only_mypy` findings (the two `only_mypy | misc` clusters headed "can only replace paramspec"). D9-6 and D9-7 tie this message to draft 5 (filed as mypy#22375) for 2 programs; the other rows were not checked, and there is no KB entry for it. `C_tvt` and its parent `d6p_..._mypy_subscript` (19 live, unread) are the largest unexamined live source.
* Of the 224 live findings, 33 were examined individually (10 strong + 22 `only_pyright` `runtime_supports` + 1 mypy `var-annotated` row; the sets are disjoint, computed here), 20 of the 22 grouped by mechanism rather than reduced one by one. The other 191 were read only as triage clusters. The Phase-5 read of rows per area is not a verdict.
* The new operators were checked for being followed only by regex (section 1). `H_dunder`'s `__exit__` rate is below half if the one `__exit__` program is an `exit_swallow_flip` one, which cannot be told from the log.
* One of the 50 generator sessions has no `effortLevel` field (model correct).
* Drafts 6 to 10 are unfiled and have no playground link. D9-4, D9-5 to D9-7 and D9-11 are duplicates that the KB does not close, so they reappear live (for example `d4v_metaclass_reflected_op` 9 live, `d3p_typevartuple_unpack_paramspec_default_after_tvt` 10 live).
* Round-8 comparison is confounded by the mix; the split between mix and KB was measured only for the KB side (3 findings).

## 8. Not verified

* Drafts 9 and 10 on a playground (placeholders open). No playground (ty, mypy, pyright) was used for any draft.
* ty `main`, pyright `main`, mypy PR branches (for example PR #22380); none was built.
* The mypy cause in D9-3 (`check_op_reversible`) and D9-10: read from mypy master source, not shown by instrumentation. D9-10 confidence is 0.4; an opt-in check without type information may be a known limit.
* Whether the maintainers of ty, mypy and pyright intend annotation-only or instance-assigned dunders to count (D9-9); only the open issues were read.
* The 20 dunder `runtime_supports` rows were each checked for pyright's message, not reduced; the `expect-error` comments of the programs were not checked as claims.
* 191 of 224 live findings (section 7); in particular the 7 + 3 `Can only replace ParamSpec` rows, the 6 `Attribute function "__call__"` rows, and the 19 live findings of `d6p_..._mypy_subscript`.
* How much of the live-rate rise (0.54 to 0.72 without `only_pyright`) comes from which part of the mix (section 2); the Round-9 programs were not replayed on the Round-8 KB.
* Discrepancies per group (derived only), Round-8 programs with a live finding on the Round-9 KB replay, and Round-9 results per mutation operator (the groups mix operators in `H_dunder`, `C_pyright_range`, `O_generics`, `R_reserve`).
* Quality of the 250 generated programs beyond the preflight, the operator-follow regexes and the triage read.
* Round-6 candidates 2 (ty recursive alias solution) and 3 (mypy memory blow-up) were not revisited.
* A generator session without `effortLevel` (`sess_18c01ae7-...`): why the key is missing was not investigated.
