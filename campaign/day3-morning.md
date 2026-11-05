# Day 3 morning (Plan §3 "Every morning")

Branch `campaign/day3-p2`. Iteration 1 (no `day3-morning-review.json` existed). No LLM was used in this step.
Raw outputs and the scripts that produced them are in `campaign/day3m/`.

## 1. Replay of Day-2 results under the final knowledge base

`scripts/kbloop_replay.py runs/day2/out3 runs/day3/replay --jobs 14 --verify-sample 50`: 5086 reports re-judged (about 16 min).
`--verify-sample 50`: 50/50 identical to a full re-run (0 mismatches). `runs/day2/out3` has 5086 reports (the earlier "runs/day2 is empty" claim was wrong).

| | Day-1 baseline | Day-2 final (`out3`) | Day-3 replay | change since Day 2 |
|---|---|---|---|---|
| programs | 5086 | 5086 | 5086 | 0 |
| discrepancies | 10615 | 10597 | 10597 | 0 |
| **live review queue** | 7841 | **7277** | **7273** | **-4** |
| programs with a live finding | 2642 | 2566 | 2562 | -4 |
| live crash findings | 10 | 10 | 6 | -4 |
| dismissed | 2784 | 3330 | 3334 | +4 |
| dismissed as DUPLICATE | 13 | 13 | 17 | +4 |

Exactly 4 findings changed, all crash findings: live -> dismissed DUPLICATE through the 11 crash entries recorded this morning
(`rule:crash:signal` 2, `rule:crash:timeout` 2; TY-4882 1, TY-4883 2, MYPY-22344 1, as already hand-checked in `day3-upstream-entries.md`).
No discrepancy (non-crash) finding changed tier. `tool_crashes` stays 10 (the crashes are still detected, 4 are now dismissed).
Live by kind after the replay: only_mypy 2551, reveal_mismatch 2103, only_ty 1764, concern_mismatch 750, runtime_miss 69, reveal_unpaired 30, crash 6.
Live findings with strong bug evidence: 625 (reveal_mismatch 200, only_ty 165, concern_mismatch 106, only_mypy 87, runtime_miss 61, crash 6).

Honest reading: the queue is 7.2 % smaller than on Day 1 (7841 -> 7273), far from the Phase-1 target of more than 50 %. What is left is not
a few big noisy patterns but mdtest/mypy-suite reveal differences and fragments that reference undefined names (section 3).
Day 3's job is mutation, not queue shrinking, so no further KB work was forced.

Files: `campaign/day3m/stats-day2-out3.txt` (before), `stats-day3-replay.txt` (after), `triage-top30-details.txt`, `triage-top60.txt`.

## 2. Parents promoted into `runs/hits/` (32 files; 30 new + the 2 existing `s3r1_*` kept)

