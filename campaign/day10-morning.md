# Day 10 morning decisions (Plan §3 "Every morning") and generation plan, phase 2

Branch `campaign/day10-p2`, local only; nothing pushed, no GitHub write (no `gh` call in this step). Pins unchanged: mypy 2.4.0, ty 0.0.97, pyright 1.1.414, CPython 3.13.16 (`phase2/results/crash-parents-probe.done`).
Inputs: `campaign/day9-morning.md` (the model for this file), `campaign/day9-report.md`, `campaign/day9-run-log.md`, `campaign/day10-run-log.md` (phase 1: ty `deprecated` on `@contextmanager` matcher, 688 passed, kb-selftest 20/0), and the Day-9 reports replayed on the Day-10 KB, `runs/day10/replay/day9` (250 programs, live 224 to 199).
Generation was **not** run in this step. The next step runs `campaign/day10/mk_groups.sh`, `campaign/day10/gen_pass.sh`, `campaign/day10/answer_pending.sh`, then `campaign/day10/judge.sh`. Evidence of this step is in `campaign/day10/phase2/` (`results/`, `scripts/`). Every number below was read from a file in `results/`; the budget numbers come from the dry run (`results/budget.out`).

## 0. What "new" means today (assumption, please confirm)

Requirement (ii) asks for new areas and new mutation operators over exhausted families. After Day 9 **no area and no operator is unused**: all 24 areas and all 23 operators of `typediff` have appeared in the prompts of Days 3 to 9 (`results/usage-by-day.out`). Phase 1 of Day 10 added no operator or area, and this step changes no code. So "new" is read as **newest or least used**:

* areas: the two Day-9 areas (`context_managers`, `dunder_dispatch`, one day each) and the five old areas with the fewest prompts over Days 3 to 9 (`final_classvar` 24, `abstract_classes` 26, `gradual_any` 33, `typeddict` 52, `paramspec_concatenate` 93, with `callables` 111 kept for its 1.67 live per program on Day 9);
* operators: the eight with the least use (`gradual_injection` 3 prompts in all, `union_widen` 7, `literal_injection` 8, `inheritance_diamond` 10, `scope_relocation` 14, all on Day 8 only; `decorator_wrapping` 25 and `descriptor_property` 25, not since Day 7; `generic_nesting` 45, not since Day 8) and the two Day-9 instruction operators, on two parents only.

If you want a truly new operator or area, that is a code change (a phase-1 style step with tests) and would have to come before generation. The safe default, used here, is the plan above. Nothing in it blocks the later steps.

## 1. Changes to `runs/hits` (40 files before, 39 now)

`runs/` is git-ignored; both actions are reversible (`rm`, `mv`). Script: `phase2/scripts/promote_retire.sh` (`results/promote_retire.out`).

