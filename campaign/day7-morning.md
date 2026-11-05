# Day 7 morning decisions (Plan §3 "Every morning") and generation plan

Branch `campaign/day7-p2`, local only; nothing pushed, no issue or PR touched. Pins: mypy 2.4.0, ty 0.0.97, pyright 1.1.414, CPython 3.13.16.
Inputs: `campaign/day6-morning.md` (the Day-6 groups), `campaign/day6-report.md`, `campaign/day7-run-log.md` (Part A: the four closed duplicate shapes), `runs/day6/out` (the 250 Day-6 reports).
Generation was **not** run in this step. The next step runs `campaign/day7/mk_groups.sh`, `campaign/day7/gen_pass.sh`, then `campaign/day7/judge.sh`.

## 1. Changes to `runs/hits` (49 files before, 45 now)

`runs/` is git-ignored; moves are reversible with `mv` and are recorded by `campaign/day7/retire_parents.sh`.

| Parent | Action | Why |
|---|---|---|
| `d6p_typevartuple_unpack_pep695_paramspec_default_mypy_subscript`, `d3p_typevartuple_unpack_paramspec_default_after_tvt` | stay in `runs/hits`, **no generation** (group `C_callback` dropped) | Callback shape is covered by mypy draft 5 and python/typing#2211. More variants add nothing |
| `d4p_tuples_fold_subclass_eq`, `d4v_ty_tuple_subclass_dunder_fold` | already in `runs/hits-dropped` (Day 6) | ty#2171 tuple fold |
| `d3p_tuples_unpacking_constant_fold_subclass` | **retired today** (moved to `runs/hits-dropped`) | the same ty#2171 shape; since Part A every finding of it is dismissed (`TY-2171`, `TY-2171-ASSERT`) |
| `d4p_narrowing_stale_alias_loop`, `d3p_narrowing_user_attr_narrowing_kept_after_method_call`, `d3p_narrowing_builtin_stale_alias_condition` | **retired today** | Part A log item 12: with the `TY-2792` entries these parents give only dismissed findings, the same case as the two retired tuple parents. This goes one step beyond "retired tuple parents"; undo with `mv runs/hits-dropped/<name>.py runs/hits/` |
| `d4v_protocols_expanding_self_receiver`, `d6p_protocols_expanding_self_receiver_{pep695,dict_arg,tuple_nesting}_ty` | stay, **never mutated** | the 20-strong expanding-receiver family (draft 1). The Day-6 replay has 20 live ty stack-overflow crash findings (one triage pattern, `ty:signal-SIGABRT:stack-overflow`) |
| `d3p_crash_ty_stack_overflow_protocol_flatten`, `d6p_async_generators_protocol_flatten_overflow_ty` | stay, **not mutated** | the first gives rc 1 with plain diagnostics on ty 0.0.97 (`campaign/day7/partB/crash-parents-probe.tsv`); the second still crashes (rc 134) but its receiver is `self: 'Stream[Stream[T_co]]'`, the draft-1 expanding-receiver shape, so it belongs to the family that gets 0 programs |
| mypy crash group `M_mypy_crash` (4 parents), `R_rest` (the other parents) | stay, **not mutated today** | the task is ty crash families plus no-hit areas. Both groups return when a day has spare budget |

`.venv/bin/python campaign/day4m/check_hits.py 0.80` after the moves: **45 files; 0 with problems; no near-duplicate pair** (`campaign/day7/partB/check_hits.out`).

## 2. Areas with no parent in `runs/hits`

`campaign/day7/partB/areas_without_hits.py` (table in `areas-without-hits.txt`) counts parents per `typediff` feature area (the `AREAS` keys in `typediff/strategy.py`, area read like `generate --from-seeds` does).

