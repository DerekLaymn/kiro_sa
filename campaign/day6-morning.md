# Day 6 morning decisions (Plan §3 "Every morning") and generation plan

Branch `campaign/day6-p2`, local only; nothing pushed, no issue or PR touched. Pins: mypy 2.4.0, ty 0.0.97, pyright 1.1.414, CPython 3.13.16 (checkers through the memguard shims in `.venv/bin`, untouched).
Inputs: `campaign/day6-verification.md` (Part A verdicts), `campaign/day5-ty97-bump.md` (what still crashes on 0.0.97), `campaign/day5-morning.md`, `runs/day5/out97` (the 250 Day-5 programs re-judged on 0.0.97), `campaign/day5/gen_pass.sh` (how Day 5 generated).
Generation was **not** run in this step. The next step runs `campaign/day6/mk_groups.sh` and then `campaign/day6/gen_pass.sh`.

Correction to the task text: `scripts/check_hits.py` does not exist. The hits checker is `campaign/day4m/check_hits.py` (same one Day 5 used); it was run with threshold 0.80.

## 1. Focus used for the choices

(a) Crash families that still reproduce on ty 0.0.97 (TY-4148 variants, protocol-flatten overflow TY-4882, TY-4898/4899/4900), to look for crashes beyond the known entries.
(b) A pyright pass: descriptors, decorators and ParamSpec parents, so more programs exercise pyright (it already crashes with `RangeError` on two parents).
(c) No generation on TypedDict-TypeVar solving or `partial | None` loops (fixed on 0.0.97).
(d) Callback shape only if Part A calls it a real bug.

## 2. Evidence: what each parent does on the pinned versions

`campaign/day6/morning/probe_hits.sh` runs every file in `runs/hits` through ty, mypy and pyright (sequentially, memguard shims, 90/120 s timeouts); output is `campaign/day6/morning/hits-probe.tsv`, re-run on the final 49 files (the table below was read from the first run over the 51 files before retirement; kept files gave the same results; return codes: 134 = SIGABRT stack overflow, 139 = SIGSEGV, 137 = killed by the shim, 101 = Rust panic, pyright 2 = `RangeError`).
`campaign/day6/morning/list_crash_findings.py runs/day5/out97` lists every crash finding of the Day-5 re-judge with its parent.

