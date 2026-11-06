# Day 8 morning decisions (Plan §3 "Every morning") and generation plan, phase 2

Branch `campaign/day8-p2`, local only; nothing pushed, no GitHub write (`gh search issues` and `gh issue view` only). Pins unchanged: mypy 2.4.0, ty 0.0.97, pyright 1.1.414, CPython 3.13.16.
Inputs: `campaign/day7-morning.md` (the model for this file), `campaign/day7-report.md`, `campaign/day8-pipeline.md` and `campaign/day8-run-log.md` (phase 1), the Day-7 judge run `runs/day7/out` and its replay with the final phase-1 KB, `runs/day8/day7replay-it2` (224 programs, `--pyright-only --rerun-runtime`).
Generation was **not** run in this step. The next step runs `campaign/day8/mk_groups.sh`, `campaign/day8/gen_pass.sh`, `campaign/day8/answer_pending.sh`, then `campaign/day8/judge.sh`. Evidence of this step is in `campaign/day8/phase2/`.

## 1. Changes to `runs/hits` (42 files before, 42 now)

No parent was moved or promoted today. `runs/` is git-ignored.

| Parent | Action | Why |
|---|---|---|
| `d7p_tuples_unpacking_partial_unpack_except_ty` | stays, **mutated for the first time** (group `H_new`, 8 programs) | promoted on Day 7 after the judge run, so it had no Day-7 mutants; its header lists the variations to try |
| `d3p_paramspec_self_annotated_dunder_call` | stays in `runs/hits`, **not mutated** | Day 7: 0 of 7 mutants crash ty (they dropped the `x: int` parameter the crash needs); since phase 1 all its non-crash findings are dismissed (`CALLABLE-SELF-RECEIVER`, `-ATTR-STORE`, `UPSTREAM-TY-3666`, `DISPLAY-EQUIVALENT`) and the crash itself is `TY-4899`. Retiring (move to `runs/hits-dropped`) waits for one more day of evidence; the ParamSpec identity parent below shows whether this family still yields anything |
| `d4v_eq_no_hash_hashable`, `d4p_inheritance_hash_none_from_eq`, `d3p_inheritance_mro_hash_none_from_eq` | stay, **not mutated** | partly closed by `MYPY-2455` / `TY-4941` (phase 1); `d3p_inheritance_mro_hash_none_from_eq` still gives a live `runtime_miss` on purpose. Day 7's `inheritance_mro` fresh run (10 programs) gave 1 live finding |
| `d4v_protocols_expanding_self_receiver`, `d6p_protocols_expanding_self_receiver_{dict_arg,pep695,tuple_nesting}_ty`, `d6p_async_generators_protocol_flatten_overflow_ty` | stay, **never mutated** | the draft-1 expanding-receiver family still crashes ty (rc 134, probe in section 5) and has no KB entry. Generating from it would recreate the 20 live crash findings of Day 6 |
| `d3p_callables_self_call_attr`, `d4v_callables_mutual_call_attr`, `d3p_self_classmethods_self_call_union`, `d3p_protocols_generic_protocol_stack_overflow` | stay in `runs/hits-dropped` (retired Day 7); **used for 8 "escape watch" programs** | they still crash ty (rc 134), but all 26 Day-7 crash events were closed by `TY-4148` / `TY-4882`. Two programs each tests whether a mutant escapes the entry's predicate, with operators Day 7 did not use |
| `d3p_crash_ty_panic_partial_or_none_in_loop`, `d3p_crash_ty_timeout_typeis_generic_in_loop`, `d4p_callables_crash_ty_panic_partial_loop` (hits-dropped), `d3p_crash_ty_stack_overflow_protocol_flatten` (hits) | no generation | ty 0.0.97 gives rc 1 with diagnostics on all four, they no longer crash |
| `d3p_crash_mypy_segv_recursive_tvt_default_alias` | no generation | mypy rc 137 (killed by the memory guard), the `MYPY-22361` shape that Day 7 closed 13 times |

