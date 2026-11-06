# Day 9 morning decisions (Plan §3 "Every morning") and generation plan, phase 2

Branch `campaign/day9-p2`, local only; nothing pushed, no GitHub write (no `gh` call at all in this step). Pins unchanged: mypy 2.4.0, ty 0.0.97 (`ty --version` in `phase2/results/crash-parents-probe.done`), pyright 1.1.414, CPython 3.13.16.
Inputs: `campaign/day8-morning.md` and `campaign/day7-morning.md` (the models for this file), `campaign/day8-report.md` (sections 5 and 7), `campaign/day9-run-log.md` (phase 1: 655 passed, kb-selftest 20/0, two new operators, two new areas), the Day-8 programs `runs/day8/gen` and their replay with the Day-9 KB, `runs/day9/day8replay` (500 files, a JSON and an MD report per program; live 155 to 152).
Generation was **not** run in this step. The next step runs `campaign/day9/mk_groups.sh`, `campaign/day9/gen_pass.sh`, `campaign/day9/answer_pending.sh`, then `campaign/day9/judge.sh`. Evidence of this step is in `campaign/day9/phase2/` (`results/`, `scripts/`, `repro/`).

The Day 9 and Day 10 requirement is to prefer **new areas and new mutation operators over exhausted families**. Day 8 sent 230 of its 250 programs to ten areas (abstract_classes 12, dataclasses 37, descriptors_properties 36, final_classvar 8, match_statement 26, overloads 26, recursive_aliases 18, self_classmethods 25, tuples_unpacking 26, typeddict 16; counts from `day8-report.md` section 3). Today those ten areas get **43** programs (17 %), all through operator groups or the reserve, none fresh (section 3).

## 1. Changes to `runs/hits` (40 files before, 41 now)

`runs/` is git-ignored; both actions are reversible (`rm`, `mv`).