Parents that crash a checker today (before this step's changes, 51 files):

| Tool, signature | Parents |
|---|---|
| ty SIGABRT stack overflow (rc 134) | `d3p_callables_self_call_attr`, `d4v_callables_mutual_call_attr`, `d3p_self_classmethods_self_call_union` (TY-4148); `d3p_protocols_generic_protocol_stack_overflow` (TY-4882, 2 of its Day-5 mutants closed by that entry), `d4v_protocols_expanding_self_receiver` (its 4 Day-5 mutants are 4 of the 8 live crash findings); `d3p_paramspec_identity_applied_to_itself` (TY-4898) |
| ty Rust panic (rc 101) | `d3p_paramspec_self_annotated_dunder_call` (TY-4899 family, the salsa cycle case E8) |
| mypy SIGSEGV / killed (rc 139, 137) | `d3p_callables_self_call_attr`, `d3p_self_classmethods_self_call_union`, `d4v_callables_mutual_call_attr` (MYPY-22361); `d3p_generics_contravariant_recursive_base` (MYPY-22360); `d3p_generics_typevar_default_refers_to_itself` (MYPY-22344); `d3p_crash_mypy_segv_recursive_tvt_default_alias`; `d3p_recursive_aliases_type_of_self_alias`; `d3p_descriptors_decorated_get` |
| pyright `RangeError` (rc 2) | `d5p_descriptors_decorated_get_pyright_rangeerror`, `d5p_descriptors_one_decorator_dunders_pyright_rangeerror` |
| none, though the name says crash | `d3p_crash_ty_stack_overflow_protocol_flatten` (ty rc 1, plain diagnostics on 0.0.97; its Day-5 mutants do overflow), `d3p_crash_ty_panic_partial_or_none_in_loop`, `d4p_callables_crash_ty_panic_partial_loop`, `d4v_callables_staticmethod_loop_union`, `d3p_crash_ty_timeout_typeis_generic_in_loop`, `d3p_typeddict_generic_typevar_unsolved` |

The Day-5 crash findings on 0.0.97 (`list_crash_findings.py`): 34 crash findings in 27 programs. 10 are live: 8 ty protocol-flatten overflows (4 from `d3p_crash_ty_stack_overflow_protocol_flatten` mutants, 4 from `d4v_protocols_expanding_self_receiver` mutants) and 2 pyright `RangeError`. The other 24 are closed by TY-4148, TY-4882, TY-4898 and MYPY-22360/22361/22344. No crash signature outside the known entries appeared.

## 3. Changes to `runs/hits` (49 files now, was 51)

### 3.1 Retired (moved to `runs/hits-dropped/`, reversible with `mv`)

Focus (c): the crash or wrong result is gone on ty 0.0.97, so mutants of these parents only reproduce a fixed bug.

| Parent | Why |
|---|---|
| `d3p_crash_ty_panic_partial_or_none_in_loop`, `d4p_callables_crash_ty_panic_partial_loop`, `d4v_callables_staticmethod_loop_union` | `partial | None` / `staticmethod | None` loop: ty rc 1 with ordinary diagnostics on 0.0.97 (Day-5 bump note: all 8 panics gone) |
| `d3p_typeddict_generic_typevar_unsolved` | TY-4884 fixed in 0.0.97 |
| `d3p_crash_ty_timeout_typeis_generic_in_loop` | the 120 s ty timeout is gone: ty returns rc 1 well inside the 90 s probe limit |

Not retired: `d3p_callables_partial_too_many_positional` (a `partial` call-arity check, not the loop).

### 3.2 Promoted (3 files, force-added to git because `runs/` is ignored, as the `d5p_*` hits were)

| New parent | Source | Evidence | Why |
|---|---|---|---|
| `d6p_async_generators_protocol_flatten_overflow_ty.py` | Day-5 mutant `runs/day5/gen/async_generators/d3p_crash_ty_stack_overflow_protocol_flatten__mut0_03b3d0f5.py` | ty 0.0.97 SIGABRT (rc -6), live finding; 0.61 similar to its parent, 0.56 to 0.60 to the `d4v_protocols_expanding_self_receiver` mutants | The original `d3p_crash_ty_stack_overflow_protocol_flatten` no longer crashes ty. This mutant keeps the `Stream[Stream[T_co]]` receiver shape, legacy TypeVar and an async generator, so mutants start from a crashing program |
| `d6p_protocols_expanding_self_receiver_pep695_ty.py` | Day-5 mutant `runs/day5/gen/protocols/d4v_protocols_expanding_self_receiver__mut0_9792459e.py` | ty 0.0.97 SIGABRT (rc -6), live finding; 0.73 similar to its parent (< 0.80) | Same root cause, PEP 695 `Stream[T]` plus `runtime_checkable` and `isinstance`; the most distinct of its 4 mutants (the other three are 0.75, 0.80 and 0.81 similar to the parent) |
| `d6p_typevartuple_unpack_pep695_paramspec_default_mypy_subscript.py` | `campaign/day6/repro/m1_mypy_use_site.py`, wrapped in `try/except TypeError` so CPython runs it | mypy 2.4.0: 6 errors (`Can only replace ParamSpec ...` at both subscripts, 4 `assert-type`); ty: `All checks passed!`; pyright: 0 errors; CPython: prints the caught `TypeError: Type parameter with a default follows TypeVarTuple` | **Callback shape, promoted.** See 3.3 |

Not promoted: the other six Day-5 protocol mutants (the three other flatten mutants are 0.85 to 0.94 similar to the promoted one, the other expanding mutants 0.78 to 0.98 similar to each other or 0.75 to 0.81 to their parent; same root cause, no new shape); the TY-4899 OOM reproducers (`E1`, `E2`, `E6`, `E10`, killed at the 4 GB shim cap). Mutating them would multiply 4 GB ty processes under `--jobs 14`, which is the memory pattern that closed Kiro earlier. The existing `d3p_paramspec_self_annotated_dunder_call` already covers the family (panic, no OOM).

### 3.3 Callback shape: promoted

`campaign/day6-verification.md` §1 and §5.7: the `class Callback[*Ts, **P = [bool]]` declaration is valid per the typing spec and PEP 696 (ty NOT-A-BUG; CPython rejects a valid class, duplicate of python/typing#2211), and **mypy rejects the valid subscript `Callback[int, str]`, STILL-BUG-NEW (draft 5)**. So the condition in the task is met: the shape is a real bug, in mypy. The new parent is the PEP 695 form with a defaulted ParamSpec after `*Ts` plus use sites. The old legacy-spelling hit `d3p_typevartuple_unpack_paramspec_default_after_tvt` stays and shares the group `C_callback`.
The hypothesis line of the new parent also lists the variants to try: defaulted `TypeVar` after `*Ts` (all three checkers must reject it, a control), `Concatenate`, nested `Foo[Foo[int], str]`, legacy `Generic[Unpack[Ts], P]`, a `TypeVarTuple` default.

### 3.4 Checks

`.venv/bin/python campaign/day4m/check_hits.py 0.80` after the changes: **49 files; 0 with problems; near-duplicate pairs (difflib ratio >= 0.80): none**. The only parents with preflight warnings or a CPython failure are the same ones as on Day 5 (hits are bug carriers, not necessarily runnable programs); the new `d6p_*` files have `preflight=[]` and run (the Callback one prints its caught `TypeError`).

## 4. Parent groups for generation

`typediff generate --from-seeds DIR` applies the same `--ops` and `--n` to every file in `DIR`, so counts per parent are set by group. `campaign/day6/mk_groups.sh` copies `runs/hits` into `runs/day6/parents/<group>/` (git-ignored; the script rebuilds it). Group sizes: 9 + 4 + 5 + 2 + 29 = 49.

| Group | Parents | Why |
|---|---|---|
| `A_ty_crash` (9) | `d3p_callables_self_call_attr`, `d4v_callables_mutual_call_attr`, `d3p_self_classmethods_self_call_union` (TY-4148); `d3p_protocols_generic_protocol_stack_overflow`, `d4v_protocols_expanding_self_receiver`, `d6p_async_generators_protocol_flatten_overflow_ty`, `d6p_protocols_expanding_self_receiver_pep695_ty` (TY-4882 / flatten / expanding base); `d3p_paramspec_identity_applied_to_itself` (TY-4898), `d3p_paramspec_self_annotated_dunder_call` (TY-4899) | Focus (a): each still crashes ty 0.0.97 |
| `M_mypy_crash` (4) | `d3p_generics_contravariant_recursive_base`, `d3p_generics_typevar_default_refers_to_itself`, `d3p_crash_mypy_segv_recursive_tvt_default_alias`, `d3p_recursive_aliases_type_of_self_alias` | mypy SIGSEGV families (MYPY-22360, 22344, recursive TVT alias); lower weight than A, since the plan targets new distinct crashes and these entries already exist |
| `P_pyright` (5) | `d5p_descriptors_decorated_get_pyright_rangeerror`, `d5p_descriptors_one_decorator_dunders_pyright_rangeerror`, `d3p_descriptors_decorated_get`, `d4p_descriptors_readonly_prop_never`, `d3p_generics_callable_attr_contravariant` | Focus (b): descriptors with decorated dunders (pyright `RangeError`) and callable-attribute parents. ParamSpec for pyright comes from the fresh `paramspec_concatenate` area and from the ParamSpec parents in A |
| `C_callback` (2) | `d6p_typevartuple_unpack_pep695_paramspec_default_mypy_subscript`, `d3p_typevartuple_unpack_paramspec_default_after_tvt` | Focus (d) |
| `R_rest` (29) | everything else in `runs/hits` (enum alias/Flag, metaclass operators, `__eq__`/`__hash__`, stale alias narrowing, tuple subclass folding, `d3p_crash_ty_stack_overflow_protocol_flatten` and others) | Kept at 2 mutants each, as Day-5 coverage of existing hits |

## 5. Ops and counts (200 mutated)

Operators are the names in the strategist prompt (`typediff/prompts.py`); `CRASH_OPS` in `typediff/strategy.py` is `recursion_deepening, invalid_type_form, feature_crossover`. An op is a prompt instruction to the generator, not a fixed code transform.

| Group | Parents | Op: n per parent | Per parent | Programs |
|---|---|---|---|---|
| A_ty_crash | 9 | recursion_deepening: 3, feature_crossover: 3, invalid_type_form: 1 | 7 | 63 |
| M_mypy_crash | 4 | recursion_deepening: 2, feature_crossover: 1, invalid_type_form: 1 | 4 | 16 |
| P_pyright | 5 | decorator_wrapping: 3, descriptor_property: 3, generic_nesting: 3 | 9 | 45 |
| C_callback | 2 | feature_crossover: 4, generic_nesting: 3, invalid_type_form: 2 | 9 | 18 |
| R_rest | 29 | narrowing_construct_swap: 1, runtime_witness: 1 | 2 | 58 |
| **Total** | **49** | | | **200** |

Per-operator totals: recursion_deepening 35, feature_crossover 39 (A 27, M 4, C 8), invalid_type_form 17 (A 9, M 4, C 4), generic_nesting 21 (P 15, C 6), decorator_wrapping 15, descriptor_property 15, narrowing_construct_swap 29, runtime_witness 29. Sum 200.

Crash-family groups (A, M, C) are 97 programs and the pyright pass 45; together 142 of 200 (71 %). Day 5 spread 4 mutants evenly over 50 parents with `narrowing_construct_swap`, `runtime_witness` and 2 x `feature_crossover`; Day 6 drops `feature_crossover` for R_rest and moves its share to A, M, C.
With `--n k` the generator adds a `Variant i of k` line to each prompt (Day-5 step 1b), so repeated draws for one parent and op differ.

## 6. Fresh programs (50)

`typediff generate --area AREA --n N` (the brief is the `AREAS` text in `typediff/strategy.py`).

| Area | n | Reason |
|---|---|---|
| descriptors_properties | 12 | pyright pass: descriptors and decorated dunders |
| paramspec_concatenate | 12 | pyright pass: ParamSpec, decorators; also TY-4898/4899 neighbourhood |
| callables | 8 | TY-4148 `__call__` neighbourhood (callback protocols) |
| protocols | 8 | protocol-flatten family |
| recursive_aliases | 6 | crash hunting: self-referential generics and aliases (Plan P4) |
| typevartuple_unpack | 4 | Callback shape, fresh programs |
| **Total** | | **50** |

Day-5 fresh areas overloads, dataclasses and enums_literals are skipped this time (protocols and typevartuple_unpack return with the crash and Callback focus). Excluded on purpose: `typeddict` and `narrowing_*` (TypedDict-TypeVar and `partial | None` loops are fixed). The `callables` brief could still drift into `partial | None`; if a program does, ty 0.0.97 gives plain diagnostics and the judge dismisses it as noise.

## 7. How the next step runs it

```
bash campaign/day6/mk_groups.sh                 # rebuild runs/day6/parents/* from runs/hits
bash campaign/day6/gen_pass.sh 0                # then 1, 2, ... until pending=0 (file bridge: answer runs/day6/inbox/*.prompt.md)
```

`gen_pass.sh` is a copy of the Day-5 script with the Day-6 groups, ops and areas, `--llm file:runs/day6/inbox`, `PYTHONHASHSEED=0`, 3 retries per command, output in `runs/day6/gen`, and a `- gen pass N: pending=.. written=..` line appended to `campaign/day6/gen-pass.log`. Expected final count: `written=250`.
Judge with `TYPEDIFF_LLM=null .venv/bin/python scripts/kbloop_run.py runs/day6/out runs/day6/gen --jobs 14` (the Day-5 form; `--jobs 14` as instructed).

## 8. Risks and open points

* **Memory.** Group A and the fresh `paramspec_concatenate` area are likely to produce TY-4899-style `Callable[P, T]` programs that run into the 4 GB shim cap (exit 137). With `--jobs 14` the worst case is many such processes at once; Day 5 ran the same width with 0 oomd kills, but the share of crash-prone programs is higher now. Check `journalctl` for oomd after the judge run and drop to `--jobs 8` if a kill appears.
* **Generator drift.** Day-5 mutants drifted away from their parent (an enum parent produced a ParamSpec program; a flatten parent produced an async-generator program). A mutant can therefore land in another group's family; the area key in the header is the generator's own.
* **Known crashes will dominate group A.** Most A/M mutants will be closed by TY-4148, TY-4882, TY-4898, MYPY-22360/22361 (as on Day 5). New crashes show up as live `CRASH` findings with no `closed_by`.
* **Callback group.** mypy findings there reproduce draft 5, so they will stay live (no `known_upstream` entry exists on purpose; Part A left that to the triage owner).
* The run log line in `campaign/day6-run-log.md` is Part A's; Part B generation logs go to `campaign/day6/gen-pass.log`.
* The untracked stray file `-l` in the repo root (garbled shell command) and `.kiro/`, `findings/2026-10-27-llm-run/` are not touched, as on Day 5.