`.venv/bin/python campaign/day4m/check_hits.py 0.80`: **42 files; 0 with problems; no near-duplicate pair** (`phase2/check_hits-before.out`).

Areas with no parent in `runs/hits` (`phase2/areas-without-hits.txt`): `typeddict`, `overloads`, `match_statement`, `dataclasses`, `self_classmethods` (new: its only parent was retired on Day 7), `final_classvar`, `abstract_classes`. `tuples_unpacking` has one parent since Day 7.

## 2. Were the Day-7 live items real or display noise? (priority d)

Method: `phase2/scripts/area_live.py` over `runs/day7/out` (judge run) and `runs/day8/day7replay-it2` (same reports, final phase-1 KB, CPython re-run). Table `phase2/area-live-table.txt`, every live finding of the two areas with the three tool messages in `phase2/area-live-match-dataclasses.txt`. Reproduction on the pins: `phase2/repro/m1.py` (`m1.out`) and `phase2/repro/d1.py` (`d1.out`).

Live findings per area, Day-7 judge run vs the same reports with the phase-1 KB:

| Area | Programs | Live before | Live after |
|---|---|---|---|
| match_statement | 16 | 21 | **21** |
| dataclasses | 28 | 13 | **11** |
| typeddict | 16 | 8 | 0 (all TypedDict display noise) |
| paramspec_concatenate | 24 | 18 | 0 (`CALLABLE-SELF-RECEIVER` and friends) |
| descriptors_properties | 34 | 20 | 18 |
| overloads / tuples_unpacking / recursive_aliases / abstract_classes | 16 / 22 / 8 / 10 | 6 / 7 / 6 / 2 | unchanged |

So the display rules removed 8 TypedDict items and 2 dataclass items; **none of the 21 match_statement items is display noise**. The remaining items are not new-bug evidence either. No finding in the two areas has strong runtime evidence (`phase2/area-live-table.txt`, column `strong`: 0 and 0).

### 2.1 match_statement, 21 live findings from 9 programs (7 of them mutants of the one seed `class_sequence_patterns`)