| Parent | Action | Why |
|---|---|---|
| `d9p_context_managers_swallowed_name_possibly_unbound` (new) | **promoted** from the Day-9 fresh program `runs/day9/gen/context_managers/gen0_b82d2e9e.py` | Draft 10 (D9-10): a name bound in a `with` whose `__exit__` returns `bool` and used after the block; CPython `UnboundLocalError`, pyright reports it, ty only under an off-by-default rule, mypy not even with `possibly-undefined`. Reproduces alone (`results/alone.out`: `gen0_b82d2e9e` 1 live finding, `gen21_6ee04c3a` the same), highest similarity to any file of `runs/hits` 0.33 (< 0.80). `context_managers` had no parent in `runs/hits`; this is the only one. The copy has one area/hypothesis/origin triple and a "Vary:" sentence, as the Day-4 and Day-9 promotions did |
| `d6p_typevartuple_unpack_pep695_paramspec_default_mypy_subscript` | **retired** (to `runs/hits-dropped`) | Rediscovery only. Its 4 Day-9 mutants gave 19 live findings on the Day-10 KB, 0 strong, 0 dismissed (`results/yield-day9-on-day10kb.out`). The rows by message template (`results/parent-live-rows.out`): 8 are mypy's "Can only replace ParamSpec with a parameter types list or another ParamSpec" (draft 5, filed as mypy#22375), 10 are `assert-type` (6) and `reveal def (*Any, **Any)` (4) rows, 1 is `call-arg`; 5 of the 19 also carry a `[valid-type]` message. Classified by message template, rows not reduced one by one |
| `d5p_descriptors_one_decorator_dunders_pyright_rangeerror` | **retired** (to `runs/hits-dropped`) | 3 Day-9 mutants, 1 live row (pyright-only "Object of type .. is not callable", the dunder trade-off of D9-9), 0 pyright crash events. Its sibling `d5p_descriptors_decorated_get_pyright_rangeerror` stays as the pyright `RangeError` reference (draft 7); both still crash pyright rc 2 (`results/probe-counts.out`) |
| `d3p_generics_callable_attr_contravariant` | stays, **revisit test today** | Day 9: 3 programs, 0 live, 2 dismissed (it had 3 live on Days 7 and 8). Its Day-8 mutant `rsv_generics_variance_7ffc3316` still gives 8 live in 4 programs. It gets 3 programs in `N_types` with two operators it never had (`union_widen` 1, `literal_injection` 2). If that gives 0 live again, the Day-11 morning retires it |
| `d3p_typevartuple_unpack_paramspec_default_after_tvt` | stays, 4 programs (was 4), other operators | Day 9: 10 live, 3 strong, all the parent's own runtime `TypeError` (python/typing#2211) and the filed draft 5 message. Kept as the crash-hunt parent for the TypeVarTuple default shape; operators `generic_nesting` 2, `union_widen` 1, `gradual_injection` 1 |
| `d7p_tuples_unpacking_partial_unpack_except_ty`, `d4v_ty_attr_eq_narrow_unreachable`, `d3p_narrowing_user_index_assign_stale` | stay, not mutated today | live / dismissed on the Day-10 KB: 2 / 7, 2 / 14, 1 / 9. The first is the draft-6 parent (its 2 live rows are `reveal` mismatches, `int \| None` against a literal); the other two have 2 `reveal Never` rows (ty only) and 1 `unsupported-operator` row. Small counts, rows not read further, so no programs today |
| `d4v_protocols_expanding_self_receiver`, `d6p_protocols_expanding_self_receiver_{dict_arg,pep695,tuple_nesting}_ty`, `d6p_async_generators_protocol_flatten_overflow_ty` | stay, **never mutated** | ty rc 134 on all five, no KB entry (draft 1); generating from them recreates live crash findings |
| the seven ty-crash parents in `runs/hits-dropped` (six rc 134 closed by `TY-4148`, `TY-4882`, `TY-4898`, `TY-4900`; one rc 101 closed by `TY-4899`) | stay retired | same exit codes as on Day 9; the `TY-4900` escape test passed on Day 9 (8 programs, 4 crash events, all closed, 0 escapes), so no crash group for them |