| Area | Parents | Hand seeds | Day-7 plan |
|---|---|---|---|
| `typeddict` | 0 | 1 | fresh 10 + seed mutants 6 |
| `overloads` | 0 | 1 | fresh 10 + 6 |
| `match_statement` | 0 | 1 | fresh 10 + 6 |
| `dataclasses` (includes `dataclass_transform`) | 0 | 3 | fresh 10 + 18 |
| `final_classvar` | 0 | 1 | fresh 10 + 6 |
| `abstract_classes` | 0 | 0 | fresh 10 |
| `tuples_unpacking` | 0 (after today's retirement) | 2 | fresh 10 + 12 |

Areas from the task list that are **not** zero-parent, and so are not in this table: generics variance (3 parents), enum/Literal narrowing (`enums_literals`, 7), TypeGuard/TypeIs (`narrowing_user`, 3), async/generators (2), ParamSpec/Concatenate (2). `__slots__` and `NewType` are not `AREAS` keys, so `generate --area` cannot target them; they only come up inside `final_classvar`/`inheritance_mro` briefs, if at all.

## 3. Budget (250 programs)

| Share | Programs | Pass 1 | Pass 2 reserve |
|---|---|---|---|
| (c) ty crash families | 40 | 40 | 0 |
| (d) pyright-leaning | 60 | 60 | 0 |
| (b) no-hit areas | 150 | 124 | 26 |
| **Total** | **250** | **224** | **26** |

Pass-1 prompt count checked with a dry run of `gen_pass.sh` against a scratch inbox (224 prompts, no LLM answers): `pending=224`. Evidence: `campaign/day7/partB/gen-pass-dryrun.sh` -> `gen-pass-dryrun.out` (re-run after the review fix: group sizes `A_ty_4148 3, A_ty_paramspec 2, A_ty_protocol_capped 1, N_seeds 9, P_pyright 5`; `pending=224`; 224 prompt files).

### 3.1 (c) ~40 programs on crash families that still crash ty 0.0.97

Probe: `campaign/day7/partB/probe_ty_crash_parents.sh` -> `crash-parents-probe.tsv` (ty 0.0.97, memguard shim): each parent below gives rc 134 (stack overflow) or rc 101 (panic).

| Group | Parents | Ops: n per parent | Programs |
|---|---|---|---|
| `A_ty_4148` | `d3p_callables_self_call_attr`, `d4v_callables_mutual_call_attr`, `d3p_self_classmethods_self_call_union` (TY-4148) | recursion_deepening 2, feature_crossover 2, invalid_type_form 1 | 3 x 5 = 15 |
| `A_ty_paramspec` | `d3p_paramspec_identity_applied_to_itself` (TY-4898), `d3p_paramspec_self_annotated_dunder_call` (TY-4899, panic, not an OOM reproducer) | recursion_deepening 3, feature_crossover 2, invalid_type_form 2 | 2 x 7 = 14 |
| `A_ty_protocol_capped` | `d3p_protocols_generic_protocol_stack_overflow` (the two-protocol `P1[T2] \| P2[T2]` shape, TY-4882; receiver is plain `self`) | feature_crossover 2, recursion_deepening 1 | 1 x 3 = **3** |
| fresh | `recursive_aliases` (crash hunting, Plan P4) | n = 8 | 8 |

The protocol-overflow variants are **capped at 3** (Day 6 gave the four protocol parents 28 programs). The draft-1 expanding-receiver family gets **0**. The family is defined by its shape (a protocol method whose `self` is annotated `Stream[Stream[T]]` or similar, as in `day6-report.md`), not by the four named parents, so `d6p_async_generators_protocol_flatten_overflow_ty` (receiver `self: 'Stream[Stream[T_co]]'`, "same root cause" in `day6-morning.md`) is **excluded** too. It was in the first version of this plan with 3 programs (review finding); those 3 went to fresh `recursive_aliases` (5 to 8), so the crash share stays 40: 15 + 14 + 3 + 8. Pass-1 total is unchanged (224).

### 3.2 (d) ~60 programs, pyright-leaning

Chosen from the pyright-only clusters of the Day-6 replay (section 5): decorated-descriptor dunders called explicitly (9), `Hashable` overlap / unhashable (10), ParamSpec on `self`-annotated `__call__`/`__init__` (7), descriptor attribute assignment (4).

| Source | Ops / n | Programs |
|---|---|---|
| `P_pyright` (5 parents: `d5p_descriptors_decorated_get_pyright_rangeerror`, `d5p_descriptors_one_decorator_dunders_pyright_rangeerror`, `d3p_descriptors_decorated_get`, `d4p_descriptors_readonly_prop_never`, `d3p_generics_callable_attr_contravariant`) | decorator_wrapping 2, descriptor_property 2, generic_nesting 2 per parent | 5 x 6 = 30 |
| fresh `descriptors_properties` | n = 10 | 10 |
| fresh `paramspec_concatenate` | n = 10 | 10 |
| fresh `inheritance_mro` (the `Hashable` / `__eq__` / `__hash__` cluster) | n = 10 | 10 |

The judge step must run with `--pyright-only` (section 5), otherwise these programs surface a pyright-only bug only as a crash. `judge.sh` applies the flag to all 224 programs (kbloop_run takes one switch per run; the flag is cheap and a pyright-only error can appear in any program). To keep Day 7 comparable with Days 1 to 6, `scripts/kbloop_stats.py` now prints an extra line `live without only_pyright: N (programs with such live=M)` whenever a run contains `only_pyright` findings; use that number when comparing days. Check on the Day-6 replay: with the flag, live 231 and programs 123; the new line gives 194 and 110, equal to the run without the flag (`stats-day6replay-pyright.txt`). Output for runs without `only_pyright` is byte-identical to before (`stats-day6replay-off.txt`).

### 3.3 (b) ~150 programs in no-hit areas

| Source | Ops / n | Programs |
|---|---|---|
| fresh, 7 areas of section 2 | `generate --area A --n 10` | 70 |
| hand seeds of those areas (9 files copied to group `N_seeds`) | feature_crossover 2, generic_nesting 1, narrowing_construct_swap 1, runtime_witness 1, invalid_type_form 1 per seed | 9 x 6 = 54 |
| **pass 2 reserve** (not generated by `gen_pass.sh`) | mutants of the pass-1 programs of these areas that show a live finding (promote with `check_hits.py`, copy to a new group, 2 ops x 2 per parent) | 26 |

Reason for the reserve: for a no-hit area the useful parents appear only after pass 1. If pass 1 yields no live finding in an area, its share goes to the area with the most live findings.

## 4. How the next step runs it

```
bash campaign/day7/mk_groups.sh                 # rebuild runs/day7/parents/* (A_ty_4148 3, A_ty_paramspec 2, A_ty_protocol_capped 1, P_pyright 5, N_seeds 9)
bash campaign/day7/gen_pass.sh 0                # then 1, 2, ... until pending=0 (answer runs/day7/inbox/*.prompt.md; campaign/day7/answer_pending.sh is the haiku-5.5 stand-in)
bash campaign/day7/judge.sh                     # kbloop_run --jobs 14 --pyright-only, stats, triage
```

`gen_pass.sh` copies the Day-6 script: `--llm file:runs/day7/inbox`, `PYTHONHASHSEED=0`, 3 retries, output `runs/day7/gen`, log line in `campaign/day7/gen-pass.log`, status JSON `.agents/tasks/day7-gen-status.json`. Expected final count: `written=224`.

## 5. Pyright pass: `only_pyright` findings

**Existing handling (grep of `typediff/` and `scripts/`)**: none that surfaces a pyright-only error. What exists is (1) `attach_pyright_evidence` / `experiments._pyright_side`, which use pyright as a weak tie-break on a discrepancy mypy and ty already disagree about, (2) `known_upstream.json` entries with `silent_tool: "ty"` that read `d.pyright` but only match an existing `only_ty` discrepancy, (3) the `RUNTIME_MISS` kind, which stores pyright diagnostics on the statement but is created from the runtime alone, and (4) pyright crashes as `CRASH` findings. A pyright error at a statement where mypy and ty are both silent produced no discrepancy.

**Added** (off by default):

* New kind `DiscrepancyKind.ONLY_PYRIGHT` (`only_pyright`). `find_discrepancies(..., pyright_only=True)` emits one at each statement where pyright has an **error** (warnings and `reveal_type` output do not count) and mypy and ty have no problem, and CPython evidence exists: `runtime_supports` (a type-related exception with the statement on the stack) or `runtime_contradicts` (coverage known, the statement ran without such an exception). Statements that never ran, unknown coverage and non-type exceptions give no discrepancy. A statement that already has a `runtime_miss` is not duplicated (that discrepancy already carries `d.pyright`).
* New discrepancies are appended after all others, so the ids of existing discrepancies do not move.
* Switch: `PipelineConfig.pyright_only` (default `False`), CLI `typediff --pyright-only ...`, `scripts/kbloop_run.py --pyright-only`, `scripts/kbloop_replay.py --pyright-only`. The flag is ignored when pyright did not run.
* Handling: priority 0.7 (supports) / 0.3 (contradicts); the deterministic stage attaches the CPython evidence plus one neutral evidence line naming the pyright rule; no KB entry applies; the finding ends in `review` / `gate` (no LLM) and is never confirmed by itself. The reducer is skipped for this kind (its predicates re-run mypy and ty only). `dataset.signature` uses the pyright codes and messages for this kind, so different rules do not collide. `render_summary` prints the pyright side.
* Tests: `tests/test_pyright_only_day7.py` (18 tests: off by default, contradicts, supports, not-run / unknown coverage / non-type exception, mypy or ty also reporting, warnings and reveals, no duplicate next to `runtime_miss`, ids stable, pipeline default adds nothing, replay of a saved report, signature).

**Day-6 replay** (`runs/day6/out`, 250 reports, `scripts/kbloop_replay.py ... --jobs 14 --verify-sample 30`; output in `campaign/day7/partB/`):

| Replay | Result |
|---|---|
| default (switch off) vs the Part A replay `runs/day7/day6replay` | 321 findings compared, **0 changed**; `verify-sample` 30/30 identical to a full re-run (`off-vs-partA.txt`, `replay-off.out`) |
| `--pyright-only` | the same 321 findings unchanged, **37 added** (`only_pyright`) in 23 programs: 0 `runtime_supports`, 37 `runtime_contradicts`, all `review` / `gate`; `verify-sample` 30/30 (`pyright-added.txt`, `replay-pyright.out`) |

Effect on the Day-6 live count: 194 -> 231, programs with a live finding 110 -> 123 (`stats-day6replay-off.txt`, `stats-day6replay-pyright.txt`). The 37 by pyright rule: reportCallIssue 13, reportGeneralTypeIssues 7, reportAttributeAccessIssue 6, reportArgumentType 5, reportUnhashable 3, reportAssertTypeFailure 2, reportInvalidTypeForm 1, reportAssignmentType 1.

Clusters in the 37 (read from `pyright-added.txt`; none was hand-verified as a pyright bug, they are triage leads): 9 x `Desc.__set__/__delete__(...)` "Object of type int is not callable" (decorated descriptor dunder, same family as the two pyright `RangeError` parents), 10 x `Hashable` overlap / unhashable (the topic of draft 4, `__eq__` without `__hash__`; here pyright rejects what ty and mypy accept), 7 x ParamSpec on `self`-annotated `__call__`/`__init__`, 4 x attribute assignment through a descriptor, 7 other single rows. No row has runtime support, so none of them is a bug claim. Because the switch changes live counts, Day-7 numbers with `--pyright-only` are not comparable with Days 1 to 6; the report lists `only_pyright` separately (`live by kind`).

## 6. Checks run in this step

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest tests -q` | **497 passed** (426 baseline + 53 Part A + 18 new) |
| `.venv/bin/typediff --python-version 3.13 kb-selftest` | **20 PASS, 0 FAIL** |
| `.venv/bin/python campaign/day4m/check_hits.py 0.80` | 45 files; 0 with problems; no near-duplicate pair |
| Day-6 replay, switch off | 0 of 321 findings changed |
| Day-6 replay, `--pyright-only` | +37 findings (23 programs) |

## 7. Risks and open points

* **Review queue size.** `--pyright-only` adds 37 live findings on top of 194 (+19 %) for the 250 Day-6 programs, all weak (`runtime_contradicts`). If the queue grows faster than it can be triaged, drop the flag from `judge.sh`; the code stays off by default.
* **`runtime_contradicts` is weak evidence.** A program that runs fine is not proof that pyright is wrong, and not proof that it is right. The finding is a lead for hand verification against the pyright docs and the typing spec, not a bug claim.
* **No `runtime_supports` yet.** Day 6 has none; the path is covered by unit tests only.
* **Memory.** Group `A_ty_paramspec` and fresh `paramspec_concatenate` can produce TY-4899-style programs that hit the 4 GB shim cap; `judge.sh` uses `--jobs 14` as instructed, check `journalctl` for oomd afterwards and fall back to `--jobs 8` if a kill appears (same note as Day 6).
* **Crash-family yield check after pass 1.** `A_ty_4148` and `A_ty_paramspec` are 29 of the 40 crash programs, and on Day 6 `TY-4148` and `TY-4898` already closed 14 and 7 crash findings from these parents. After pass 1, count live crash findings (and `crash closures by closing reference`) from the programs of these two groups. If fewer than 3 of the 29 are live, move the unspent crash budget (not yet generated, so pass 2) to the no-hit area with the most live findings.
* **`runtime_supports` has no real-data coverage.** The 0.7-priority branch of `only_pyright` is unit-tested only (0 in the Day-6 replay). On the first Day-7 `only_pyright` finding whose runtime evidence is a type exception on the stack, check its evidence text and priority by hand before trusting the branch.
* **Retirement scope needs your confirmation.** The three narrowing parents retired in section 1 go beyond "retired tuple parents". Reverting is `mv runs/hits-dropped/<name>.py runs/hits/` followed by `check_hits.py 0.80`, then `mk_groups.sh` if a group should include them (none does today).
* The untracked `-l` file, `.kiro/` and `findings/2026-10-27-llm-run/` are not touched.