| Parent | Action | Why |
|---|---|---|
| `d8p_dunder_dispatch_annotation_only_call` (new) | **promoted** from the Day-8 mutant `callables/d3p_callables_self_call_attr__mut0_5445453a` (`phase2/scripts/promote.sh`, `results/promote.out`) | The annotation-only `__call__: Step` lead of `day8-report.md` section 5: CPython raises `TypeError`, ty and pyright accept `C()()`, mypy rejects it for another reason (confidence 0.4, not strong). It is the only parent of the new area `dunder_dispatch`, and the only program that the new operator `dunder_instance_shadow` generalises. The copy has one area/hypothesis/origin triple (the Day-8 file has two) and a "Vary:" sentence, as the Day-4 promotions did |
| `d3p_callables_self_call_attr`, `d4v_callables_mutual_call_attr`, `d3p_self_classmethods_self_call_union`, `d3p_protocols_generic_protocol_stack_overflow` (hits-dropped) | **retired as mutation parents** (the Day-8 group `A_ty_escape` is gone); files stay in `runs/hits-dropped` | Day 8 escape watch: 8 programs, 7 crash events, all 7 closed (by `TY-4148`, `TY-4882` or `MYPY-22361`; 3 + 1 + 3 in the Day-8 closing-reference counts), 1 live non-crash row, 0 escapes (`day8-report.md` section 3). The Day-8 risk list said to drop the group if this repeated |
| `d3p_paramspec_identity_applied_to_itself`, `d3p_paramspec_self_annotated_dunder_call` | stay retired (hits-dropped) | Retired on Day 8 (0 live in 8 and 7 mutants) |
| `d5p_descriptors_decorated_get_pyright_rangeerror`, `d5p_descriptors_one_decorator_dunders_pyright_rangeerror` | stay, **mutated less (6 programs, was 12) and with other operators** | Day 8: 12 programs, 12 live, all `only_pyright`, 0 strong, all rediscoveries of unfiled draft 7 (D8-6). They still crash pyright (rc 2), so they remain the pyright crash reference |
| `d3p_generics_contravariant_recursive_generic_base` (hits-dropped, retired Day 4 as a 0.86 near duplicate) | **used as a parent copy** in `C_generic_rec`; file not moved | The probe found it still crashes ty 0.0.97 (rc 134). Day 8's named list did not include it. `TY-4900` closes only an *expanding* generic base (`requires: expanding_generic_base`), so a mutant with another variance or a non-expanding base may escape the entry (section 4) |
| `d4v_protocols_expanding_self_receiver`, `d6p_protocols_expanding_self_receiver_{dict_arg,pep695,tuple_nesting}_ty`, `d6p_async_generators_protocol_flatten_overflow_ty` | stay, **never mutated** | ty rc 134 on all five, no KB entry (draft 1). Generating from them recreates the 20 live crash findings of Day 6 |
| `d4v_eq_no_hash_hashable`, `d4p_inheritance_hash_none_from_eq`, `d3p_inheritance_mro_hash_none_from_eq` | stay, not mutated | partly closed by `MYPY-2455` / `TY-4941` (Day 8); no change today |
| `d4p_descriptors_readonly_prop_never` | stays, not mutated | see decision D-1 below |
| `d3p_crash_ty_panic_partial_or_none_in_loop`, `d3p_crash_ty_timeout_typeis_generic_in_loop`, `d4p_callables_crash_ty_panic_partial_loop`, `d3p_crash_ty_stack_overflow_protocol_flatten` | no generation | ty 0.0.97 gives rc 1 with diagnostics on all four (the TSV says "panic" for the first only because the word is in the file's own header comment, as on Day 8) |
| `d3p_crash_mypy_segv_recursive_tvt_default_alias` | no generation | mypy rc 137 (memory guard), the `MYPY-22361` shape that Day 7 closed 13 times |

`.venv/bin/python campaign/day4m/check_hits.py 0.80`: before **40 files; 0 with problems**, after the promotion **41 files; 0 with problems**, no near-duplicate pair (`phase2/results/check_hits-before.out`, `check_hits-after.out`, `check_hits-final.out`).

Areas with no parent in `runs/hits` after the promotion (`phase2/results/areas-without-hits-after.txt`): `paramspec_concatenate`, `typeddict`, `overloads`, `match_statement`, `dataclasses`, `self_classmethods`, `final_classvar`, `abstract_classes`, `context_managers`. `dunder_dispatch` has one parent (the promoted program).

### Decisions on the open points of phase 1

* **D-1. `d4p_descriptors_readonly_prop_never__mut0_f116e46b` (a `t.__dict__['doubled'] = 99` write) stays live; `TY-2792-READONLY` is not widened.** A `__dict__` write is not a method call or a descriptor store. Treating it as one would also close the retained parent `d4p_descriptors_readonly_prop_never` itself, which is the program that shows the bug shape. Two live rows stay in the queue; neither is mutated today.
* **D-2. The three KB entries queued on Day 8 are still not implemented** (`TY-NONFINAL-PATTERN`, `ASSERT-NEVER-ALL-REJECT`, a wider `JOIN-VS-UNION`). Writing them is code and replay work, not a morning decision. The plan does not need them today: it sends **0 fresh programs to `match_statement`** (21 live Day-8 rows, classes A to D of `day8-morning.md` section 2.1) and none to `tuples_unpacking`, `recursive_aliases` or `dataclasses`, the three areas that fed the rows the entries would close. The Day-8 rows stay live in the Day-8 triage; they do not grow today.
* **D-3. No KB entry is added in this step** (no code or KB change; pytest and kb-selftest are therefore not re-run, section 9).

## 2. The Day-8 live items re-read (which ones earn programs today)

Method: `runs/day9/day8replay` (Day-8 reports, Day-9 KB, `--pyright-only --rerun-runtime`), 152 live findings; per-area counts from the JSON (`phase2/scripts/live_by_area.py` -> `phase2/results/day8-live-by-area.txt`, `day8-live-programs.txt`); the live rows of the candidate parents printed with `phase2/scripts/show_live_rows.py` (`reserve-candidates-rows.txt`, `reserve-candidates-rows-2.txt`) and checked on the pins where a check was cheap. Two small programs were run on the pins (`phase2/repro/`).

Live Day-8 findings per area directory on the Day-9 KB: recursive_aliases 27, overloads 26, descriptors_properties 23, match_statement 21, tuples_unpacking 18, self_classmethods 12, dataclasses 12, abstract_classes 6, typeddict 3, generics_variance 3, callables 1 (sum 152; paramspec_concatenate, final_classvar and protocols 0).

Live rows of the candidate reserve parents and what they are:

| Day-8 program | Live row | Verdict | Used |
|---|---|---|---|
| `generics_variance/d3p_generics_callable_attr_contravariant__mut1_7ffc3316` | `only_ty`: `Handler[float](lambda x: ...)` rejected against `Sink[float]` (2 rows) | open: ty infers the lambda as `(x) -> None` and rejects it; pyright also reports an `reportArgumentType`; not reduced | reserve |
| `abstract_classes/rsv_abstract_classes_ae31b752__mut0_5a90804c` | `only_mypy` `arg-type` on `load(Fixed())`; `only_pyright` `reportIncompatibleMethodOverride` for a class attribute `name = 'attr'` over an abstract property (3 rows) | open: same family as the Day-8 reserve parent (6 live in 3 mutants); abstract_classes has 22 programs in 8 days, the thinnest of the old areas | reserve |
| `descriptors_properties/gen9_92c10e28` | `only_mypy` `attr-defined` "overloaded function has no attribute fget" and `reveal_mismatch` (mypy `Overload(def (self) -> float)`, ty and pyright `property`) | open: a property read on the class object; `gen11_8c4adaee` shows the same for `cached_property` (mypy `def (self: ...) -> float`, ty and pyright `cached_property[float]`). Not reproduced today | reserve (`gen9`); `gen11` left out as the same mechanism |
| `descriptors_properties/gen1_4287130f` | `only_pyright`: `Box.width.attr` "Cannot access attribute `attr` for class `int`" | open: pyright resolves `Box.width` to `int` through the descriptor; mypy and ty silent | reserve |
| `self_classmethods/gen10_22a2e020` | `only_pyright`: `HtmlBuilder.add(Builder(), 'z')` (unbound call with a base instance for `Self`) | open: ty solves `Self` per call (DESIGN.md §8), mypy silent | reserve |
| `overloads/rsv_overloads_d6e90b34__mut0_186f739e` | `reveal_mismatch`: `reveal_type(unwrap(xs, strict=True))` is `Unknown` in ty, `int \| str` in mypy and pyright | open: a ty inference gap on an overload call with a literal keyword flag | reserve |
| `descriptors_properties/d3p_descriptors_decorated_get__mut0_8d166ec7` | `only_ty` `unresolved-attribute`: `fn.__name__` on `F` bound to `Callable[..., Any]` | **NOT-A-BUG, design.** Reproduced on the pins: ty rejects `__name__` on `Callable` and on a TypeVar bound to it and links its FAQ ("not all callable objects are functions"); mypy and pyright accept (`phase2/repro/callable_name.py`, `.out`) | not used. Candidate KB entry (DESIGN_DIVERGENCE, source: the ty FAQ), not written |
| `dataclasses/gen4_fe950119` | `only_mypy` `arg-type` on `Config('svc')` for `@dataclass(kw_only=True)` | **NOT-A-BUG, noise.** Reproduced: ty (`missing-argument`, `too-many-positional-arguments`) and pyright (`reportCallIssue`) reject the call, mypy rejects it too (`call-arg` twice) and adds a third consequence message `arg-type` for the same call (`phase2/repro/kw_only_positional.py`, `.out`). All three agree the call is wrong | not used |
| `typeddict/gen7_2655c013` | `only_mypy` `call-arg` "Unexpected keyword argument `extra_items`" on a `TypedDict` class | KNOWN_LIMITATION: mypy 2.4.0 does not accept the PEP 728 keyword (read from the replay message, not run today) | not used |
| `self_classmethods/self_param_inherited__mut0_625d747c` | `only_mypy` x2, `only_pyright` x1 on `x.add(Node())` for `add(self, c: Self)` | duplicate of ty#4656 (`TY-4656` dismisses the sibling programs); two rows stay live because the program is not of the quoted-`'Self'` shape W1 fixed | not used |
| `match_statement`, `recursive_aliases`, `tuples_unpacking` live rows | see `day8-morning.md` section 2 and D-2 | exhausted; KB-queued classes | not used |

Candidate KB entries seen in this read, **not written** (they need the phase-1 routine of tests, replays and kb-selftest): `CALLABLE-NAME-ATTR` (ty FAQ, reproduced), and a "property or cached_property read on the class object" difference (two programs, not reproduced). Both are cheap after the judge run if they show up again.

## 3. Budget (250 programs, all generated)

Counts below are read from the dry-run inbox (`phase2/scripts/budget.py` -> `phase2/results/budget.out`), not computed by hand.

| Share | Programs | Groups |
|---|---|---|
| **New operators** `dunder_instance_shadow`, `exit_swallow_flip` (these two prompts carry the operator instruction; 52 prompts) | 48 + 4 | `H_dunder` 6, `D_shadow` 21, `D_exit` 21; 4 more in `C_pyright_range` |
| **Six old operators that no earlier day used** (`variance_flip`, `bound_constraint_swap`, `protocol_vs_abc`, `overload_reorder`, `python_version_flip`, `async_generator_wrap`; 57 prompts) | 47 + 10 | `O_overload` 8, `O_generics` 18, `O_protocol` 6, `O_version` 6, `O_async` 9; 10 more inside the crash groups |
| Crash families (some of the programs above, with `recursion_deepening` 6 and `invalid_type_form` 2) | 22 | `C_generic_rec` 8, `C_pyright_range` 6, `C_tvt` 8 |
| Pass-2 reserve | 24 | `R_reserve` (6 parents x 4) |
| Fresh, **new areas** | 44 | `dunder_dispatch` 22, `context_managers` 22 |
| Fresh, areas with no program on Days 7 and 8 | 65 | gradual_any 10, async_generators 6, narrowing_builtin 9, constructors_metaclasses 7, typevartuple_unpack 8, narrowing_user 9, inheritance_mro 7, protocols 7, enums_literals 2 |
| **Total** | **250** | the partition by group: 48 + 47 + 22 + 24 + 109 fresh |

Operator counts in the 250 prompts (`budget.out`): fresh (no operator) 109, `dunder_instance_shadow` 29, `exit_swallow_flip` 23, `variance_flip` 16, `bound_constraint_swap` 10, `overload_reorder` 10, `async_generator_wrap` 9, `annotation_spelling_swap` 6, `feature_crossover` 6, `protocol_vs_abc` 6, `python_version_flip` 6, `qualifier_toggle` 6, `recursion_deepening` 6, `runtime_witness` 6, `invalid_type_form` 2. So **109 of the 141 operator prompts (77 %) use an operator that no earlier day used** (the two Day-9 operators, or one of the six that Days 3 to 8 never ran). `grep -l <operator> runs/day{3..8}/inbox/*.prompt.md` gave 0 files for each of the six old operators on every day. The other 32 are the reserve (4 operators x 6 parents, all low-use) and the crash operators.

Programs per area as the generator will see it (the `Feature area:` line of the prompts): dunder_dispatch 28, generics_variance 27, context_managers 22, descriptors_properties 19, gradual_any 19, narrowing_user 18, protocols 16, typevartuple_unpack 16, async_generators 15, constructors_metaclasses 13, inheritance_mro 13, narrowing_builtin 12, overloads 10, self_classmethods 7, abstract_classes 4, callables 3, paramspec_concatenate 3, tuples_unpacking 3, enums_literals 2. **Zero** for match_statement, recursive_aliases, dataclasses, typeddict, final_classvar.

Dry run of `campaign/day9/gen-pass-dryrun.sh` (`gen_pass.sh` against the scratch inbox `/tmp/d9-dryrun`, no answers, nothing written under `runs/day9/{inbox,gen}`, no real gate file): **`pending=250 written=0`**; `inbox_check.py`: `prompts=250 (retry prompts=0) answers=0 answered=0 pending=250 orphan_answers=0 malformed_keys=0`; 250 prompt files, 250 distinct keys; **0 keys shared with the inboxes of Days 3 to 8** (`phase2/results/gen-pass-dryrun.out`, `overlap-prior.out`). The first dry run had 1 key shared with Days 3 and 4 (`C_tvt` with `feature_crossover` 1 on `d3p_typevartuple_unpack_paramspec_default_after_tvt`, key `73a744f856c44bc5`); the operator of that slot was changed to `bound_constraint_swap` and the dry run repeated. Group sizes (`phase2/results/mk_groups.out`): `C_generic_rec 2, C_pyright_range 2, C_tvt 2, D_exit 7, D_shadow 7, H_dunder 1, O_async 3, O_generics 6, O_overload 4, O_protocol 3, O_version 3, R_reserve 6`.

## 4. Crash families (22 programs), probed on ty 0.0.97

Probe: `phase2/scripts/probe_crash_parents.sh` -> `phase2/results/crash-parents-probe.tsv` (run before the promotion). Day 8 probed a named list of 21 files; today the script probes **every** file of `runs/hits` and `runs/hits-dropped` with ty (59 files = 40 + 19, sequential, memguard shim, 90 s limit), then the mypy and pyright crash parents. ty exit codes (`phase2/results/probe-counts.out`): rc 134 on 11 files, rc 101 on 1, rc 1 on 21, rc 0 on 26.

| Result | Files | KB |
|---|---|---|
| ty rc 134, stack overflow, 5 in `runs/hits` | `d4v_protocols_expanding_self_receiver`, `d6p_async_generators_protocol_flatten_overflow_ty`, `d6p_protocols_expanding_self_receiver_{dict_arg,pep695,tuple_nesting}_ty` | none (draft 1): **not mutated** |
| ty rc 134, 6 in `runs/hits-dropped` | `d3p_callables_self_call_attr`, `d4v_callables_mutual_call_attr`, `d3p_self_classmethods_self_call_union` (TY-4148), `d3p_protocols_generic_protocol_stack_overflow` (TY-4882), `d3p_paramspec_identity_applied_to_itself` (TY-4898), **`d3p_generics_contravariant_recursive_generic_base` (TY-4900, not in the Day-8 list)** | closed; only the last one is used (escape test for the entry's predicate) |
| ty rc 101, panic | `d3p_paramspec_self_annotated_dunder_call` | TY-4899, retired |
| ty rc 1, diagnostics only (former ty crash parents, fixed in 0.0.97) | `d3p_crash_ty_stack_overflow_protocol_flatten`, `d3p_crash_ty_panic_partial_or_none_in_loop`, `d3p_crash_ty_timeout_typeis_generic_in_loop`, `d4p_callables_crash_ty_panic_partial_loop` | no generation |
| ty rc 1, diagnostics only (never a ty crash) | `d3p_typevartuple_unpack_paramspec_default_after_tvt` (runtime `TypeError` as well) | `C_tvt` parent, with the second TypeVarTuple parent (ty rc 0), for the mypy/TypeVarTuple shape of draft 5 |
| mypy rc 137 | `d3p_crash_mypy_segv_recursive_tvt_default_alias` | MYPY-22361, no generation |
| pyright rc 2, `RangeError` | the two `d5p_*_rangeerror` parents | draft 7 (unfiled), PYRIGHT-11961 / 11960 |

Everything else (47 files) gives rc 0 or 1 with no crash signature.

| Group | Parents | Ops: n per parent | Programs |
|---|---|---|---|
| `C_generic_rec` | `d3p_generics_contravariant_recursive_generic_base` (ty crash), `d3p_generics_contravariant_recursive_base` (mypy crash, MYPY-22360; ty rc 0) | `variance_flip` 2, `recursion_deepening` 1, `bound_constraint_swap` 1 | 2 x 4 = 8 |
| `C_pyright_range` | the two `d5p_*_rangeerror` parents | `dunder_instance_shadow` 2, `overload_reorder` 1 | 2 x 3 = 6 |
| `C_tvt` | `d3p_typevartuple_unpack_paramspec_default_after_tvt`, `d6p_typevartuple_unpack_pep695_paramspec_default_mypy_subscript` | `recursion_deepening` 2, `invalid_type_form` 1, `bound_constraint_swap` 1 | 2 x 4 = 8 |

Crash share: 22 programs (8.8 %) in the three groups, plus 8 fresh `typevartuple_unpack` programs that the brief aims at fix-point shapes, about 12 % in total (Day 8: 40 of 250, 16 %). The reduction follows the Day-8 result: of its 16 crash events 15 were closed by an entry and the one live crash was the pyright `RangeError`. The only ty crash family that still reproduces and has no entry (draft 1) is left alone on purpose.

Why `variance_flip` on the TY-4900 pair: the entry matches an *expanding* generic base (`class C(Generic[X], N[N['C[C[X]]']])` with `N` contravariant). Flipping the variance, or changing the base so that it no longer expands, tests whether the crash survives outside the predicate. A crash that survives is a live `crash` finding: either a new trigger of #4900 or a distinct bug. The ty rc 134 itself is known; the escape is the test.

## 5. Operator groups (95 programs)

Parents are picked for what the operator can flip, from five places (`mk_groups.sh`): `runs/hits`, `runs/hits-dropped`, hand seeds, harvested conformance/mypy/pyright programs, Day-8 programs.

| Group | Parents | Op: n per parent | Programs |
|---|---|---|---|
| `H_dunder` | `d8p_dunder_dispatch_annotation_only_call` (promoted today) | `dunder_instance_shadow` 4, `exit_swallow_flip` 2 | 6 |
| `D_shadow` | `d3p_descriptors_decorated_get`, `d4v_metaclass_reflected_op`, `d3p_inheritance_mro_total_ordering_inherited_lt`, seeds `callables/positional_only_assignability`, `constructors_metaclasses/new_returns_other`, `inheritance_mro/override_lsp`, harvested `protocols/conformance__protocols_class_objects` | `dunder_instance_shadow` 3 | 7 x 3 = 21 |
| `D_exit` | `d7p_tuples_unpacking_partial_unpack_except_ty`, `d4v_ty_attr_eq_narrow_unreachable`, `d3p_narrowing_user_index_assign_stale`, seeds `narrowing_builtin/len_in_walrus`, `narrowing_user/typeis_generic`, `gradual_any/gradual_guarantee`, `self_classmethods/self_runtime_witness` | `exit_swallow_flip` 3 | 7 x 3 = 21 |
| `O_overload` | seeds `overloads/literal_flag_overload`, `descriptors_properties/descriptor_get_overload`; harvested `overloads/mypy__check_classes__testOverloadedDescriptorSelected`, `overloads/conformance__overloads_basic` | `overload_reorder` 2 | 8 |
| `O_generics` | seeds `generics_variance/{constrained_typevar,pep695_variance_inference,typevar_defaults}`, `paramspec_concatenate/decorator_signature`; hits `d3p_generics_callable_attr_contravariant`, `d3p_generics_typevar_default_refers_to_itself` | `variance_flip` 2, `bound_constraint_swap` 1 | 6 x 3 = 18 |
| `O_protocol` | seeds `protocols/{generic_callback_protocol,property_vs_attribute}`; harvested `protocols/conformance__protocols_explicit` | `protocol_vs_abc` 2 | 6 |
| `O_version` | harvested `gradual_any/{conformance__directives_version_platform,pyright__staticExpression1,pyright__unreachable1}` (reachability under `sys.version_info`) | `python_version_flip` 2 | 6 |
| `O_async` | seed `async_generators/generator_send_return`; harvested `async_generators/{pyright__generator11,pyright__async1}` | `async_generator_wrap` 3 | 9 |

Why these two new operators on these parents: `dunder_instance_shadow` has a runtime oracle (CPython looks special methods up on the type, so each use raises `TypeError`), the same kind of evidence that gave the Day-8 strong findings. `exit_swallow_flip` is aimed at reachability and narrowing after a `with` block, where ty's unreachable-code handling (`d4v_ty_attr_eq_narrow_unreachable`) and exceptional-flow handling (draft 6) have already produced bugs. The `O_*` operators are bare names (the generator reads the name and guesses, DESIGN.md §6); that is how the 21 old operators work, so their yield is also a first measurement of operators nobody had run.

## 6. (c) The pass-2 reserve, 24 programs, spent today

Parents: Day-8 programs of non-exhausted areas with a live finding in `runs/day9/day8replay` that is not in a family queued for the KB (section 2). `campaign/day9/check_reserve.py` (`phase2/results/reserve-check.out`): 6 parents, each has 1 to 3 live findings, closest `runs/hits` file ratio 0.31 to 0.56, closest other reserve parent 0.29 to 0.44 (threshold 0.80), **0 flagged**. They are copied as `rsv_<area>_<hash>.py` into `R_reserve`; they are not added to `runs/hits`.

| Parent (Day-8 program) | Live | Why it is a parent |
|---|---|---|
| `generics_variance/..callable_attr_contravariant__mut1_7ffc3316` | 2 | ty-only lambda rejection against a contravariant `Sink[float]` |
| `abstract_classes/rsv_abstract_classes_ae31b752__mut0_5a90804c` | 3 | pyright/mypy abstract-property differences; the thinnest old area |
| `descriptors_properties/gen9_92c10e28` | 2 | property read on the class object, mypy `Overload(...)` |
| `descriptors_properties/gen1_4287130f` | 1 | pyright-only attribute error through a descriptor on the class |
| `self_classmethods/gen10_22a2e020` | 1 | pyright-only unbound `Self` call |
| `overloads/rsv_overloads_d6e90b34__mut0_186f739e` | 1 | ty `Unknown` for an overload call with a keyword flag |

Operators: `runtime_witness` 1, `feature_crossover` 1, `annotation_spelling_swap` 1, `qualifier_toggle` 1 per parent (the last two ran only on hand seeds on Day 8). 6 x 4 = **24**. Considered and left out, with the reasons in section 2: `decorated_get__mut0_8d166ec7` (ty FAQ), `dataclasses/gen4_fe950119` (mypy consequence message), `typeddict/gen7_2655c013` (PEP 728 limitation), `self_param_inherited__mut0_625d747c` (ty#4656), all `match_statement`, `recursive_aliases`, `tuples_unpacking` rows (exhausted, KB-queued).

## 7. Fresh programs, 109

| Area | Programs | Last generated | Reason |
|---|---|---|---|
| dunder_dispatch | 22 | never (new area) | special methods looked up on the type; runtime oracle |
| context_managers | 22 | never (new area) | `__exit__` return type, swallowing, reachability after `with` |
| gradual_any | 10 | Day 6 (14 programs ever) | least generated old area |
| async_generators | 6 | Day 6 (21) | `O_async` and `D_exit` also touch it |
| narrowing_builtin | 9 | Day 6 (34) | loop-widening and alias-condition bugs came from here (hits `d4v_ty_alias_loop_backedge`) |
| constructors_metaclasses | 7 | Day 6 (52) | 4 parents in `runs/hits`; metaclass operators are dunder-adjacent |
| typevartuple_unpack | 8 | Day 6 (54) | crash hunting with the mypy/ty TypeVarTuple shapes |
| narrowing_user | 9 | Day 6 (64) | TypeIs/TypeGuard and user-index narrowing, 3 parents |
| inheritance_mro | 7 | Day 7 (58) | `__hash__`/`__eq__` family partly closed; new MRO shapes |
| protocols | 7 | Day 8 (74; 3 programs on Day 7, 2 on Day 8) | protocol families crash ty often; only 5 programs in two days |
| enums_literals | 2 | Day 6 (102) | smallest share, 7 parents already |
| **Total** | **109** | | |

`n` differs from every earlier day for the same area (no key shared, section 3). `typediff generate` still has no avoid hook, so fresh programs may meet known families again; the new areas make that less likely.

## 8. How the next step runs it

```
bash campaign/day9/mk_groups.sh > out.txt 2>&1      # rebuild runs/day9/parents/* (sizes: C_generic_rec 2, C_pyright_range 2, C_tvt 2, D_exit 7, D_shadow 7, H_dunder 1, O_async 3, O_generics 6, O_overload 4, O_protocol 3, O_version 3, R_reserve 6)
bash campaign/day9/gen_pass.sh 0 > out.txt 2>&1     # then answer_pending.sh, then gen_pass.sh 1, 2 ... until pending=0 written=250
bash campaign/day9/answer_pending.sh > out.txt 2>&1 # headless kiro-cli --agent-engine v3 --model claude-haiku-5.5 --effort medium, 5 prompts per session, 4 sessions at once
bash campaign/day9/judge.sh > out.txt 2>&1          # kbloop_run --jobs 14 --pyright-only, stats, triage, only_pyright relations
```

`gen_pass.sh` passes `--llm file:/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/runs/day9/inbox`, `PYTHONHASHSEED=0`, 3 retries, output `runs/day9/gen`, log `campaign/day9/gen-pass.log`, status `Assignment_2/.agents/tasks/day9-gen-status.json`. `gen_worker.sh`, `answer_pending.sh`, `judge.sh`, `check_reserve.py`, `only_pyright_relations.py` and `gen-pass-dryrun.sh` differ from the Day-8 files only in paths, the reserve parent source and comments (`phase2/results/syntax.out` holds the diffs; `gen_pass.sh` and `mk_groups.sh` are new content). The judge writes `campaign/day9-stats.txt`, `campaign/day9-triage.txt`, `campaign/day9-only-pyright-relations.txt`.

## 9. Checks run in this step

| Check | Result |
|---|---|
| `bash -n` on every shell script under `campaign/day9`, `py_compile` on the 2 Python helpers | ok (`phase2/results/syntax.out`, final run after the last script was written) |
| `gen-pass-dryrun.sh` | `pending=250 written=0`, 250 distinct prompt keys, 0 shared with Days 3 to 8 |
| `check_reserve.py` | 6 parents, 0 flagged |
| `check_hits.py 0.80` | 40 files before, 41 after, 0 with problems |
| Crash probe | section 4 |
| pytest, kb-selftest | not re-run: no code, KB or pin changed in this step (phase 1: 655 passed, 20 PASS / 0 FAIL) |

## 10. Risks and what to read after the judge run

* **The new operators are untested on a real model.** Phase 1 tested that the instruction reaches the prompt (`test_generate_puts_the_instruction_of_a_new_operator_into_the_prompt`), not that Haiku follows it. After generation, count programs with `__exit__` in `D_exit`/`H_dunder` and with an annotation-only or instance-assigned dunder in `D_shadow`/`H_dunder` before judging. A group where fewer than half follow the operator should be reported, not hidden in the live count.
* **`variance_flip`, `bound_constraint_swap`, `protocol_vs_abc`, `overload_reorder`, `python_version_flip`, `async_generator_wrap` are bare names.** They may produce near-copies of the parent. `check_hits.py 0.80` style similarity of the mutants to their parents is cheap to compute after generation.
* **Escape test of `TY-4900`** (section 4): `C_generic_rec` is the only group built to find a live ty crash. If all 8 programs crash and are closed, the next morning drops it; if one is live, read it before anything else.
* **`runtime_supports` is still untested on a true positive** (Day 8: 1 of 20, NOT-A-BUG). `dunder_instance_shadow` is the operator most likely to produce `only_pyright` rows with a handled `TypeError`; read each `runtime_supports` row of `campaign/day9-only-pyright-relations.txt` before trusting the 0.7 priority.
* **Memory.** The TY-4900 parent crashes by stack overflow, not by memory; no memory-heavy group is planned. `--jobs 14` as in `judge.sh`; check `journalctl` for oomd afterwards and fall back to `--jobs 8` if a kill appears.
* **Class F / draft 8, drafts 6 and 7** remain unfiled; D8-1 and D8-6 style rediscoveries will keep appearing in `d7p_*` mutants (not mutated today) and in `C_pyright_range` (6 programs).
* **Untouched, not mine:** `campaign/day7-report.md` and `campaign/day8/phase6/results/commit.out` carry uncommitted edits; untracked `-l`, `.kiro/` and `findings/2026-10-27-llm-run/` are left alone. Nothing was pushed.