Strong-evidence candidates (`results/strong_live.out`, 10 findings in 8 programs, the same set as Day 9): all 8 reproduce alone with the same strong evidence (`results/alone.out`); similarity to `runs/hits`: 0.70, 0.56, 0.53, 0.48, 0.43, 0.40, 0.36, 0.33, none at or above 0.80, no pair at or above 0.60. **None is promoted**, for the reasons recorded in `day9-report.md` section 5 (D9-1 duplicate of mypy#8595, D9-2 invalid program, D9-3 and the `paramspec_default_after_tvt` and `reflected_op` mutants are rediscoveries of existing parents, D9-4 to D9-7 duplicates, D9-8 gradual guarantee).

`.venv/bin/python campaign/day4m/check_hits.py 0.80`: before **40 files; 0 with problems**, after the promotion and the two moves **39 files; 0 with problems**, no near-duplicate pair (`results/check_hits-before.out`, `check_hits-after.out`, `check_hits-final.out`).

Git: the two retired files were tracked (force-added on Days 5 and 6), so their move shows as two deletions under `runs/hits`; they are committed with this step (tracked files under `runs/`: 8 to 6). The copies are in `runs/hits-dropped` and in git history. The promoted file is not force-added (as on Days 8 and 9).

Areas with no parent in `runs/hits` after the promotion (`results/areas-without-hits-after.txt`): `paramspec_concatenate`, `typeddict`, `overloads`, `match_statement`, `dataclasses`, `self_classmethods`, `final_classvar`, `abstract_classes`. `context_managers` now has one parent, `dunder_dispatch` one.

## 2. Decisions

* **D-1. One promotion, two retirements, no KB entry.** No code, KB or pin changed in this step, so pytest and kb-selftest were not re-run (phase 1: 688 passed, 20 PASS / 0 FAIL).
* **D-2. The three KB entries queued on Day 8 are still not implemented** (`TY-NONFINAL-PATTERN`, `ASSERT-NEVER-ALL-REJECT`, wider `JOIN-VS-UNION`), nor `MYPY-8595`. The plan sends **0 fresh programs** to `match_statement`, `recursive_aliases`, `dataclasses`, `tuples_unpacking`, `async_generators` (0 live in 15 Day-9 programs) and 9 programs to `descriptors_properties` and `enums_literals` together, all through parents (section 3).
* **D-3. A new candidate for that queue, not verified and not written:** ty's `callable()` narrowing of a non-final class (`int & ((...) -> object)`, `int & ~Top[(...) -> object]`) gives 13 live rows in 3 Day-9 programs (`narrowing_builtin/gen1_f8b8838c`, `gen3_f348b592`, `gen7_46ec78af`; `results/reserve-candidates-rows.out`). Same mechanism as `TY-NONFINAL-PATTERN` (ty keeps the possibility that a subclass is callable). Those three programs are therefore not reserve parents and `narrowing_builtin` gets no fresh program (3 programs reach it through parents).
* **D-4. Three families reproduced in 4 of 4 mutants and are leads for the verification step, not for more programs:** mypy reads `property` on the class object as `Overload(def (self) -> float)` and reports `overloaded function has no attribute "fget"` (`rsv_descriptors_properties_92c10e28`, 4 programs, 2 live rows each); ty rejects a lambda against `Sink[float]` / `Sink[int]` (`rsv_generics_variance_7ffc3316`, 4 programs, 8 live, all `only_ty`; in `..mut0_3c28536f` pyright also reports 2 of the 3 rows, so it may be a shared rejection that the matcher cannot see); ty reveals `Unknown` for an overload call with a keyword flag (`rsv_overloads_186f739e`, 4 programs, 4 live). None has been reduced or searched upstream. Only the generics one is a reserve parent today, with other operators.
* **D-5. The Day-9 operators with no yield get no group:** `async_generator_wrap` (`O_async` 0 live in 9 programs), `python_version_flip` (`O_version` 0 in 6), `variance_flip` and `bound_constraint_swap` (`O_generics` 2 in 18), `protocol_vs_abc` (`O_protocol` 2 in 6), and `C_generic_rec` (0 live, 4 crash events all closed). `overload_reorder` stays with 9 programs (`O_overload` 7 live in 8). All from `results/yield-day9-on-day10kb.out`.

## 3. Budget (250 programs, all generated)

Read from the dry-run inbox (`phase2/scripts/budget.py` -> `phase2/results/budget.out`), not hand-computed. The rows partition the 250.

| Share | Programs | Groups and operators |
|---|---|---|
| Fresh, **newest areas** | 26 | `context_managers` 18, `dunder_dispatch` 8 |
| Fresh, thin and low-count areas | 73 | `abstract_classes` 8, `gradual_any` 8, `paramspec_concatenate` 6, `typeddict` 6, `callables` 5, `constructors_metaclasses` 5, `final_classvar` 5, `inheritance_mro` 5, `overloads` 5, `self_classmethods` 5, `protocols` 4, `generics_variance` 4, `narrowing_user` 4, `typevartuple_unpack` 3 |
| **New (least-used) operators**, 4 groups x 8 parents x 3 | 96 | `N_flow` 24 (`scope_relocation` 16, `gradual_injection` 8), `N_types` 24 (`literal_injection` 16, `union_widen` 8), `N_class` 24 (`inheritance_diamond` 16, `descriptor_property` 8), `N_wrap` 24 (`generic_nesting` 16, `decorator_wrapping` 8) |
| Day-9 instruction operators, second round | 12 | `H_new` (2 promoted parents): `exit_swallow_flip` 6, `dunder_instance_shadow` 6 |
| `overload_reorder` | 9 | `O_overload` 3 parents x 3 |
| Crash families | 10 | `C_pyright_range` 6 (`scope_relocation` 2, `descriptor_property` 1, `decorator_wrapping` 1, `union_widen` 1, `gradual_injection` 1), `C_tvt` 4 (`generic_nesting` 2, `union_widen` 1, `gradual_injection` 1) |
| Pass-2 reserve | 24 | `R_reserve` 6 parents x 4 (`scope_relocation`, `union_widen`, `literal_injection`, `gradual_injection`, 6 each) |
| **Total** | **250** | 99 fresh + 151 with an operator |

Of the 151 operator prompts, **142 (94 %) use a least-used operator or one of the two Day-9 instruction operators** (130 + 12); the other 9 are `overload_reorder`. The three operators that carried Days 3 to 8 get no prompt (`feature_crossover` 366 prompts over Days 3 to 9, `runtime_witness` 201, `narrowing_construct_swap` 187). Operators of the 250 (`budget.out`), with their use on Days 3 to 9 (`usage-by-day.out`):

| Operator | Prompts Days 3 to 9 (days) | Day 10 |
|---|---|---|
| `gradual_injection` | 3 (1) | 16 |
| `union_widen` | 7 (1) | 16 |
| `literal_injection` | 8 (1) | 22 |
| `inheritance_diamond` | 10 (1) | 16 |
| `scope_relocation` | 14 (1) | 24 |
| `decorator_wrapping` | 25 (2) | 9 |
| `descriptor_property` | 25 (2) | 9 |
| `generic_nesting` | 45 (3) | 18 |
| `dunder_instance_shadow` | 29 (1) | 6 |
| `exit_swallow_flip` | 23 (1) | 6 |
| `overload_reorder` | 10 (1) | 9 |
| (fresh, no operator) | | 99 |

Programs per area as the generator will see it (the `Feature area:` line of the prompts; `budget.out`): context_managers 32, paramspec_concatenate 19, abstract_classes 18, gradual_any 18, callables 17, overloads 17, narrowing_user 16, typeddict 15, dunder_dispatch 14, final_classvar 14, generics_variance 14, inheritance_mro 14, self_classmethods 11, constructors_metaclasses 8, typevartuple_unpack 7, descriptors_properties 6, protocols 4, enums_literals 3, narrowing_builtin 3. **Zero** for match_statement, recursive_aliases, dataclasses, tuples_unpacking, async_generators. Newest areas 46 (18 %), thin areas 84 (34 %), exhausted families (`descriptors_properties`, `enums_literals`) 9 (3.6 %). The ten areas that took 230 of Day 8's programs (`abstract_classes`, `dataclasses`, `descriptors_properties`, `final_classvar`, `match_statement`, `overloads`, `recursive_aliases`, `self_classmethods`, `tuples_unpacking`, `typeddict`) got 43 on Day 9 and get 81 today: `abstract_classes` 18, `typeddict` 15, `final_classvar` 14, `overloads` 17, `self_classmethods` 11, `descriptors_properties` 6, and 0 for `dataclasses`, `match_statement`, `recursive_aliases`, `tuples_unpacking`. The rise is on purpose and sits in three thin areas (`abstract_classes`, `typeddict`, `final_classvar`: 26, 52 and 24 prompts over Days 3 to 9) plus `overloads` and `self_classmethods`; the areas whose live rows are queued for the KB (`match_statement`, `recursive_aliases`, `dataclasses`, `tuples_unpacking`) stay at 0.

Dry run of `campaign/day10/gen-pass-dryrun.sh` (`gen_pass.sh` against the scratch inbox `/tmp/d10-dryrun`, no answers; `results/gen-pass-dryrun.out`): **`pending=250 written=0`**; `inbox_check.py`: `prompts=250 (retry prompts=0) answers=0 answered=0 pending=250 orphan_answers=0 malformed_keys=0`; 250 prompt files, **250 distinct keys**; **0 keys shared with the inboxes of Days 3 to 9** (`results/overlap-prior.out`). Nothing under `runs/day10/inbox` or `runs/day10/gen` (`results/runs-day10-listing.out`: both absent; only `parents` and `replay`), and `day10-gen-status.json` does not exist (`results/gate-dir-listing.out`). The first dry run shared 20 keys with Days 6 to 8 (same parent or area, operator and `n`). The slots were changed and the dry run repeated until 0 were shared (`results/shared-key.out` is empty): `final_classvar` 6 to 5, `typevartuple_unpack` 4 to 3, `gradual_any` 6 to 8 (keeps the 99 fresh), `N_types` from `union_widen` 2 / `literal_injection` 1 to 1 / 2, `N_wrap` from `decorator_wrapping` 2 / `generic_nesting` 1 to 1 / 2, `C_pyright_range` from two operators to five, the seed `final_classvar/final_overrides` replaced by the harvested `pyright__final3`, the harvested `abstract_classes/pyright__abstractClass3` of `N_types` replaced by the "revisit" parent that had been in `N_wrap`, which was given `hv_generics_variance__conformance__generics_upper_bound`. Group sizes (`mk_groups.sh` output in the dry run): `C_pyright_range 1, C_tvt 1, H_new 2, N_class 8, N_flow 8, N_types 8, N_wrap 8, O_overload 3, R_reserve 6`.

## 4. Crash-parent probe on ty 0.0.97

`phase2/scripts/probe_crash_parents.sh` (every file of `runs/hits` and `runs/hits-dropped` with ty, sequential, memguard shim, 90 s limit; then the mypy and pyright crash parents) -> `results/crash-parents-probe.tsv`, counts in `results/probe-counts.out`. Run before the promotion and the moves. 60 ty rows (40 + 20): rc 134 on 11, rc 101 on 1, rc 1 on 21, rc 0 on 27. mypy rc 137 on `d3p_crash_mypy_segv_recursive_tvt_default_alias`; pyright rc 2 `RangeError` on both `d5p_*_rangeerror` parents. **The 63 files probed on both days give the same exit code on both days** (0 differences), so the crash picture of Day 9 holds: the 5 draft-1 parents in `runs/hits` (ty rc 134, no entry, never mutated) and 6 closed ty crash parents in `runs/hits-dropped`. No crash family has an open escape test today, so crash programs are 10 (4 %; Day 9: 22 plus 8 in `typevartuple_unpack`).

## 5. Pass-2 reserve, 24 programs, spent today

Parents: Day-9 programs with a live finding on the Day-10 KB that is not in a family already filed, closed or queued (`results/live-programs-by-area.out`, `reserve-candidates-rows.out`, `reserve-candidates-rows-2.out`). `campaign/day10/check_reserve.py` (`results/reserve-check.out`): 6 parents, 1 to 3 live findings each, closest `runs/hits` file 0.33 to 0.55, closest other reserve parent 0.31 to 0.36 (threshold 0.80), **0 flagged**. They are copied as `rsv_<area>_<hash>.py` into `R_reserve`; they are not added to `runs/hits`.

| Parent (Day-9 program) | Live | Why |
|---|---|---|
| `context_managers/gen5_c8eb51b8` | 1 | `reveal_type(x)` after a `with`: ty `Literal[1, 2]`, mypy `int \| None`, pyright `Literal[1, 2] \| None` |
| `context_managers/gen15_d3110ded` | 1 | `reveal_type(x)` after a `with`: ty `int`, mypy and pyright `int \| None` |
| `generics_variance/rsv_generics_variance_7ffc3316__mut0_3c28536f` | 3 | ty-only lambda rejection against `Sink[int]` / `Sink[float]` (D-4) |
| `paramspec_concatenate/..decorator_signature__mut1_29247984` | 1 | ty reveals `(...) -> Unknown` for a decorated function, mypy and pyright the signature |
| `abstract_classes/rsv_abstract_classes_5a90804c__mut0_cf2683fb` | 3 | ty `AttrSource \| (Fixed & Source)` against mypy and pyright `AttrSource`; two pyright-only property overrides. The thinnest old area |
| `gradual_any/gen6_76921a4b` | 1 | `reveal_type(obj)`: ty `Never`, pyright `object`, mypy silent |

Left out, with the reason: the three `callable()` programs (D-3), the three stable families as reserve parents except generics (D-4), `dunder_dispatch` programs with `len()` / `list()` / `in` rows (the documented trade-off, D9-9), `protocols/gen1_21fd81b8` and the abstract-property override (pyright-only `reportIncompatibleMethodOverride`, same family as the abstract reserve parent), `constructors_metaclasses/gen6_d7dc98c9` (mypy `type-abstract`, a known mypy behaviour), `gen1_c86958a8` (mypy#8595). Operators: `scope_relocation`, `union_widen`, `literal_injection`, `gradual_injection`, 1 per parent (Day 9 used `runtime_witness` and `feature_crossover`, the two most used operators, plus `annotation_spelling_swap` and `qualifier_toggle`, which only Day 8 had run).

## 6. Operator groups (96 + 12 + 9 programs)

Parents are picked for what the operator can move, from five places (`mk_groups.sh`): `runs/hits`, `runs/hits-dropped`, hand seeds, harvested conformance/mypy/pyright programs, Day-9 programs (reserve only). The operators other than the two of `H_new` are bare names (the generator reads the name and guesses, DESIGN.md §6), so the judge run is also the first real measurement of the yield of eight operators that have barely run.

| Group | Parents (8 each unless noted) | Operators |
|---|---|---|
| `N_flow` | hits `d4v_ty_alias_loop_backedge`, `d4v_ty_flag_or_else_never`, `s3r1_ty_type_equality_narrowing_any`, `s3r1_mypy_class_base_forward_ref`; harvested `narrowing_user/{conformance__narrowing_typeis, conformance__narrowing_typeguard, pyright__typeIs3}`, `gradual_any/conformance__exceptions_context_managers` | `scope_relocation` 2, `gradual_injection` 1 |
| `N_types` | seeds `typeddict/readonly_notrequired`, `overloads/literal_flag_overload`; harvested `typeddict/{conformance__typeddicts_required, pyright__typedDict10}`, `final_classvar/{pyright__final2, pyright__final3, mypy__check_final__testFinalDefiningInstanceVar}`; hits `d3p_generics_callable_attr_contravariant` (revisit) | `union_widen` 1, `literal_injection` 2 |
| `N_class` | harvested `inheritance_mro/{conformance__classes_override, pyright__mro2, pyright__methodOverride2}`, `abstract_classes/{mypy__check_abstract__testImplementingAbstractMethodWithMultipleBaseClasses, pyright__abstractClass5}`, `constructors_metaclasses/conformance__constructors_call_metaclass`, `self_classmethods/conformance__generics_self_basic`; seed `self_classmethods/self_classmethod_param` | `inheritance_diamond` 2, `descriptor_property` 1 |
| `N_wrap` | seed `paramspec_concatenate/decorator_signature`; harvested `callables/{conformance__callables_subtyping, conformance__callables_kwargs, conformance__callables_annotation}`, `paramspec_concatenate/{conformance__generics_paramspec_components, conformance__generics_paramspec_semantics}`, `generics_variance/conformance__generics_upper_bound`; hits `d3p_callables_partial_too_many_positional` | `decorator_wrapping` 1, `generic_nesting` 2 |
| `H_new` (2 parents) | hits `d8p_dunder_dispatch_annotation_only_call`, `d9p_context_managers_swallowed_name_possibly_unbound` (promoted today) | `exit_swallow_flip` 3, `dunder_instance_shadow` 3 |
| `O_overload` (3 parents) | harvested `overloads/{conformance__overloads_consistency, conformance__overloads_evaluation, conformance__overloads_definitions}` | `overload_reorder` 3 |

The thin areas get most of the parents: `typeddict` and `final_classvar` have no parent in `runs/hits`, so their only entries are the harvested and seed programs of `N_types`. `H_new` keeps the two instruction operators only where each has a promoted parent that showed a finding.

## 7. Fresh programs, 99

| Area | Programs | Prompts Days 3 to 9 | Reason |
|---|---|---|---|
| context_managers | 18 | 22 (Day 9 only) | newest area, produced draft 10 from fresh programs; `__exit__` swallowing, reachability after `with` |
| dunder_dispatch | 8 | 28 (Day 9 only) | fewer than Day 9: the live rows are the documented trade-off (D9-9) |
| abstract_classes | 8 | 26 | thinnest old area, 2.0 live per program on Day 9 |
| gradual_any | 8 | 33 | few programs overall; 4 live in 19 Day-9 programs on the Day-10 KB, so also a check for noise |
| paramspec_concatenate | 6 | 93 | 3 programs on Day 9; no parent in `runs/hits` |
| typeddict | 6 | 52 | no program since Day 8, 3 live in 16 on the Day-9 KB |
| callables, constructors_metaclasses, final_classvar, inheritance_mro, overloads, self_classmethods | 5 each (30) | 111, 71, 24, 71, 72, 65 | Day 9 gave 1.67, 1.08, no program, 0.77, 0.90, 1.00 live per program |
| protocols, generics_variance, narrowing_user | 4 each (12) | 90, 98, 82 | small share to keep a baseline |
| typevartuple_unpack | 3 | 73 | Day 9 had 34 live in 16, mostly the filed draft 5 and typing#2211 |
| **Total** | **99** | | |

`typediff generate` still has no avoid hook, so fresh programs may meet known families again.

## 8. How the next step runs it

```
bash campaign/day10/mk_groups.sh > out.txt 2>&1      # rebuild runs/day10/parents/* (sizes: C_pyright_range 1, C_tvt 1, H_new 2, N_class 8, N_flow 8, N_types 8, N_wrap 8, O_overload 3, R_reserve 6)
bash campaign/day10/gen_pass.sh 0 > out.txt 2>&1     # then answer_pending.sh, then gen_pass.sh 1, 2 ... until pending=0 written=250
bash campaign/day10/answer_pending.sh > out.txt 2>&1 # headless kiro-cli --agent-engine v3 --model claude-haiku-5.5 --effort medium, 5 prompts per session, 4 sessions at once
bash campaign/day10/judge.sh > out.txt 2>&1          # kbloop_run --jobs 14 --pyright-only, stats, triage, only_pyright relations
```

`gen_pass.sh` passes `--llm file:/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/runs/day10/inbox`, `PYTHONHASHSEED=0`, 3 retries, output `runs/day10/gen`, log `campaign/day10/gen-pass.log`, status `Assignment_2/.agents/tasks/day10-gen-status.json`. `gen_worker.sh`, `answer_pending.sh`, `judge.sh`, `check_reserve.py`, `only_pyright_relations.py`, `check_gen_sessions.py`, `live_by_area.py`, `operator_follow.py` and `gen-pass-dryrun.sh` differ from the Day-9 files only in paths and comments (`results/syntax.out` holds the diffs; `live_by_area.py` is identical; `operator_follow.py` also says that only `H_new` has an instruction to check); `gen_pass.sh` and `mk_groups.sh` are new content. The generator is never Opus, `gpt-*` or `sol-5.6` (`check_gen_sessions.py` checks the sessions afterwards). The judge writes `campaign/day10-stats.txt`, `campaign/day10-triage.txt`, `campaign/day10-only-pyright-relations.txt`.

## 9. Checks run in this step

| Check | Result |
|---|---|
| `bash -n` on every shell script under `campaign/day10`, `py_compile` on every Python file there | 15 shell scripts and 12 Python files, 27 ok, 0 bad (`results/syntax.out`, final run after the last edit) |
| `gen-pass-dryrun.sh` | `pending=250 written=0`, 250 distinct prompt keys, 0 shared with Days 3 to 9 |
| `check_reserve.py` | 6 parents, 0 flagged |
| `check_hits.py 0.80` | 40 files before, 39 after, 0 problems both times |
| Crash probe | section 4 |
| pytest, kb-selftest | not re-run: no code, KB or pin changed in this step |

## 10. Risks and what to read after the judge run

* **The eight bare-name operators are untested on a real model.** The generator reads `scope_relocation` or `union_widen` and guesses, so some programs may be near-copies of the parent. After generation, compute the `check_hits.py` style similarity of each mutant to its parent per group; a group with a median above 0.8 is a failed operator, not a clean result. The two instruction operators in `H_new` can be checked with `campaign/day10/operator_follow.py`.
* **Yield per program will probably fall.** Day 9's live rate came partly from the TVT / ParamSpec rows (19 + 10 live in 8 programs, now retired or capped) and from `dunder_instance_shadow` rows (36 in 21 programs). Neither is repeated at that scale, so a lower live count is the expected result of the plan, not a regression. Compare "live without `only_pyright`" per group, not the total.
* **`N_types` / `N_class` use harvested mypy and pyright test programs as parents.** Some are long, and their `expect-error` comments follow mypy or pyright test conventions, so the preflight may reject more of them than the hand seeds. Check `failed (` lines in `gen-pass.log` for rejected generations.
* **The "revisit" test:** `d3p_generics_callable_attr_contravariant` (3 programs in `N_types`). Retire it on Day 11 if its mutants give 0 live again.
* **Leads waiting for a verification step** (not for programs): D-3 (`callable()` narrowing) and D-4 (the three stable families). Drafts 6 to 10 remain unfiled.
* **Memory.** No memory-heavy group is planned (no TY-4900 parent, no mypy `rc 137` parent). `--jobs 14` as in `judge.sh`; check `journalctl` for oomd afterwards and fall back to `--jobs 8` if a kill appears.
* **Untouched, not mine:** `campaign/day7-report.md` and `campaign/day8/phase6/results/commit.out` carry uncommitted edits; untracked `-l`, `.kiro/` and `findings/2026-10-27-llm-run/` are left alone. Nothing was pushed.