| Class | n | What it is | Verdict | Goes to |
|---|---|---|---|---|
| B. ty reveals more than mypy and pyright | 9 | `reveal_type(rest)` or `reveal_type(s)` after a sequence, mapping or class pattern. ty: `tuple[int, int] & ~Point & ~Circle` (4), `list[int] \| list[str]`, `list[int] \| list[object] \| list[str]`, `list[int] \| list[Unknown]`, `dict[object, Unknown] \| dict[object, object] \| dict[str, int]` (5). mypy and pyright: the plain type | design difference: ty keeps the possibility that a value of a non-final class (`Point`, `int`, `dict`, `list`) is also a `Sequence` or `Mapping` subclass. Reproduced on the pins: `list[int] \| int` subject gives ty `list[int] \| list[object]`, `Point \| list[int]` after `case Point()` gives `list[int] & ~Point` forms, mypy and pyright `list[int]` (`m1.out`). The `list[str]` member in two programs is consistent with a `dict[str, int]` subject (iterating a dict gives `str`), I did not trace it in ty's source | **KB entry** (DESIGN_DIVERGENCE), see 2.3 |
| A. `assert_never` rejected by all three | 6 | `concern_mismatch` on `assert_never(s)`: mypy `list[int]`, pyright `list[int]`, ty `list[int] & ~Point`; all three say the argument is not `Never` | not a differential finding: nobody accepts. The programs expect `[first, *rest]` plus `[]` to exhaust a `list[int]`, which none of the three narrows (the seed's own hypothesis expects mypy not to narrow non-tuple sequences by length). A possible shared false positive, outside what a differential pipeline can judge; not checked against the spec | **KB entry** (dismiss when all three tools report an error on the same `assert_never` call), see 2.3 |
| C. mypy `describe(v)` argument is `object` | 3 | `for v in [Point(..), (1, 2), ..]: describe(v)`: mypy reports `object` (join of the list elements), ty and pyright are silent | join-vs-union, the plan's "do not chase" item; the existing `JOIN-VS-UNION` entry fires only on reveals | **KB entry**: widen `JOIN-VS-UNION` to an `arg-type` error whose argument is a loop variable over a list display of mixed element types (needs a control: a list of one type stays live) |
| D. ty `object + object` after `case (a, b)` | 2 | Day-7 candidate D7-5, a non-final class in the subject | NOT-A-BUG, ty#1578 (closed, not planned; `gh issue view`, `phase2/gh-postinit-match.out`) | same entry as B (same mechanism) |
| E. mypy `list-item` error | 1 | `Wrap([])` is `Wrap[list[Never]]` in a list typed with the union | a mutant with a wrong type, mypy is right | none, stays live |

Mutation: **no more mutants of `class_sequence_patterns` beyond 2** (it produced 13 live findings on Day 7, 12 of them classes A to D). New match coverage comes from 24 fresh programs and the 2 mutants with operators Day 7 did not use. `typediff generate` has no avoid hook (`cmd_generate` passes `[]`), so fresh programs will meet classes A and B again; they are cheap once the entries exist.

### 2.2 dataclasses, 11 live findings from 7 programs, all mutants of the seed `overloaded_post_init`

| Class | n | What it is | Verdict | Goes to |
|---|---|---|---|---|
| F. mypy rejects an extra `__post_init__` overload | 4 | `@overload def __post_init__(self, value: str)` next to `value: int` for `InitVar[int]` (override error, "Argument 2 ... supertype defines the argument type as int"). ty and pyright are silent. The seed itself says "expected: accepted; mypy 2.4.0 instead rejects the extra str overload" | the plain, non-overloaded mismatch **is** rejected by all three (`d1.out`: mypy override error, ty `invalid-dataclass`, pyright parameter type mismatch). So the difference is only for overloaded `__post_init__`. **Candidate mypy false positive**, not verified: an overloaded override with one compatible item should be accepted. 3 `gh search issues` term sets on python/mypy found nothing | **verify** in the next step (reduction, mypy 2.4.1 and master, spec text); 3 variants in the reserve to size it. Not a KB entry yet |
| G. other overloaded `__post_init__` mismatches | 4 | `memoryview` against `bytes`, `dict[str, list[int]]` against `dict[str, list[T]]`; in one program ty also reports `invalid-dataclass` | no compatible overload exists, mypy is right | none, stays live |
| H. `InitVar[int]` as a function parameter annotation | 3 | one program: ty `invalid-type-form` and pyright `reportInvalidTypeForm` reject it, mypy accepts it and then reports two consequences (`*` on `InitVar[int]`, wrong argument type) | mypy false negative on an invalid annotation, mutant-induced, low value | none, stays live; the two consequences would close with it |

Mutation: `overloaded_post_init` gets 2 mutants (not 6); `kw_only_initvar_order` and `dataclass_transform` (0 or 2 live in 12 Day-7 programs) get 4 each; 24 fresh programs.

### 2.3 KB entries wanted before the Day-8 judge run (not implemented in this step)

| Entry (proposed id) | Kind / category | Closes (Day 7) | Controls it needs |
|---|---|---|---|
| `TY-NONFINAL-PATTERN` | reveal_mismatch / only_ty on a statement inside a `case` of a program whose subject union contains a non-final class; ty's text is mypy's text plus `& ~Name` terms or extra `list[..]` / `dict[..]` union members. DESIGN_DIVERGENCE, source ty#1578 | classes B and D, 11 | a `@final` class in the subject stays live (ty#1578 says `@final` removes it); ty narrower than mypy stays live; a CPython type error at the statement stays live |
| `ASSERT-NEVER-ALL-REJECT` | concern_mismatch: mypy, ty and pyright all report an error on the same `assert_never(..)` call. NOISE | class A, 6 | one tool silent stays live; a non-`assert_never` call stays live |
| `JOIN-VS-UNION` (widen) | only_mypy `arg-type` with a loop variable over a mixed list display | class C, 3 | single-type list, argument not a loop variable |

Each needs the phase-1 routine: tests with positives and controls, replay of Day 7 (`kbloop_replay.py ... --rerun-runtime --verify-sample 30`), replays of the Day 3 to 6 controls, `kb-selftest`. If the entries are not done before the judge run, expect about 20 to 25 more live findings from the 250 programs (Day 7 had 20 findings in classes A to D in 224 programs).

## 3. Budget (250 programs, all generated)

Day 7 generated 224 of 250 and never spent the 26-program reserve. Day 8 generates all 250 in one `gen_pass.sh`. The reserve parents come from Day-7 programs that already have a live finding, so no mid-day judge is needed.

| Share | Programs | Source |
|---|---|---|
| (c) ty and pyright crash families that still reproduce | 40 | section 4 |
| (c) pass-2 reserve | 26 | section 5 |
| (c) pyright descriptors for `runtime_supports` | 18 | section 6 |
| promoted Day-7 parent | 8 | section 4.2 |
| (d) fresh, areas without parent plus `tuples_unpacking`, `descriptors_properties` | 120 | section 7 |
| (d) hand-seed mutants | 38 | section 7 |
| **Total** | **250** | |

Dry run of `campaign/day8/gen-pass-dryrun.sh` (`gen_pass.sh` against the scratch inbox `/tmp/d8-dryrun`, no answers, nothing written under `runs/day8/{inbox,gen}`, no gate file): **`pending=250 written=0`**, `inbox_check.py`: `prompts=250 (retry prompts=0) answers=0 pending=250 orphan_answers=0 malformed_keys=0`, 250 prompt files, 250 distinct keys, **0 keys shared with `runs/day7/inbox`** (`phase2/gen-pass-dryrun.out`, `phase2/overlap-day7.out`). Group sizes: `A_pyright_range 2, A_ty_4898 1, A_ty_escape 4, H_new 1, N_seeds_a 3, N_seeds_b 8, P_pyright 3, R_reserve2 1, R_reserve3 8`.

Operators and `n` differ from Day 7 for every parent and area, on purpose: the file bridge keys a prompt by its text, so an identical prompt reproduces the Day-7 program.

## 4. (c) Crash families, 40 programs, probed as on Day 7

Probe: `phase2/scripts/probe_crash_parents.sh` -> `phase2/crash-parents-probe.tsv` (sequential, memguard shim, 90 s limit, same method as `campaign/day7/partB/probe_ty_crash_parents.sh`, extended to `runs/hits-dropped`, mypy and pyright).

| Parent | Tool | rc | Signature | Used |
|---|---|---|---|---|
| `d3p_paramspec_identity_applied_to_itself` | ty | 134 | stack overflow (TY-4898) | yes |
| `d3p_paramspec_self_annotated_dunder_call` | ty | 101 | panic (TY-4899) | no (section 1) |
| `d3p_callables_self_call_attr`, `d4v_callables_mutual_call_attr`, `d3p_self_classmethods_self_call_union` | ty | 134 | stack overflow (TY-4148) | escape watch |
| `d3p_protocols_generic_protocol_stack_overflow` | ty | 134 | stack overflow (TY-4882) | escape watch |
| `d4v_protocols_expanding_self_receiver`, `d6p_async_generators_protocol_flatten_overflow_ty` | ty | 134 | stack overflow (draft 1 family) | no |
| `d3p_crash_ty_stack_overflow_protocol_flatten`, `d3p_crash_ty_panic_partial_or_none_in_loop`, `d3p_crash_ty_timeout_typeis_generic_in_loop`, `d4p_callables_crash_ty_panic_partial_loop` | ty | 1 | diagnostics only (the TSV says "panic" for the second one only because the word is in the file's own header comment, `phase2/panic-text.out`) | no (fixed) |
| `d3p_crash_mypy_segv_recursive_tvt_default_alias` | mypy | 137 | killed by memory guard | no (MYPY-22361) |
| `d5p_descriptors_decorated_get_pyright_rangeerror`, `d5p_descriptors_one_decorator_dunders_pyright_rangeerror` | pyright | 2 | `RangeError` (draft 7) | yes |

| Group | Parents | Ops: n per parent | Programs |
|---|---|---|---|
| `A_ty_4898` | `d3p_paramspec_identity_applied_to_itself` | recursion_deepening 4, feature_crossover 3, invalid_type_form 1 | 8 |
| `A_pyright_range` | the two `d5p_*_rangeerror` parents | runtime_witness 2, inheritance_diamond 2, union_widen 2 | 2 x 6 = 12 |
| `A_ty_escape` | TY-4148 trio, TY-4882 protocol parent | feature_crossover 1, generic_nesting 1 | 4 x 2 = 8 |
| fresh | `recursive_aliases` (crash hunting, Plan P4) | n = 12 | 12 |

Day-7 yield of crash programs: the 29 programs of `A_ty_4148` and `A_ty_paramspec` gave 0 live ty crash findings; all 29 crash events (26 + 3, `group_yield.out`) were closed by an entry. Today's crash share therefore moves to the pyright `RangeError` pair (the only crash family with a live Day-7 finding) and to the ParamSpec identity parent (2 live, 3 closed crashes in 7 programs); the retired parents get 8 programs instead of 15 to 29 as an escape watch.

### 4.2 Promoted parent (8 programs, group `H_new`)

`d7p_tuples_unpacking_partial_unpack_except_ty` (draft 6, strong runtime evidence on 3 Day-7 siblings): feature_crossover 3, narrowing_construct_swap 2, runtime_witness 2, generic_nesting 1. The parent's header names the variations (nested star target, handler narrowing, for target, attribute target, `finally`, `with`/`del`).

## 5. (c) The pass-2 reserve, 26 programs, spent today

Parents: Day-7 programs of the no-parent areas with a live finding in `runs/day8/day7replay-it2` that is not in a family queued for the KB (section 2.3). `campaign/day8/check_reserve.py` (`phase2/reserve-check.out`): 9 parents, each has 1 or 2 live findings, closest `runs/hits` file ratio 0.28 to 0.44, closest other reserve parent 0.35 to 0.55 (threshold 0.80), 0 flagged. They are copied as `rsv_<area>_<hash>.py` into groups; they are not added to `runs/hits`.

| Group | Parent (Day-7 program) | Why it is a parent | Programs |
|---|---|---|---|
| `R_reserve3` | `overloads/gen7_d41747bd` | 3-way disagreement on a `Literal` flag overload: mypy `Literal['A'] \| Literal['B'] \| int`, ty `Literal["a", "b"] \| int`, pyright `int \| str` | 3 |
| `R_reserve3` | `overloads/gen4_7ab4b09b` | `overload-overlap` in mypy and `reportOverlappingOverload` in pyright; ty silent | 3 |
| `R_reserve3` | `abstract_classes/gen9_ae31b752` | pyright-only override error on `name = 'attr'` over an abstract property; mypy-only `arg-type` | 3 |
| `R_reserve3` | `tuples_unpacking/..variadic_tuples__mut0_b068dfad` | mypy `Cannot determine type of "x"` (has-type) on variadic unpacking | 3 |
| `R_reserve3` | `tuples_unpacking/..variadic_tuples__mut1_c98fed28` | the same finding, a second program | 3 |
| `R_reserve3` | `dataclasses/..overloaded_post_init__mut0_223fff8f` | class F (candidate mypy false positive), to size the variants | 3 |
| `R_reserve3` | `recursive_aliases/gen4_0bbabab4` | pyright prints `list[Nested[T@Nested]]`, mypy `str \| list[...]`, ty `list[str \| list[Nested[str]]]` | 3 |
| `R_reserve3` | `recursive_aliases/gen3_d5395259` | JSON and tree aliases: three different reveals | 3 |
| `R_reserve2` | `overloads/gen9_d6e90b34` | second overlap case | 2 |

Ops: `R_reserve3`: feature_crossover 1, runtime_witness 1, narrowing_construct_swap 1; `R_reserve2`: feature_crossover 1, runtime_witness 1. Total 8 x 3 + 2 = **26**. Considered and left out: `tuples_unpacking/gen9_c53ea70f` (mypy join `list[Sequence[object]]` against ty and pyright `list[str \| bytes]`, join-vs-union), `overloads/gen6_3e1bf348` (`Any` against `Unknown`, display), the match items of section 2.1 and the dataclass classes G and H.

## 6. (c) `only_pyright` and `runtime_supports`

Phase 1 found the cause (the harness saw only uncaught exceptions) and fixed it. Replay of saved runs: Day 7 0 -> 1 of 19, Day 6 0 -> 5 of 37 (`phase1/only_pyright_relations.txt`). The one Day-7 case is `desc.__delete__(obj, 1)  # expect-error` in the decorated-descriptor family, three of the Day-6 cases are unhashable set and dict displays.

Today's programs that can produce more: `P_pyright` 18 (`d3p_descriptors_decorated_get`, `d4p_descriptors_readonly_prop_never`, `d3p_generics_callable_attr_contravariant`; runtime_witness 2, inheritance_diamond 2, scope_relocation 2 each), `A_pyright_range` 12 (above), fresh `descriptors_properties` 12. `runtime_witness` is the operator that asks for calls CPython can refute. `judge.sh` keeps `--pyright-only` for all 250 programs and ends with `campaign/day8/only_pyright_relations.py` -> `campaign/day8-only-pyright-relations.txt` (count by relation and the `runtime_supports` rows). **Check after the judge run**: `runtime_supports` > 0 on programs generated today, and read each such row's evidence text before trusting the 0.7 priority.

## 7. (d) Areas without parent and highest live yield, 158 programs

Fresh (`generate --area A --n N`; N differs from Day 7's 10 everywhere):

| Area | Programs | Day 7 (programs, live after phase-1 KB) | Reason |
|---|---|---|---|
| match_statement | 24 | 16, 21 | highest live yield; no parent. Classes A to D are KB-queued, so the extra programs are for what is not yet seen |
| dataclasses | 24 | 28, 11 | no parent; one seed produced all 11 |
| typeddict | 12 | 16, 0 | no parent; Day-7 live items were display noise, now closed |
| overloads | 14 | 16, 6 | no parent; 3 distinct patterns (section 5) |
| self_classmethods | 11 | 0 (not generated) | no parent since the Day-7 retirement; 3 hand seeds exist |
| abstract_classes | 9 | 10, 2 | no parent, no seed |
| final_classvar | 6 | 16, 0 | no parent; 0 live in 16 programs, so the smallest share |
| tuples_unpacking | 8 | 22, 7 | has a parent now (`H_new` covers it) |
| descriptors_properties | 12 | 34, 18 | `runtime_supports` target (section 6) |
| **Total** | **120** | | |

Hand-seed mutants (38): `N_seeds_a` (3 seeds x 2: `class_sequence_patterns`, `overloaded_post_init`, `final_overrides`; union_widen 1, gradual_injection 1) and `N_seeds_b` (8 seeds x 4: `kw_only_initvar_order`, `dataclass_transform`, `readonly_notrequired`, `literal_flag_overload`, `variadic_tuples`, and the 3 `self_classmethods` seeds; qualifier_toggle 1, literal_injection 1, annotation_spelling_swap 1, scope_relocation 1). `partial_unpack_exception` is replaced by its promoted parent.

## 8. How the next step runs it

```
bash campaign/day8/mk_groups.sh > out.txt 2>&1      # rebuild runs/day8/parents/* (sizes: A_pyright_range 2, A_ty_4898 1, A_ty_escape 4, H_new 1, N_seeds_a 3, N_seeds_b 8, P_pyright 3, R_reserve2 1, R_reserve3 8)
bash campaign/day8/gen_pass.sh 0 > out.txt 2>&1     # then answer_pending.sh, then gen_pass.sh 1, 2 ... until pending=0 written=250
bash campaign/day8/answer_pending.sh > out.txt 2>&1 # headless kiro-cli --agent-engine v3 --model claude-haiku-5.5 --effort medium, 5 prompts per session, 4 sessions at once
bash campaign/day8/judge.sh > out.txt 2>&1          # kbloop_run --jobs 14 --pyright-only, stats, triage, only_pyright relations
```

`gen_pass.sh` passes `--llm file:/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/runs/day8/inbox`, `PYTHONHASHSEED=0`, 3 retries, output `runs/day8/gen`, log `campaign/day8/gen-pass.log`, status `Assignment_2/.agents/tasks/day8-gen-status.json`. `campaign/day8/gen_worker.sh` and `answer_pending.sh` differ from the Day-7 files only in paths and comments (`phase2/syntax.out`).

## 9. Checks run in this step

| Check | Result |
|---|---|
| `bash -n` on the 6 scripts, `py_compile` on the 2 Python helpers | ok (`phase2/syntax.out`) |
| `gen-pass-dryrun.sh` | `pending=250 written=0`, 250 distinct prompt keys, 0 shared with Day 7 |
| `check_reserve.py` | 9 parents, 0 flagged |
| `check_hits.py 0.80` | 42 files; 0 with problems |
| Crash probe | section 4 |
| pytest, kb-selftest | not re-run: no code, KB or pin changed in this step (phase 1: 604 passed, 20 PASS / 0 FAIL) |

## 10. Risks and open points

* **KB entries are not done.** Section 2.3 lists three. Without them the judge run leaves about 20 to 25 findings of classes A to D live; with them, each needs a Day-7 replay and the control replays first.
* **Class F is a candidate, not a result.** "mypy rejects an overloaded `__post_init__` that one item satisfies" rests on the seed's own header and 4 findings; the tracker search was 3 term sets (`gh search` matches words, not meaning). No playground was used.
* **Section 2.1 mechanism.** Reproduced for `int` and `Point` subjects; the `list[str]` member was not traced.
* **Crash share.** If the 40 crash programs again give 0 live crash findings except the pyright pair, the next morning should drop `A_ty_escape` and the ParamSpec identity parent.
* **Fresh generation cannot avoid known families** (`cmd_generate` has no avoid option); adding one is a code change I did not make.
* **Memory.** `A_ty_4898` can produce TY-4899-style programs that reach the 4 GB shim cap; use `--jobs 14` as in `judge.sh`, check `journalctl` for oomd afterwards and fall back to `--jobs 8` if a kill appears.
* **Accidental Day-7 script run (repaired).** While looking up the Day-7 dry-run script I ran `campaign/day7/partB/gen-pass-dryrun.sh` by mistake. It rebuilt `runs/day7/parents`, and the two groups whose parents had moved to `runs/hits-dropped` (`A_ty_4148`, `A_ty_protocol_capped`) came out empty. I restored the four files from `runs/hits-dropped` (`phase2/scripts/restore_d7parents.sh`, `restore_d7parents.out`: group sizes 3, 2, 1, 9, 5 as in `day7-morning.md`). The files are copies, git-ignored, and moved (not edited) between directories, so nothing was lost. It also wrote `/tmp/d7-dryrun` only; `runs/day7/{inbox,gen,out}` and `campaign/day7/gen-pass.log` were not touched.
* `campaign/day7-report.md` still carries an uncommitted edit that is not mine (`se=0-9rches`); not committed. The untracked `-l`, `.kiro/` and `findings/2026-10-27-llm-run/` are not touched.