Every file starts with the 3 header lines `# area:` (a real `typediff.strategy.AREAS` key), `# hypothesis:` (the generator's brief) and `# origin:`.
Checked by `campaign/day3m/check_hits.py` (header, AREAS key, compile, `typediff.generator.preflight` with target 3.13: 0 ERROR; only WARNs such
as "class never used") and by `python -m py_compile` on all 32 (0 failures, `final_hits_check.txt`). Bare `reveal_type` in two verbatim files is
injected by the runtime harness, so CPython runs them under the pipeline.
The no-LLM pipeline (`typediff seeds runs/hits`, `run_hits.log`, `hits_summary2.txt`) was run over all of them to confirm each still shows its signal.
The two existing files only got a `# hypothesis:` line (bodies untouched).

"Result" is what the pipeline reported today. "dup X" means the finding was dismissed DUPLICATE of an existing upstream entry, which is expected for
bugs the team already filed: variants that differ from the filed shape are what the mutation step is looking for.

| File (`d3p_` prefix) | Area | Source | Why | Result |
|---|---|---|---|---|
| callables_self_call_attr | callables | team repro `temp/xfer/var/A1.py` | `__call__: "C"` self-annotated; crash family | ty stack overflow confirmed; mypy SIGSEGV dup MYPY-22361 |
| self_classmethods_self_call_union | self_classmethods | `A5.py`, bound to a real instance | `__call__: Self \| None`; A5 as filed stops at NameError, the bound form runs (CPython TypeError) and still crashes both | ty stack overflow confirmed, mypy SIGSEGV dup |
| descriptors_decorated_get | descriptors_properties | `A7.py` | decorated `__get__` | mypy SIGSEGV confirmed (no entry matches) |
| generics_contravariant_recursive_base | generics_variance | `B1.py` (B4 dropped as the same shape) | `class C(N[N["C"]])` contravariant | mypy SIGSEGV dup MYPY-22360 |
| generics_contravariant_recursive_generic_base | generics_variance | `D7.py` (D10 dropped) | generic variant | mypy SIGSEGV dup MYPY-22360, ty overflow dup TY-4900 |
| paramspec_identity_applied_to_itself | paramspec_concatenate | `C1.py` (C3 dropped) | `id(id)` with ParamSpec | ty stack overflow, dup |
| paramspec_self_annotated_dunder_call | paramspec_concatenate | `E8.py` (E6 dropped) | `self: Callable[P, T]` | ty panic, dup |
| generics_callable_attr_contravariant | generics_variance | `temp/mypy_callable_variance.py` | mypy accepts Handler[float] for Handler[int]; runtime AttributeError | runtime_miss (strong) in review; only_ty dup MYPY-22339 |
| protocols_generic_protocol_stack_overflow | protocols | crash25 `ty_TB_protocol_stack_overflow` | generic protocols referencing each other | ty overflow, dup |
| recursive_aliases_type_of_self_alias | recursive_aliases | crash25 `mypy_A_typealias_segfault` | `type X = Meta[X]` | mypy SIGSEGV, dup |
| generics_typevar_default_refers_to_itself | generics_variance | crash25 `mypy_E_typevar_default_self` | `TypeVar("T", default="T")` | mypy SIGSEGV dup MYPY-22344 |
| narrowing_user_index_assign_stale | narrowing_user | fuzz branch bug-01 | stale index narrowing in mypy, runtime TypeError | dup MYPY-20969 |
| enums_flag_or_literal_union | enums_literals | fuzz branch bug-02 | `F.R \| F.W` as literal union in ty | dup TY-876 |
| enums_flag_is_narrowing_else | enums_literals | fuzz branch bug-06 | mypy treats the Flag else branch as unreachable | dup MYPY-21937 |
| typeddict_generic_typevar_unsolved | typeddict | fuzz branch bug-05 | ty cannot solve T from a generic TypedDict | dup TY-4884 |
| narrowing_builtin_stale_alias_condition | narrowing_builtin | `calibration/must_stay_live/mypy_stale_alias.py` | aliased condition reused after mutation | 1 reveal_mismatch in review |
| tuples_unpacking_constant_fold_subclass | tuples_unpacking | `calibration/must_stay_live/ty_constant_fold_tuple_subclass.py` | ty folds `<` on a tuple subclass with `__lt__` | 1 only_ty in review |
| crash_ty_stack_overflow_protocol_flatten | async_generators | replay `seed-50a85e2bdd8d` (ruff mdtest with/async 43) | live ty crash | ty overflow, dup of A1's identical signature in the same run |
| crash_mypy_segv_recursive_tvt_default_alias | recursive_aliases | replay `seed-918936c5da72` (pep695 aliases 17) | live mypy crash | crash confirmed (SIGKILL: 4 GB guard) |
| crash_ty_panic_partial_or_none_in_loop | callables | replay `seed-dc88d8cc6015` (union 11) | live ty salsa panic | panic confirmed |
| crash_ty_timeout_typeis_generic_in_loop | narrowing_user | replay `seed-23cf4835dc66` (type_guards 49) | live ty timeout (120 s) | timeout confirmed |
| callables_partial_too_many_positional | callables | replay `seed-67774769f97e` | `partial(f, 1, 2, 3)`; CPython raises on call, mypy silent, ty flags only the `partial` line | runtime_miss (strong) |
| inheritance_mro_hash_none_from_eq | inheritance_mro | replay `seed-67975a0c41c4` (trimmed) | `__eq__` without `__hash__`; calling `__hash__` raises, only pyright reports | runtime_miss (strong) |
| typevartuple_unpack_paramspec_default_after_tvt | typevartuple_unpack | replay `seed-570818101ed2` | `Generic[*Ts, P]` with defaulted P raises TypeError in 3.13; checkers accept and disagree | 8 findings in review (runtime_miss strong) |
| constructors_metaclasses_type_call_generic_base | constructors_metaclasses | replay `seed-badf7d3532a5` | `type(name, (Container[int],), {})` raises at runtime | 6 findings in review (runtime_miss strong) |
| constructors_metaclasses_missing_kwonly_class_args | constructors_metaclasses | replay `seed-1cadfac7cbe5` (trimmed to the construct) | metaclass `__new__` with required keyword-only args, class omits them | runtime_miss (strong) |
| enums_literals_intenum_true_aliases_one | enums_literals | replay `seed-0aa2461b8e0e` (trimmed + runtime witness) | `TRUE = True` is an alias of `ONE`; mypy and pyright keep it separate | 2 reveal_mismatch (strong) |
| inheritance_mro_total_ordering_inherited_lt | inheritance_mro | replay `seed-bcd8afd96f79` (trimmed + prints) | mypy reveals the opposite literals for `<` and `>` | 3 reveal_mismatch (2 strong) |
| constructors_metaclasses_reflected_operator_on_metaclass | constructors_metaclasses | replay `seed-d68de70a95aa` (+ print) | CPython returns `'right'` (reflected method first), mypy and pyright say `'left'` | 1 reveal_mismatch (strong) |
| narrowing_user_attr_narrowing_kept_after_method_call | narrowing_user | replay `seed-a9f445b3a193` (trimmed + prints) | ty keeps `Literal["a"]` after `a.update_x("b")`; runtime `'b'` (ty's own mdtest marks it TODO) | 1 reveal_mismatch (strong) |
| s3r1_mypy_class_base_forward_ref | gradual_any | existing | | 2 in review |
| s3r1_ty_type_equality_narrowing_any | narrowing_user | existing | | 11 in review |

Confirmed-tier crash parents (not matched by any upstream entry): A1 (ty), A5 (ty), A7 (mypy), the mypy tvt-alias segfault, the ty panic and the ty timeout.
Parents whose signal is currently "dup" are kept on purpose: they are filed bugs, and plan §2 asks for 5-20 variants of known hits.

Dropped after the confirmation run: `ty_TA_nested_tuple_compare` (20 aliases). On ty 0.0.84 it neither crashes nor times out at depth 20
(ty#4883 only closes at depth 24, 148 s), so it carried no signal.
Not promoted: the other crash25 repros and xfer cases that are the same shape as the ones above (B4, D10, C3, E6) and everything in the
"Rejected ideas" list.

## 3. Pattern verdicts (Plan §6 applied to the biggest live patterns of the replay)

Sampling: `campaign/day3m/sample_patterns.py` (5 seeded random non-strong examples per pattern, origin mix, KB hints).

| Pattern (live, strong) | Source mix | Verdict | Recommendation |
|---|---|---|---|
| reveal_mismatch gradual: 589 (90) | ty-mdtest 445, mypy-suite 134 | two things mixed: mypy `Any` vs ty `Unknown`/precise type (BOTH-GRADUAL already closed 458 others), and ty `Unknown` caused by names the fragment never defines (the 90 strong are CPython NameError) | extend the undefined-name cascade rule to reveal lines in the next KB round |
| reveal_mismatch uncomparable: 538 (13) | ty-mdtest 422, mypy-suite 108 | display/semantics differences (`X & ~AlwaysFalsy` vs `TypedDict(...)`, `<class 'list[int]'>` vs `Overload(...)`, `(...) -> T` vs `def (*Any, **Any)`) | needs normalizer work in `typenorm`, not an entry |
| reveal_mismatch different: 480 (82) | ty-mdtest 430 | mostly literal/tuple precision and enum values; the strong ones are real (IntEnum alias, Flag, metaclass operator: now parents) | none |
| reveal_mismatch ty_more_precise: 414 (8) | ty-mdtest 401 | ty narrows more (`int` vs `int \| None`, `Literal["b", 2]`); the mdtest's own `# revealed:` comment matches ty (hint ORIGIN-ORACLE-NOTE on 385) | widen PRECISION-RUNTIME-CONSISTENT only with a runtime probe per case; not done |
| only_mypy assert-type: 306 (7) | pyright samples 271 | mypy reports "Any, not X" where ty accepts: either mypy imprecision (typeshed `Any`) or ty accepting an assert_type it should reject (see TY-4884-ASSERT, TY-876-ASSERT) | split by whether mypy's type is `Any` before deciding |
| only_mypy arg-type: 220 (8) | pyright 130, ty-mdtest 53, mypy-suite 32 | protocol/callable assignability that mypy rejects and ty accepts; no common cause | none |
| only_ty unresolved-reference: 163 (62) | mypy-suite | fragments use a name before its definition; CPython NameError confirms ty, mypy is lenient in annotations/class bases | mypy gap, but the evidence is a harness artifact; leave live |
| concern_mismatch assignment: 127 (7) | mypy-suite 77 | ty reports "name used when not defined" where mypy reports the type error (hint GRADUAL-OPERAND on 69) | same undefined-name cascade |
| only_ty unsupported-bool-conversion: 15 (10) | ty-mdtest | ty is right (CPython TypeError at the conversion); mypy does not check `__bool__` | mypy-miss candidate, leave live |
| concern_mismatch str-unpack: 7 (7) | ty-mdtest | both reject, different message and rule (mypy lint vs ty arity); CPython ValueError confirms | design difference, see "Rejected ideas" |
| concern_mismatch disjoint bases: 29 (10) | ty-mdtest, pyright | both reject, different wording; CPython TypeError confirms | design difference, see "Rejected ideas" |
| runtime_miss: 69 (61) | all | 18 strong findings across the queue are "X is not subscriptable" at runtime (typeshed-only generic classes such as `zip[...]`, `memoryview[...]`), many others are mdtest fragments that fail deliberately on an earlier line, 7 are NameError; the real gaps became parents (partial, `__hash__`, kw-only metaclass args, TypeVarTuple default, `type()` with a generic base) | none |
| crash: 6 live | pyright samples 2, ty mdtests 4 | ty: timeout x2 (`pyright__matchSequence2`, `type_guards_49`), stack overflow, salsa panic; mypy: SIGSEGV x2 (`aliases_17`, `pyright__typeVarDefaultTypeAlias2`); none matches a crash entry's `requires` shape. Four are parents; `matchSequence2` (189 lines) and `typeVarDefaultTypeAlias2` (141 lines) are too large to be useful briefs | reduce and file in P5 |

## 4. Retired patterns: none added this morning

New KB / upstream entries added: **0**. Reasons, per the step's rules (at most 3, only on a clear verdict, never hide a finding with CPython evidence):
- The only patterns with a clear verdict (str-unpack, disjoint bases: both tools reject the same statement) consist entirely of findings that
  carry strong CPython-exception evidence. Dismissing them would hide findings with runtime evidence, which the step forbids.
- The large patterns without runtime evidence are mixtures (table above). A narrow, correct matcher for them needs the normalizer or probe work
  listed under "Recommendation", which is a separate change with its own calibration run.
- No upstream issue candidate came out of the sampling for any top live pattern, so no `gh` lookup was run (none was needed to reach the verdicts above).

KB state is unchanged: pytest and `kb-selftest` results below are for the unchanged KB plus the runner fix.

## 5. Rejected ideas

- KB entries for the str-unpack and disjoint-bases patterns: see section 4.
- `ty_TA_nested_tuple_compare` as a parent: no signal on 0.0.84 at depth 20.
- Promoting replay findings whose strong evidence is a `NameError` or `UnboundLocalError` (195 of the 625): the fragment never defines the name; harness artifact.
- Promoting the two large live crash programs (`pyright__matchSequence2`, 189 lines; `pyright__typeVarDefaultTypeAlias2`, 141 lines): too big to serve as a brief; their crash signatures are already represented by smaller parents.
- Promoting every "runtime value does not inhabit the revealed type" finding (98 findings, 63 programs, `inhabit.txt`). In the sample I read, the
  mypy side is a declared type that the mdtest violates on purpose (`x: list[int] = [1, "2"]`) or a declared type that ty's flow-narrowing overrides
  (try/except flows); only the IntEnum alias, total_ordering, metaclass-operator and attribute-narrowing cases looked like real checker errors, and those are parents. The rest of the list was not individually reviewed.
- `ty__enums__24`, `ty__enums__35`, `OverloadedNewAndInitNoReturn`, `class__slots__16/17/61`, `ty__del__4`, `ty__narrow__truthiness__2`,
  `tuple7/8/9`, `Union[()]`, `hashability1/2`: the runtime error is caused by an empty stub body or a declared-but-unset attribute, or the tools' answers are a documented design choice.
- Widening TY-CHECK-NOT-IMPLEMENTED for `unsupported-bool-conversion`: mypy's miss is a candidate, not noise.
- Using an LLM for any of this: not needed; every promotion is a copy or a hand-trim of a program that already exists.

## 6. Off-plan defect fixed

Found while running the hits through the pipeline: 16 `pyright` node processes (1.4 to 4.4 h old, ~100 % CPU, 0.5-1 GB RSS each) were orphaned by
earlier timeouts. `Runners._exec` used `subprocess.run(timeout=)`, which kills only the `pyright` launcher, not its node child. They slowed every
run and are a plausible contributor to the earlier out-of-memory exits. Fix (commit `032bf3d`): run each tool in its own session and SIGKILL the
process group on timeout; output on timeout is unchanged (`TIMEOUT after Ns`, `code=None`). Tests: `tests/test_runner_timeout_kills_group.py` (3).
The 16 leftover orphans (only pyright processes with `--outputjson case.py`, parent init, older than 1 h) were killed by `campaign/day3m/reap_orphans.py`.

One related behaviour to know about, not changed: the crash dedupe by signature inside a run can hide a different bug that shares a signature
(here the `Stream[Stream[T]]` ty overflow was dismissed as "DUPLICATE of" the A1 overflow). Upstream entries avoid this through their mandatory `requires` shape.

## 7. Verification

- `python -m pytest tests -q`: **360 passed** (357 before + 3 new), 63.6 s, after the runner fix. (`campaign/day3m/pytest.txt`)
- `typediff --python-version 3.13 kb-selftest`: **20 PASS, 0 FAIL**, exit 0. (`campaign/day3m/kb-selftest.txt`)
- Replay verify-sample: 50/50 identical to a full re-run.
- `runs/hits`: 32 files, header + AREAS + compile + preflight (no ERROR) + `py_compile` all pass.
