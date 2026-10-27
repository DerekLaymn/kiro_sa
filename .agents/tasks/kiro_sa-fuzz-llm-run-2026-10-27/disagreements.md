# DISAGREEMENTS: fuzz/llm-run-2026-10-27

Pipeline: `TYPEDIFF_LLM=null typediff --out typediff_out --python-version 3.13 seeds gen` (deterministic: KB, oracles, experiments; undecided goes to review).
Results dir: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/`; dataset: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/dataset.jsonl`; triage (full, `--top 40 --details`): `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/triage.txt`; run log: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/run.log`.

## Counts summary

- Programs run: 142 (all 142 files in gen/, 17 area dirs; 8 genB files were first rejected by the preflight for sys.argv and ran in a second pass, see Notes)
- Total discrepancies (dataset records): 199
- Closed automatically (dismissed): 38
  - DESIGN_DIVERGENCE: 27
  - KNOWN_LIMITATION: 6
  - CONFIG_ARTIFACT: 3
  - SPEC_AMBIGUITY: 2
  - by KB/decider: kb:PRECISION-RUNTIME-CONSISTENT=8, kb:MYPY-SKIPS-UNREACHABLE=8, kb:LITERAL-WIDENING=8, kb:JOIN-VS-UNION=5, kb:MYPY-OPTIONAL-CHECK=3, kb:BOTH-GRADUAL=2, kb:SUPPRESSION-SEMANTICS=1, kb:TY-CHECK-NOT-IMPLEMENTED=1, kb:TY-GRADUAL-GENERIC-NARROWING=1, kb:UPSTREAM-TY-4212=1
- In review queue (NEEDS_HUMAN, no LLM): 161 discrepancies across 81 programs
  - by kind: reveal_mismatch=112, only_mypy=33, only_ty=14, concern_mismatch=2
- Review items with strong verified bug evidence (the triage `*` ones): 10 (triage: 7 + 2 + 1 = 10 listed under 3 patterns)
- Crashes: 0
- Invalid programs: 0
- Tool versions: mypy 2.4.0 (compiled: yes); ty 0.0.84; 3.13.16.
- Notes: (1) 8 genB programs (callables/genB_cb_self_attr_callable_12, generics_variance/genB_bound_self_referential_05, 5 in paramspec_concatenate, typevartuple_unpack/genB_tvt_callable_args_05) were rejected by the typediff preflight because sys.argv is a nondeterministic construct. I replaced the guard `len(sys.argv) > 99` with `len("") > 99` in those gen/ files (same intent: never-executed error lines are still type-checked) and ran them into the same typediff_out (log: rerun.log). (2) pyright ran normally; the odd pyright version string in dataset records is only a wrapper banner. (3) With no LLM the gate sends everything it cannot explain to review, so the review count is an upper bound; most items are reveal_type formatting differences (uncomparable/gradual).

Per area (programs run / review items / strong):

| area | programs | review | strong | dismissed |
|---|---|---|---|---|
| async_generators | 7 | 9 | 0 | 1 |
| callables | 12 | 15 | 0 | 0 |
| constructors_metaclasses | 8 | 11 | 3 | 0 |
| dataclasses | 8 | 4 | 0 | 1 |
| descriptors_properties | 7 | 3 | 0 | 1 |
| enums_literals | 8 | 6 | 1 | 7 |
| generics_variance | 11 | 10 | 0 | 2 |
| inheritance_mro | 8 | 5 | 0 | 2 |
| match_statement | 7 | 19 | 0 | 3 |
| narrowing_builtin | 7 | 17 | 0 | 2 |
| narrowing_user | 7 | 9 | 1 | 3 |
| overloads | 8 | 8 | 0 | 0 |
| paramspec_concatenate | 10 | 7 | 0 | 0 |
| protocols | 7 | 6 | 0 | 2 |
| tuples_unpacking | 9 | 7 | 0 | 4 |
| typeddict | 8 | 17 | 1 | 6 |
| typevartuple_unpack | 10 | 8 | 4 | 4 |

Triage patterns (from triage.txt, review queue grouped): 45 findings (7 with strong bug evidence)  reveal_mismatch | different; 5 findings (2 with strong bug evidence)  reveal_mismatch | ty_more_precise; 1 findings (1 with strong bug evidence)  only_mypy | ('return-value',) | incompatible return value type (got _, expected _); 39 findings (0 with strong bug evidence)  reveal_mismatch | uncomparable; 20 findings (0 with strong bug evidence)  reveal_mismatch | gradual; 6 findings (0 with strong bug evidence)  only_ty | ('unused-type-ignore-comment',) | unused blanket _ directive; 4 findings (0 with strong bug evidence)  only_mypy | ('attr-defined',) | _ has no attribute _; 4 findings (0 with strong bug evidence)  only_ty | ('invalid-argument-type',) | argument to function _ is incorrect: expected _, found _; 3 findings (0 with strong bug evidence)  only_mypy | ('arg-type',) | argument n to _ has incompatible type _; expected _; 3 findings (0 with strong bug evidence)  reveal_mismatch | mypy_more_precise; 2 findings (0 with strong bug evidence)  only_ty | ('invalid-return-type',) | return type does not match returned value: expected _, found _; 2 findings (0 with strong bug evidence)  only_mypy | ('misc',) | cannot infer value of type parameter _ of _

## Strong-evidence items (judge these first)

| id | area | kind | summary |
|---|---|---|---|
| 20261027-194745-8c4c34d5:D4 | constructors_metaclasses | reveal_mismatch | `reveal_type(v)` line 15 |
| 20261027-194745-8c4c34d5:D5 | constructors_metaclasses | reveal_mismatch | `reveal_type(w)` line 18 |
| 20261027-194749-43a57668:D2 | constructors_metaclasses | reveal_mismatch | `reveal_type(k)` line 18 |
| 20261027-194814-c8a4b97b:D2 | enums_literals | reveal_mismatch | `reveal_type(F.R / F.W)` line 31 |
| 20261027-194856-5ce43559:D1 | narrowing_user | reveal_mismatch | `reveal_type(b.items[0])` line 27 |
| 20261027-194942-40b2a3a0:D1 | typeddict | reveal_mismatch | `reveal_type(s["name"])` line 28 |
| 20261027-194951-e477e717:D1 | typevartuple_unpack | only_mypy | `return (*a, *b)` line 5 |
| 20261027-194951-e477e717:D2 | typevartuple_unpack | reveal_mismatch | `reveal_type(cat((1, "a"), (2.0,)))` line 8 |
| 20261027-194952-e7e24cc6:D1 | typevartuple_unpack | reveal_mismatch | `reveal_type(ident(x))` line 14 |
| 20261027-194953-8512cb21:D2 | typevartuple_unpack | reveal_mismatch | `reveal_type(y)` line 16 |

## Review items grouped by feature area

Format per item: id, kind, source, case files, mypy vs ty vs pyright, KB hints / decided_by, strong evidence, generator hypothesis. `*` marks strong bug evidence.

### async_generators (9 items)

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/async_generators/genD_async_comprehension_await_03.py`
- case: 20261027-194720-06f0236c | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194720-06f0236c.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194720-06f0236c.md`
- hypothesis: async comprehensions with await, async genexp type, gather over list[Awaitable]

- 20261027-194720-06f0236c:D1 [reveal_mismatch] line 20 `reveal_type(c)`
  - mypy: reveal `typing.AsyncGenerator[int, None]`
  - ty: reveal `AsyncGeneratorType[int, None]`
  - pyright: reveal `AsyncGenerator[int, None]`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194720-06f0236c:D2 [reveal_mismatch] line 24 `reveal_type(e)`
  - mypy: reveal `list[typing.Coroutine[Any, Any, int]]`
  - ty: reveal `list[CoroutineType[Any, Any, int]]`
  - pyright: reveal `list[CoroutineType[Any, Any, int]]`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/async_generators/genD_asynccontextmanager_04.py`
- case: 20261027-194727-95d9d021 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194727-95d9d021.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194727-95d9d021.md`
- hypothesis: asynccontextmanager signature and tuple-unpacking `as`

- 20261027-194727-95d9d021:D1 [reveal_mismatch] line 21 `reveal_type(res)`
  - mypy: reveal `def (name: str) -> contextlib._AsyncGeneratorContextManager[list[str], None]`
  - ty: reveal `(name: str) -> _AsyncGeneratorContextManager[list[str], None]`
  - pyright: reveal `(name: str) -> _AsyncGeneratorContextManager[list[str], None]`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/async_generators/genD_coroutine_vs_gen_decorator_06.py`
- case: 20261027-194728-25a34e92 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194728-25a34e92.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194728-25a34e92.md`
- hypothesis: Awaitable vs Coroutine callable assignability, Task, gather tuple

- 20261027-194728-25a34e92:D1 [only_mypy] line 18 `reveal_type(leaf(1))`
  - mypy: [unused-coroutine] Value of type "Coroutine[Any, Any, str]" must be used
  - ty: (nothing)
  - pyright: reveal `CoroutineType[Any, Any, str]`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194728-25a34e92:D2 [reveal_mismatch] line 17 `reveal_type(leaf)`
  - mypy: reveal `def (x: int) -> typing.Coroutine[Any, Any, str]`
  - ty: reveal `def leaf(x: int) -> CoroutineType[Any, Any, str]`
  - pyright: reveal `(x: int) -> CoroutineType[Any, Any, str]`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194728-25a34e92:D3 [reveal_mismatch] line 18 `reveal_type(leaf(1))`
  - mypy: reveal `typing.Coroutine[Any, Any, str]`
  - ty: reveal `CoroutineType[Any, Any, str]`
  - pyright: reveal `CoroutineType[Any, Any, str]`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/async_generators/genD_yield_from_iterable_05.py`
- case: 20261027-194730-f261f6b1 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194730-f261f6b1.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194730-f261f6b1.md`
- hypothesis: yield from in Iterator/Iterable return types; str yielded into Iterator[int] (intended error)

- 20261027-194730-f261f6b1:D1 [only_mypy] line 17 `r = yield from [1, 2]`
  - mypy: [func-returns-value] Function does not return a value (it only ever returns None)
  - ty: (nothing)
  - KB hints: TY-CHECK-MISSING-JUDGE-MYPY, TY-CHECK-PARTIAL | decided_by: gate | symptom: None

- 20261027-194730-f261f6b1:D2 [reveal_mismatch] line 18 `reveal_type(r)`
  - mypy: reveal `None`
  - ty: reveal `Unknown`
  - pyright: reveal `Unknown`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194730-f261f6b1:D3 [reveal_mismatch] line 25 `reveal_type(x)`
  - mypy: reveal `str`
  - ty: reveal `Unknown`
  - pyright: reveal `str`
  - KB hints: - | decided_by: gate | symptom: None

### callables (15 items)

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/callables/genB_cb_bound_method_07.py`
- case: 20261027-194731-8c7c5337 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194731-8c7c5337.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194731-8c7c5337.md`
- hypothesis: bound vs unbound method assignability

- 20261027-194731-8c7c5337:D1 [reveal_mismatch] line 14 `reveal_type(a)`
  - mypy: reveal `def (int) -> str`
  - ty: reveal `bound method C.m(n: int) -> str`
  - pyright: reveal `(n: int) -> str`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194731-8c7c5337:D2 [reveal_mismatch] line 15 `reveal_type(b)`
  - mypy: reveal `def (case.C, int) -> str`
  - ty: reveal `def m(self, n: int) -> str`
  - pyright: reveal `(self: C, n: int) -> str`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/callables/genB_cb_callable_in_union_narrow_10.py`
- case: 20261027-194732-d141e520 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194732-d141e520.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194732-d141e520.md`
- hypothesis: `callable()` narrowing on `int \

- 20261027-194732-d141e520:D1 [only_ty] line 8 `return x()`
  - mypy: (nothing)
  - ty: [invalid-return-type] Return type does not match returned value: expected `int`, found `object`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194732-d141e520:D2 [reveal_mismatch] line 7 `reveal_type(x)`
  - mypy: reveal `def () -> int`
  - ty: reveal `(int & ((...) -> object)) | (() -> int) | (str & ((...) -> object))`
  - pyright: reveal `() -> int`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194732-d141e520:D3 [reveal_mismatch] line 9 `reveal_type(x)`
  - mypy: reveal `int | str`
  - ty: reveal `(int & ~Top[(...) -> object]) | (str & ~Top[(...) -> object])`
  - pyright: reveal `int | str`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/callables/genB_cb_contravariant_param_04.py`
- case: 20261027-194734-ea227106 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194734-ea227106.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194734-ea227106.md`
- hypothesis: param contravariance / return covariance

- 20261027-194734-ea227106:D1 [reveal_mismatch] line 19 `reveal_type(f(B()))`
  - mypy: reveal `case.A`
  - ty: reveal `B`
  - pyright: reveal `B`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/callables/genB_cb_default_args_02.py`
- case: 20261027-194735-111aded4 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194735-111aded4.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194735-111aded4.md`
- hypothesis: default args and Callable arity assignability

- 20261027-194735-111aded4:D1 [reveal_mismatch] line 12 `reveal_type(a)`
  - mypy: reveal `def (int) -> int`
  - ty: reveal `def f(x: int, y: int = 1) -> int`
  - pyright: reveal `(x: int, y: int = 1) -> int`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/callables/genB_cb_kwargs_forward_05.py`
- case: 20261027-194737-d8db1038 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194737-d8db1038.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194737-d8db1038.md`
- hypothesis: `**kwargs: int` satisfies named kw-only protocol; `**kwargs: str` does not

- 20261027-194737-d8db1038:D1 [reveal_mismatch] line 18 `reveal_type(p)`
  - mypy: reveal `case.P`
  - ty: reveal `def k(**kwargs: int) -> int`
  - pyright: reveal `(**kwargs: int) -> int`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/callables/genB_cb_overloaded_to_callable_11.py`
- case: 20261027-194738-4ea8d8e9 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194738-4ea8d8e9.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194738-4ea8d8e9.md`
- hypothesis: overloaded function assigned to Callable (matching, non-matching, union)

- 20261027-194738-4ea8d8e9:D1 [reveal_mismatch] line 16 `reveal_type(a)`
  - mypy: reveal `def (int) -> int`
  - ty: reveal `Overload[(x: int) -> int, (x: str) -> str]`
  - pyright: reveal `Overload[(x: int) -> int, (x: str) -> str]`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/callables/genB_cb_protocol_kwonly_01.py`
- case: 20261027-194739-11ffa936 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194739-11ffa936.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194739-11ffa936.md`
- hypothesis: callback protocol kw-only param name must match

- 20261027-194739-11ffa936:D1 [reveal_mismatch] line 18 `reveal_type(a)`
  - mypy: reveal `case.CB`
  - ty: reveal `def f1(x: int) -> int`
  - pyright: reveal `(x: int) -> int`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/callables/genB_cb_staticmethod_classmethod_08.py`
- case: 20261027-194740-5f87666c | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194740-5f87666c.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194740-5f87666c.md`
- hypothesis: static/classmethod via instance and class as Callable

- 20261027-194740-5f87666c:D1 [reveal_mismatch] line 20 `reveal_type(c.k)`
  - mypy: reveal `def (n: int) -> int`
  - ty: reveal `bound method type[C].k(n: int) -> int`
  - pyright: reveal `(n: int) -> int`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/callables/genB_cb_varargs_to_fixed_03.py`
- case: 20261027-194740-ac1c2946 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194740-ac1c2946.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194740-ac1c2946.md`
- hypothesis: `*args: int` fits fixed arity; fixed does not fit larger arity

- 20261027-194740-ac1c2946:D1 [reveal_mismatch] line 16 `reveal_type(x)`
  - mypy: reveal `def (int, int) -> int`
  - ty: reveal `def v(*args: int) -> int`
  - pyright: reveal `(*args: int) -> int`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/callables/genB_cb_self_attr_callable_12.py`
- case: 20261027-202447-6a63fa0a | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-202447-6a63fa0a.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-202447-6a63fa0a.md`
- hypothesis: Callable instance attr vs ClassVar[Callable]: self binding differs

- 20261027-202447-6a63fa0a:D1 [only_mypy] line 20 `reveal_type(h.cls_attr)`
  - mypy: [misc] Invalid self argument "H" to attribute function "cls_attr" with type "Callable[[int], int]"
  - ty: (nothing)
  - pyright: reveal `() -> int`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-202447-6a63fa0a:D2 [only_mypy] line 24 `print(h.cls_attr(1))`
  - mypy: [misc] Invalid self argument "H" to attribute function "cls_attr" with type "Callable[[int], int]"; [call-arg] Too many arguments
  - ty: (nothing)
  - pyright: [reportCallIssue] Expected 0 positional arguments
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-202447-6a63fa0a:D3 [reveal_mismatch] line 20 `reveal_type(h.cls_attr)`
  - mypy: reveal `def () -> int`
  - ty: reveal `(int, /) -> int`
  - pyright: reveal `() -> int`
  - KB hints: - | decided_by: gate | symptom: None

### constructors_metaclasses (11 items)

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/constructors_metaclasses/genC_metaclass_call_returns_other_02.py`
- case: 20261027-194745-8c4c34d5 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194745-8c4c34d5.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194745-8c4c34d5.md`
- hypothesis: Metaclass __call__ annotated to return a different type than the class

- * 20261027-194745-8c4c34d5:D4 [reveal_mismatch] line 15 `reveal_type(v)`
  - mypy: reveal `case.K`
  - ty: reveal `int`
  - pyright: reveal `int`
  - KB hints: - | decided_by: gate | symptom: None
  - strong evidence: runtime value '42' of type builtins.int does NOT inhabit mypy's revealed type K

- * 20261027-194745-8c4c34d5:D5 [reveal_mismatch] line 18 `reveal_type(w)`
  - mypy: reveal `case.K`
  - ty: reveal `int`
  - pyright: reveal `int`
  - KB hints: - | decided_by: gate | symptom: None
  - strong evidence: runtime value '42' of type builtins.int does NOT inhabit mypy's revealed type K

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/constructors_metaclasses/genC_new_returns_subclass_08.py`
- case: 20261027-194749-43a57668 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194749-43a57668.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194749-43a57668.md`
- hypothesis: __new__ returning a different class instance that skips __init__ (not instance of cls)

- * 20261027-194749-43a57668:D2 [reveal_mismatch] line 18 `reveal_type(k)`
  - mypy: reveal `case.K`
  - ty: reveal `Other`
  - pyright: reveal `Other`
  - KB hints: - | decided_by: gate | symptom: None
  - strong evidence: runtime value '<__main__.Other object at 0x7ffa29eba120>' of type __main__.Other does NOT inhabit mypy's revealed type K

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/constructors_metaclasses/genC_init_subclass_kwargs_04.py`
- case: 20261027-194742-d8850f11 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194742-d8850f11.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194742-d8850f11.md`
- hypothesis: __init_subclass__ keyword parameters, required kw, and missing kw at class definition

- 20261027-194742-d8850f11:D1 [only_mypy] line 10 `cls.weight = weight`
  - mypy: [attr-defined] "type[Plugin]" has no attribute "weight"
  - ty: (nothing)
  - KB hints: TY-CHECK-MISSING-JUDGE-MYPY, TY-CHECK-PARTIAL | decided_by: gate | symptom: None

- 20261027-194742-d8850f11:D2 [only_mypy] line 27 `reveal_type(A.weight)`
  - mypy: [attr-defined] "type[A]" has no attribute "weight"
  - ty: (nothing)
  - pyright: reveal `int`
  - KB hints: TY-CHECK-MISSING-JUDGE-MYPY, TY-CHECK-PARTIAL | decided_by: gate | symptom: None

- 20261027-194742-d8850f11:D3 [only_mypy] line 28 `print(A.weight, B.weight, sorted(Plugin.registry))`
  - mypy: [attr-defined] "type[A]" has no attribute "weight"; [attr-defined] "type[B]" has no attribute "weight"
  - ty: (nothing)
  - KB hints: TY-CHECK-MISSING-JUDGE-MYPY, TY-CHECK-PARTIAL | decided_by: gate | symptom: None

- 20261027-194742-d8850f11:D4 [reveal_mismatch] line 27 `reveal_type(A.weight)`
  - mypy: reveal `Any`
  - ty: reveal `int`
  - pyright: reveal `int`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/constructors_metaclasses/genC_metaclass_call_returns_other_02.py`
- case: 20261027-194745-8c4c34d5 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194745-8c4c34d5.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194745-8c4c34d5.md`
- hypothesis: Metaclass __call__ annotated to return a different type than the class

- 20261027-194745-8c4c34d5:D1 [only_mypy] line 14 `v = K()`
  - mypy: [call-arg] Missing positional argument "x" in call to "K"
  - ty: (nothing)
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194745-8c4c34d5:D2 [only_mypy] line 16 `print(v + 1)`
  - mypy: [operator] Unsupported operand types for + ("K" and "int")
  - ty: (nothing)
  - KB hints: ERROR-CASCADE | decided_by: gate | symptom: None

- 20261027-194745-8c4c34d5:D3 [only_mypy] line 17 `w = K("a", "b", z=1)`
  - mypy: [call-arg] Too many arguments for "K"; [call-arg] Unexpected keyword argument "z" for "K"
  - ty: (nothing)
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/constructors_metaclasses/genC_new_returns_subclass_08.py`
- case: 20261027-194749-43a57668 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194749-43a57668.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194749-43a57668.md`
- hypothesis: __new__ returning a different class instance that skips __init__ (not instance of cls)

- 20261027-194749-43a57668:D1 [only_ty] line 10 `def __new__(cls) -> Other:  # type: ignore`
  - mypy: (nothing)
  - ty: [unused-type-ignore-comment] Unused blanket `type: ignore` directive
  - KB hints: MYPY-OPTIONAL-CHECK, SUPPRESSION-LINE | decided_by: gate | symptom: None

### dataclasses (4 items)

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/dataclasses/genA_generic_dataclass_05.py`
- case: 20261027-194753-8a725af4 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194753-8a725af4.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194753-8a725af4.md`
- hypothesis: generic dataclass with specialized subclass; inference of Box(1, ["x"]) may differ.

- 20261027-194753-8a725af4:D1 [only_mypy] line 26 `bad = Box(1, ["x"])`
  - mypy: [misc] Cannot infer value of type parameter "T" of "Box"
  - ty: (nothing)
  - pyright: [reportArgumentType] Argument of type "list[str]" cannot be assigned to parameter "extras" of type "list[T@Box]" in function "__init__"
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/dataclasses/genA_kw_only_inherit_01.py`
- case: 20261027-194754-efdcc08e | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194754-efdcc08e.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194754-efdcc08e.md`
- hypothesis: KW_ONLY in base then non-kw field in child: checkers may disagree on synthesized __init__ order.

- 20261027-194754-efdcc08e:D1 [reveal_mismatch] line 25 `reveal_type(Child.__init__)`
  - mypy: reveal `def (self: case.Child, a: int, c: float =, *, b: str =)`
  - ty: reveal `(self: Child, a: int, c: float = ..., *, b: str = "b") -> None`
  - pyright: reveal `(self: Child, a: int, c: float = 1, *, b: str = "b") -> None`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/dataclasses/genA_postinit_initvar_07.py`
- case: 20261027-194757-edc14252 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194757-edc14252.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194757-edc14252.md`
- hypothesis: InitVar inheritance and __post_init__ signature check; access to Sub.extra may differ.

- 20261027-194757-edc14252:D1 [only_mypy] line 27 `reveal_type(Sub.extra)`
  - mypy: [attr-defined] "type[Sub]" has no attribute "extra"
  - ty: (nothing)
  - pyright: reveal `Unknown`; [reportAttributeAccessIssue] Cannot access attribute "extra" for class "type[Sub]"
  - KB hints: TY-CHECK-MISSING-JUDGE-MYPY, TY-CHECK-PARTIAL | decided_by: gate | symptom: None

- 20261027-194757-edc14252:D2 [reveal_mismatch] line 27 `reveal_type(Sub.extra)`
  - mypy: reveal `Any`
  - ty: reveal `int`
  - pyright: reveal `Unknown`; [reportAttributeAccessIssue] Cannot access attribute "extra" for class "type[Sub]"
  - KB hints: - | decided_by: gate | symptom: None

### descriptors_properties (3 items)

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/descriptors_properties/genC_cached_property_02.py`
- case: 20261027-194759-b7be913f | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194759-b7be913f.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194759-b7be913f.md`
- hypothesis: functools.cached_property: class access, assignment, deletion, and override in subclass by plain attribute

- 20261027-194759-b7be913f:D1 [only_ty] line 26 `value = "overridden"  # type: ignore`
  - mypy: (nothing)
  - ty: [unused-type-ignore-comment] Unused blanket `type: ignore` directive
  - KB hints: MYPY-OPTIONAL-CHECK, SUPPRESSION-LINE | decided_by: gate | symptom: None

- 20261027-194759-b7be913f:D2 [reveal_mismatch] line 16 `reveal_type(A.value)`
  - mypy: reveal `def (self: case.A) -> int`
  - ty: reveal `cached_property[int]`
  - pyright: reveal `cached_property[int]`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/descriptors_properties/genC_property_override_attr_06.py`
- case: 20261027-194804-07bd650d | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194804-07bd650d.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194804-07bd650d.md`
- hypothesis: Subclass overrides property with plain attribute and vice versa; deleter semantics

- 20261027-194804-07bd650d:D2 [only_ty] line 19 `def v(self) -> int:  # type: ignore`
  - mypy: (nothing)
  - ty: [unused-type-ignore-comment] Unused blanket `type: ignore` directive
  - KB hints: MYPY-OPTIONAL-CHECK, SUPPRESSION-LINE | decided_by: gate | symptom: None

### enums_literals (6 items)

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/enums_literals/genA_enum_value_types_02.py`
- case: 20261027-194814-c8a4b97b | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194814-c8a4b97b.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194814-c8a4b97b.md`
- hypothesis: StrEnum/IntEnum/Flag/tuple-valued .value and operator reveals differ.

- * 20261027-194814-c8a4b97b:D2 [reveal_mismatch] line 31 `reveal_type(F.R | F.W)`
  - mypy: reveal `case.F`
  - ty: reveal `Literal[F.R, F.W]`
  - pyright: reveal `F`
  - KB hints: LITERAL-WIDENING | decided_by: gate | symptom: None
  - strong evidence: runtime value '<F.R|W: 3>' of type __main__.F does NOT inhabit ty's revealed type Literal[F.R] | Literal[F.W]
  - strong evidence: KB:LITERAL-WIDENING would explain this, but runtime value '<F.R|W: 3>' (__main__.F) is outside ty's type Literal[F.R] | Literal[F.W]

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/enums_literals/genA_enum_bool_truthy_07.py`
- case: 20261027-194807-208af9db | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194807-208af9db.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194807-208af9db.md`
- hypothesis: truthiness narrowing of enums with/without __bool__ and Literal[0,1].

- 20261027-194807-208af9db:D1 [only_ty] line 21 `if b:`
  - mypy: (nothing)
  - ty: [redundant-condition] Object of type `Bit` is always truthy
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194807-208af9db:D3 [reveal_mismatch] line 26 `reveal_type(f)`
  - mypy: reveal `case.Flagged`
  - ty: reveal `Flagged & ~AlwaysFalsy`
  - pyright: reveal `Flagged`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194807-208af9db:D4 [reveal_mismatch] line 28 `reveal_type(f)`
  - mypy: reveal `case.Flagged`
  - ty: reveal `Flagged & ~AlwaysTruthy`
  - pyright: reveal `Flagged`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/enums_literals/genA_enum_final_nonmember_06.py`
- case: 20261027-194810-f2f1b453 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194810-f2f1b453.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194810-f2f1b453.md`
- hypothesis: member()/nonmember()/_ignore_/Final inside Enum treated differently.

- 20261027-194810-f2f1b453:D1 [reveal_mismatch] line 24 `reveal_type(K.helper)`
  - mypy: reveal `def (self: case.K) -> int`
  - ty: reveal `def helper(self) -> int`
  - pyright: reveal `(self: K) -> int`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/enums_literals/genA_enum_members_methods_05.py`
- case: 20261027-194812-13f4ef5e | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194812-13f4ef5e.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194812-13f4ef5e.md`
- hypothesis: enum with __init__ tuple values, attrs, classmethod, __members__ reveals.

- 20261027-194812-13f4ef5e:D1 [reveal_mismatch] line 25 `reveal_type(Planet.EARTH.value)`
  - mypy: reveal `tuple[float, float]`
  - ty: reveal `Any`
  - pyright: reveal `Any`
  - KB hints: - | decided_by: gate | symptom: None

### generics_variance (10 items)

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/generics_variance/genB_constrained_union_arg_07.py`
- case: 20261027-194816-bed4617d | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194816-bed4617d.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194816-bed4617d.md`
- hypothesis: constrained TypeVar given `int \

- 20261027-194816-bed4617d:D1 [reveal_mismatch] line 10 `reveal_type(r)`
  - mypy: reveal `int | str`
  - ty: reveal `Unknown`
  - pyright: reveal `Unknown`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/generics_variance/genB_invariant_dict_values_10.py`
- case: 20261027-194818-1ef16884 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194818-1ef16884.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194818-1ef16884.md`
- hypothesis: dict to Mapping: value covariant, key invariant

- 20261027-194818-1ef16884:D1 [reveal_mismatch] line 12 `reveal_type(m1)`
  - mypy: reveal `typing.Mapping[str, float]`
  - ty: reveal `dict[str, int]`
  - pyright: reveal `dict[str, int]`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/generics_variance/genB_pep695_callable_attr_variance_04.py`
- case: 20261027-194819-b0b61389 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194819-b0b61389.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194819-b0b61389.md`
- hypothesis: mutable Callable[[T], None] attribute: invariant vs contravariant inference

- 20261027-194819-b0b61389:D1 [only_ty] line 16 `use(hf)  # attribute is mutable -> invariant: error expected`
  - mypy: (nothing)
  - ty: [invalid-argument-type] Argument to function `use` is incorrect: Expected `Handler[int]`, found `Handler[float]`
  - pyright: [reportArgumentType] Argument of type "Handler[float]" cannot be assigned to parameter "h" of type "Handler[int]" in function "use"
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/generics_variance/genB_pep695_frozen_covariant_02.py`
- case: 20261027-194822-5a240f4d | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194822-5a240f4d.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194822-5a240f4d.md`
- hypothesis: read-only property infers covariant, method param infers contravariant

- 20261027-194822-5a240f4d:D1 [reveal_mismatch] line 24 `reveal_type(ri)`
  - mypy: reveal `case.Ro[int]`
  - ty: reveal `Ro[Literal[1]]`
  - pyright: reveal `Ro[int]`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194822-5a240f4d:D2 [reveal_mismatch] line 28 `reveal_type(si)`
  - mypy: reveal `case.Sink[int]`
  - ty: reveal `Sink[float]`
  - pyright: reveal `Sink[float]`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/generics_variance/genB_typevar_default_pep696_09.py`
- case: 20261027-194825-360b5d1e | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194825-360b5d1e.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194825-360b5d1e.md`
- hypothesis: PEP696 default `V = int` with partial specialization and mismatched construction

- 20261027-194825-360b5d1e:D1 [concern_mismatch] line 15 `r: Pair[str] = Pair("a", "b")  # error: V is int`
  - mypy: [arg-type] Argument 2 to "Pair" has incompatible type "str"; expected "int"
  - ty: [invalid-assignment] Object of type `Pair[str, str]` is not assignable to `Pair[str, int]`
  - pyright: [reportAssignmentType] Type "Pair[str, str]" is not assignable to declared type "Pair[str, int]"
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/generics_variance/genB_bound_self_referential_05.py`
- case: 20261027-202452-8a6304e4 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-202452-8a6304e4.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-202452-8a6304e4.md`
- hypothesis: TypeVar bound to Protocol with `__lt__(Cmp)`; mixed int/float solving

- 20261027-202452-8a6304e4:D1 [only_mypy] line 18 `mx(object(), object())  # error: bound violation (never executed)`
  - mypy: [type-var] Value of type variable "T" of "mx" cannot be "object"
  - ty: (nothing)
  - pyright: [reportArgumentType] Argument of type "object" cannot be assigned to parameter "a" of type "T@mx" in function "mx"; [reportArgumentType] Argument of type "object" cannot be assigned to parameter "b" of type "T@mx" in function "mx"
  - KB hints: TY-CHECK-MISSING-JUDGE-MYPY, TY-CHECK-PARTIAL | decided_by: gate | symptom: None

- 20261027-202452-8a6304e4:D2 [reveal_mismatch] line 13 `reveal_type(mx(1, 2))`
  - mypy: reveal `int`
  - ty: reveal `Unknown`
  - pyright: reveal `Unknown`; [reportArgumentType] Argument of type "Literal[1]" cannot be assigned to parameter "a" of type "T@mx" in function "mx"; [reportArgumentType] Argument of type "Literal[2]" cannot be assigned to parameter "b" of type "T@mx" in function "mx"
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-202452-8a6304e4:D3 [reveal_mismatch] line 14 `reveal_type(mx("a", "b"))`
  - mypy: reveal `str`
  - ty: reveal `Unknown`
  - pyright: reveal `Unknown`; [reportArgumentType] Argument of type "Literal['a']" cannot be assigned to parameter "a" of type "T@mx" in function "mx"; [reportArgumentType] Argument of type "Literal['b']" cannot be assigned to parameter "b" of type "T@mx" in function "mx"
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-202452-8a6304e4:D4 [reveal_mismatch] line 15 `reveal_type(mx(1, 2.5))`
  - mypy: reveal `float`
  - ty: reveal `Unknown`
  - pyright: reveal `Unknown`; [reportArgumentType] Argument of type "Literal[1]" cannot be assigned to parameter "a" of type "T@mx" in function "mx"; [reportArgumentType] Argument of type "float" cannot be assigned to parameter "b" of type "T@mx" in function "mx"
  - KB hints: - | decided_by: gate | symptom: None

### inheritance_mro (5 items)

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/inheritance_mro/genC_attr_to_readonly_property_04.py`
- case: 20261027-194827-34ae8d15 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194827-34ae8d15.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194827-34ae8d15.md`
- hypothesis: Base attribute overridden by read-only property: assignment in Base.__init__ raises at runtime

- 20261027-194827-34ae8d15:D1 [only_ty] line 10 `def n(self) -> int:  # type: ignore`
  - mypy: (nothing)
  - ty: [unused-type-ignore-comment] Unused blanket `type: ignore` directive
  - KB hints: MYPY-OPTIONAL-CHECK, SUPPRESSION-LINE | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/inheritance_mro/genC_diamond_super_kwargs_01.py`
- case: 20261027-194829-3b66c420 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194829-3b66c420.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194829-3b66c420.md`
- hypothesis: Cooperative diamond super() with kwargs passthrough; MRO order and type of super() result

- 20261027-194829-3b66c420:D1 [reveal_mismatch] line 34 `reveal_type(super())`
  - mypy: reveal `super`
  - ty: reveal `<super: <class 'D'>, Self@who>`
  - pyright: reveal `Left`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/inheritance_mro/genC_mutable_attr_covariant_override_03.py`
- case: 20261027-194831-0dde95ca | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194831-0dde95ca.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194831-0dde95ca.md`
- hypothesis: Subclass narrows mutable attribute type (list[int] vs list[object], int vs int

- 20261027-194831-0dde95ca:D1 [only_ty] line 14 `items: list[int]  # type: ignore`
  - mypy: (nothing)
  - ty: [unused-type-ignore-comment] Unused blanket `type: ignore` directive
  - KB hints: MYPY-OPTIONAL-CHECK, SUPPRESSION-LINE | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/inheritance_mro/genC_override_param_rename_02.py`
- case: 20261027-194834-bb07d747 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194834-bb07d747.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194834-bb07d747.md`
- hypothesis: Override renames positional parameter; call-by-keyword through base type fails at runtime

- 20261027-194834-bb07d747:D1 [only_ty] line 10 `def f(self, y: int) -> int:  # LSP violation for keyword calls`
  - mypy: (nothing)
  - ty: [invalid-method-override] Invalid override of method `f`: Definition is incompatible with `Base.f`
  - pyright: [reportIncompatibleMethodOverride] Method "f" overrides class "Base" in an incompatible manner
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/inheritance_mro/genC_override_sync_to_async_07.py`
- case: 20261027-194835-77ba6513 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194835-77ba6513.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194835-77ba6513.md`
- hypothesis: Override sync method with async and staticmethod with instance method

- 20261027-194835-77ba6513:D1 [only_ty] line 18 `def util(self, x: int) -> int:  # type: ignore`
  - mypy: (nothing)
  - ty: [unused-type-ignore-comment] Unused blanket `type: ignore` directive
  - KB hints: MYPY-OPTIONAL-CHECK, SUPPRESSION-LINE | decided_by: gate | symptom: None

### match_statement (19 items)

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/match_statement/genD_assert_never_enum_03.py`
- case: 20261027-194838-9ebd498c | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194838-9ebd498c.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194838-9ebd498c.md`
- hypothesis: exhaustiveness with assert_never on enum and Literal incl. bool; ends with a runtime-true branch call

- 20261027-194838-9ebd498c:D1 [only_mypy] line 36 `assert_never(x)`
  - mypy: [arg-type] Argument 1 to "assert_never" has incompatible type "Literal[True]"; expected "Never"
  - ty: (nothing)
  - pyright: [reportArgumentType] Argument of type "Literal[True]" cannot be assigned to parameter "arg" of type "Never" in function "assert_never"
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194838-9ebd498c:D3 [reveal_mismatch] line 26 `reveal_type(x)`
  - mypy: reveal `Literal[1] | bool`
  - ty: reveal `Literal[1, True]`
  - pyright: reveal `bool | Literal[1]`
  - KB hints: TY-STRICT-EQUALITY | decided_by: gate | symptom: None

- 20261027-194838-9ebd498c:D4 [reveal_mismatch] line 35 `reveal_type(x)`
  - mypy: reveal `Literal[True]`
  - ty: reveal `Never`
  - pyright: reveal `Literal[True]`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/match_statement/genD_builtin_class_pattern_07.py`
- case: 20261027-194840-b0b45d0c | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194840-b0b45d0c.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194840-b0b45d0c.md`
- hypothesis: builtin class patterns bool(b)/int(i)/str(s) and or-patterns, 0 \

- 20261027-194840-b0b45d0c:D2 [reveal_mismatch] line 32 `reveal_type(x)`
  - mypy: reveal `int | str`
  - ty: reveal `(int & ~Literal[0] & ~Literal[False]) | (str & ~Literal[""])`
  - pyright: reveal `int | str`
  - KB hints: TY-GRADUAL-GENERIC-NARROWING | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/match_statement/genD_class_dataclass_positional_01.py`
- case: 20261027-194841-31b252fb | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194841-31b252fb.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194841-31b252fb.md`
- hypothesis: dataclass positional patterns skip kw_only fields; nested class/sequence

- 20261027-194841-31b252fb:D1 [reveal_mismatch] line 30 `reveal_type(o)`
  - mypy: reveal `case.Q`
  - ty: reveal `Q & ~P`
  - pyright: reveal `Q`
  - KB hints: TY-GRADUAL-GENERIC-NARROWING | decided_by: gate | symptom: None

- 20261027-194841-31b252fb:D2 [reveal_mismatch] line 33 `reveal_type(o)`
  - mypy: reveal `case.Q | int`
  - ty: reveal `(Q & ~P) | (int & ~P)`
  - pyright: reveal `Q | int`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/match_statement/genD_guard_narrowing_04.py`
- case: 20261027-194842-20a180d2 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194842-20a180d2.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194842-20a180d2.md`
- hypothesis: guards and narrowing of subject in later cases

- 20261027-194842-20a180d2:D1 [reveal_mismatch] line 13 `reveal_type(s)`
  - mypy: reveal `str`
  - ty: reveal `str & ~AlwaysFalsy`
  - pyright: reveal `str`
  - KB hints: TY-GRADUAL-GENERIC-NARROWING | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/match_statement/genD_mapping_pattern_02.py`
- case: 20261027-194844-50d1934a | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194844-50d1934a.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194844-50d1934a.md`
- hypothesis: mapping patterns on dict, TypedDict, list unions; `**rest`

- 20261027-194844-50d1934a:D1 [reveal_mismatch] line 12 `reveal_type(d)`
  - mypy: reveal `dict[str, int] | TypedDict(case.Cmd, {'kind': str, 'n': int}) | list[int]`
  - ty: reveal `dict[str, int] | Cmd | (list[int] & Top[Mapping[Unknown, object]])`
  - pyright: reveal `dict[str, int] | Cmd`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194844-50d1934a:D2 [reveal_mismatch] line 13 `reveal_type(k)`
  - mypy: reveal `object | Any`
  - ty: reveal `object`
  - pyright: reveal `int | str`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194844-50d1934a:D3 [reveal_mismatch] line 14 `reveal_type(n)`
  - mypy: reveal `object | Any`
  - ty: reveal `object`
  - pyright: reveal `int`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194844-50d1934a:D4 [reveal_mismatch] line 17 `reveal_type(a)`
  - mypy: reveal `object | Any`
  - ty: reveal `object`
  - pyright: reveal `int`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194844-50d1934a:D5 [reveal_mismatch] line 18 `reveal_type(rest)`
  - mypy: reveal `dict[object, object]`
  - ty: reveal `dict[str, int] | dict[object, Unknown]`
  - pyright: reveal `dict[str, int]`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194844-50d1934a:D6 [reveal_mismatch] line 21 `reveal_type(d)`
  - mypy: reveal `dict[str, int] | TypedDict(case.Cmd, {'kind': str, 'n': int})`
  - ty: reveal `(dict[str, int] & ~Cmd) | (list[int] & Top[Mapping[Unknown, object]])`
  - pyright: reveal `dict[str, int] | Cmd | list[int]`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194844-50d1934a:D7 [reveal_mismatch] line 24 `reveal_type(d)`
  - mypy: reveal `list[int]`
  - ty: reveal `list[int] & ~Top[Mapping[Unknown, object]]`
  - pyright: reveal `dict[str, int] | Cmd | list[int]`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194844-50d1934a:D8 [reveal_mismatch] line 31 `reveal_type(v)`
  - mypy: reveal `int`
  - ty: reveal `Unknown & int`
  - pyright: reveal `int`
  - KB hints: TY-GRADUAL-GENERIC-NARROWING | decided_by: gate | symptom: None

- 20261027-194844-50d1934a:D9 [reveal_mismatch] line 34 `reveal_type(s)`
  - mypy: reveal `str`
  - ty: reveal `Unknown & str`
  - pyright: reveal `str`
  - KB hints: TY-GRADUAL-GENERIC-NARROWING | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/match_statement/genD_match_args_custom_06.py`
- case: 20261027-194845-3207d5e5 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194845-3207d5e5.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194845-3207d5e5.md`
- hypothesis: custom `__match_args__` order and reachability of later cases

- 20261027-194845-3207d5e5:D1 [reveal_mismatch] line 27 `reveal_type(o)`
  - mypy: reveal `case.<subclass of "builtins.int" and "case.Pt">`
  - ty: reveal `Never`
  - KB hints: TY-STRICT-EQUALITY, TY-GRADUAL-GENERIC-NARROWING | decided_by: gate | symptom: None

- 20261027-194845-3207d5e5:D2 [reveal_mismatch] line 30 `reveal_type(o)`
  - mypy: reveal `int`
  - ty: reveal `int & ~Pt`
  - pyright: reveal `int`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/match_statement/genD_sequence_star_tuple_05.py`
- case: 20261027-194846-3f1581af | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194846-3f1581af.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194846-3f1581af.md`
- hypothesis: sequence patterns on tuple unions, star captures, str/bytes excluded

- 20261027-194846-3f1581af:D1 [reveal_mismatch] line 39 `reveal_type(t)`
  - mypy: reveal `tuple[int, ...]`
  - ty: reveal `tuple[int, ...] & ~tuple[object, *tuple[object, ...], object]`
  - pyright: reveal `tuple[int, ...]`
  - KB hints: - | decided_by: gate | symptom: None

### narrowing_builtin (17 items)

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/narrowing_builtin/genD_callable_union_02.py`
- case: 20261027-194847-1a61f79a | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194847-1a61f79a.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194847-1a61f79a.md`
- hypothesis: callable() on union with callable instance, type[str] and non-callables

- 20261027-194847-1a61f79a:D1 [only_ty] line 22 `return v()`
  - mypy: (nothing)
  - ty: [invalid-return-type] Return type does not match returned value: expected `str`, found `object`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194847-1a61f79a:D2 [reveal_mismatch] line 11 `reveal_type(v)`
  - mypy: reveal `(def (int) -> int) | type[str]`
  - ty: reveal `(int & ((...) -> object)) | ((int, /) -> int) | type[str]`
  - pyright: reveal `((int) -> int) | Fn | type[str]`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194847-1a61f79a:D3 [reveal_mismatch] line 13 `reveal_type(v)`
  - mypy: reveal `int`
  - ty: reveal `int & ~Top[(...) -> object]`
  - pyright: reveal `int`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194847-1a61f79a:D4 [reveal_mismatch] line 19 `reveal_type(v)`
  - mypy: reveal `str`
  - ty: reveal `str & ~Top[(...) -> object]`
  - pyright: reveal `str`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194847-1a61f79a:D5 [reveal_mismatch] line 21 `reveal_type(v)`
  - mypy: reveal `def () -> str`
  - ty: reveal `(str & ((...) -> object)) | (() -> str)`
  - pyright: reveal `() -> str`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/narrowing_builtin/genD_hasattr_narrowing_03.py`
- case: 20261027-194849-4c0967e4 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194849-4c0967e4.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194849-4c0967e4.md`
- hypothesis: hasattr() narrowing (synthesized intersection in ty/pyright vs mypy)

- 20261027-194849-4c0967e4:D1 [reveal_mismatch] line 14 `reveal_type(x)`
  - mypy: reveal `case.A | case.B`
  - ty: reveal `A | (B & <Protocol with members 'name'>)`
  - pyright: reveal `A | B`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194849-4c0967e4:D2 [reveal_mismatch] line 16 `reveal_type(x)`
  - mypy: reveal `case.B`
  - ty: reveal `B & ~<Protocol with members 'name'>`
  - pyright: reveal `A | B`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194849-4c0967e4:D3 [reveal_mismatch] line 22 `reveal_type(x)`
  - mypy: reveal `object`
  - ty: reveal `<Protocol with members 'bit_length'>`
  - pyright: reveal `object`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/narrowing_builtin/genD_isinstance_generic_alias_08.py`
- case: 20261027-194850-2f3fc472 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194850-2f3fc472.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194850-2f3fc472.md`
- hypothesis: isinstance vs ABCs (Mapping/Sequence) on mixed unions; str/bytes are Sequence

- 20261027-194850-2f3fc472:D1 [reveal_mismatch] line 7 `reveal_type(x)`
  - mypy: reveal `typing.Mapping[str, int]`
  - ty: reveal `(int & Mapping[Unknown, Unknown]) | (Sequence[int] & Mapping[Unknown, Unknown]) | Mapping[str, int]`
  - pyright: reveal `Mapping[str, int]`
  - KB hints: TY-GRADUAL-GENERIC-NARROWING | decided_by: gate | symptom: None

- 20261027-194850-2f3fc472:D2 [reveal_mismatch] line 10 `reveal_type(x)`
  - mypy: reveal `typing.Sequence[int]`
  - ty: reveal `(int & Sequence[Unknown] & ~Top[Mapping[Unknown, object]]) | (Sequence[int] & ~Top[Mapping[Unknown, object]])`
  - pyright: reveal `Sequence[int]`
  - KB hints: TY-GRADUAL-GENERIC-NARROWING | decided_by: gate | symptom: None

- 20261027-194850-2f3fc472:D3 [reveal_mismatch] line 12 `reveal_type(x)`
  - mypy: reveal `int`
  - ty: reveal `int & ~Top[Mapping[Unknown, object]] & ~Sequence[object]`
  - pyright: reveal `int`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/narrowing_builtin/genD_isinstance_tuple_types_01.py`
- case: 20261027-194851-77099533 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194851-77099533.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194851-77099533.md`
- hypothesis: isinstance with tuple of classes, plus `and not isinstance(bool)` on object

- 20261027-194851-77099533:D1 [reveal_mismatch] line 17 `reveal_type(x)`
  - mypy: reveal `list[Any] | tuple[Any, ...]`
  - ty: reveal `list[Unknown] | tuple[Unknown, ...]`
  - pyright: reveal `list[Unknown] | tuple[Unknown, ...]`
  - KB hints: TY-GRADUAL-GENERIC-NARROWING | decided_by: gate | symptom: None

- 20261027-194851-77099533:D2 [reveal_mismatch] line 20 `reveal_type(x)`
  - mypy: reveal `int | str`
  - ty: reveal `(int & ~bool) | str`
  - pyright: reveal `int | str`
  - KB hints: TY-GRADUAL-GENERIC-NARROWING | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/narrowing_builtin/genD_issubclass_type_04.py`
- case: 20261027-194852-a2c8adec | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194852-a2c8adec.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194852-a2c8adec.md`
- hypothesis: issubclass on type[A]\

- 20261027-194852-a2c8adec:D1 [reveal_mismatch] line 11 `reveal_type(t)`
  - mypy: reveal `type[case.Left] | type[case.Right]`
  - ty: reveal `type[Left | Right] | (type[int] & type[Base])`
  - pyright: reveal `type[Left] | type[Right]`
  - KB hints: TY-GRADUAL-GENERIC-NARROWING | decided_by: gate | symptom: None

- 20261027-194852-a2c8adec:D2 [reveal_mismatch] line 13 `reveal_type(t)`
  - mypy: reveal `type[int]`
  - ty: reveal `type[int] & ~type[Base]`
  - pyright: reveal `type[int]`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194852-a2c8adec:D3 [reveal_mismatch] line 19 `reveal_type(t)`
  - mypy: reveal `type[case.Left] | type[case.Right]`
  - ty: reveal `type[Left | Right]`
  - pyright: reveal `type[Left] | type[Right]`
  - KB hints: TY-GRADUAL-GENERIC-NARROWING | decided_by: gate | symptom: None

- 20261027-194852-a2c8adec:D4 [reveal_mismatch] line 21 `reveal_type(t)`
  - mypy: reveal `type[case.Base]`
  - ty: reveal `type[Base] & ~type[Left] & ~type[Right]`
  - pyright: reveal `type[Base]`
  - KB hints: - | decided_by: gate | symptom: None

### narrowing_user (9 items)

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/narrowing_user/genD_typeis_attribute_target_02.py`
- case: 20261027-194856-5ce43559 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194856-5ce43559.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194856-5ce43559.md`
- hypothesis: TypeIs on attribute and subscript targets; invalidation on assignment

- * 20261027-194856-5ce43559:D1 [reveal_mismatch] line 27 `reveal_type(b.items[0])`
  - mypy: reveal `str`
  - ty: reveal `Literal[3]`
  - pyright: reveal `Literal[3]`
  - KB hints: - | decided_by: gate | symptom: None
  - strong evidence: runtime value '3' of type builtins.int does NOT inhabit mypy's revealed type str

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/narrowing_user/genD_typeis_callable_tuple_07.py`
- case: 20261027-194857-bac95359 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194857-bac95359.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194857-bac95359.md`
- hypothesis: TypeIs to tuple[int,int] and Callable[[int],int] on unions

- 20261027-194857-bac95359:D1 [reveal_mismatch] line 23 `reveal_type(x)`
  - mypy: reveal `int | (def (str) -> str)`
  - ty: reveal `(int & ~((int, /) -> int)) | (((str, /) -> str) & ~((int, /) -> int))`
  - pyright: reveal `int | ((int) -> int) | ((str) -> str)`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/narrowing_user/genD_typeis_final_class_never_06.py`
- case: 20261027-194858-7f55fffe | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194858-7f55fffe.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194858-7f55fffe.md`
- hypothesis: TypeIs with @final class against disjoint classes yields Never or the original type

- 20261027-194858-7f55fffe:D1 [reveal_mismatch] line 24 `reveal_type(x)`
  - mypy: reveal `case.F | case.Q`
  - ty: reveal `F | (Q & ~P)`
  - pyright: reveal `F | Q`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/narrowing_user/genD_typeis_generic_container_04.py`
- case: 20261027-194859-d8f036df | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194859-d8f036df.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194859-d8f036df.md`
- hypothesis: generic TypeIs[Sequence[T]] / PEP 695 TypeIs[list[T]] on unions

- 20261027-194859-d8f036df:D1 [reveal_mismatch] line 18 `reveal_type(x)`
  - mypy: reveal `typing.Sequence[int | str]`
  - ty: reveal `Sequence[int | str] & ~Sequence[int]`
  - pyright: reveal `Sequence[int | str]`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194859-d8f036df:D2 [reveal_mismatch] line 24 `reveal_type(x)`
  - mypy: reveal `list[object]`
  - ty: reveal `list[int]`
  - pyright: reveal `<subclass of Sequence[int] and list[int | str]> | <subclass of tuple[str, ...] and list[int | str]>`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194859-d8f036df:D3 [reveal_mismatch] line 26 `reveal_type(x)`
  - mypy: reveal `typing.Sequence[int] | tuple[str, ...]`
  - ty: reveal `(Sequence[int] & ~Top[list[Unknown]]) | tuple[str, ...]`
  - pyright: reveal `Sequence[int] | tuple[str, ...]`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/narrowing_user/genD_typeis_method_self_03.py`
- case: 20261027-194900-2e32ef3d | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194900-2e32ef3d.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194900-2e32ef3d.md`
- hypothesis: TypeIs/TypeGuard as method, staticmethod, classmethod; Any argument

- 20261027-194900-2e32ef3d:D1 [reveal_mismatch] line 25 `reveal_type(x)`
  - mypy: reveal `case.Square | int`
  - ty: reveal `(Square & ~Circle) | (int & ~Circle)`
  - pyright: reveal `Square | int`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194900-2e32ef3d:D3 [reveal_mismatch] line 33 `reveal_type(x)`
  - mypy: reveal `int`
  - ty: reveal `int & ~Shape`
  - pyright: reveal `int`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194900-2e32ef3d:D4 [reveal_mismatch] line 38 `reveal_type(x)`
  - mypy: reveal `case.Circle`
  - ty: reveal `Any & Circle`
  - pyright: reveal `Circle`
  - KB hints: - | decided_by: gate | symptom: None

### overloads (8 items)

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/overloads/genD_any_argument_02.py`
- case: 20261027-194902-55ef95db | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194902-55ef95db.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194902-55ef95db.md`
- hypothesis: Any argument with differing returns: Any vs first match

- 20261027-194902-55ef95db:D1 [reveal_mismatch] line 21 `reveal_type(p(a))`
  - mypy: reveal `Any`
  - ty: reveal `Unknown`
  - pyright: reveal `Unknown`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194902-55ef95db:D2 [reveal_mismatch] line 23 `reveal_type(q(a, a))`
  - mypy: reveal `Any`
  - ty: reveal `Unknown`
  - pyright: reveal `Unknown`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/overloads/genD_generic_overload_04.py`
- case: 20261027-194903-63b651c4 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194903-63b651c4.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194903-63b651c4.md`
- hypothesis: generic overloads with Sequence/Iterable overlap; default-argument overload

- 20261027-194903-63b651c4:D1 [only_mypy] line 32 `reveal_type(get({"a": 1}, "a", "s"))`
  - mypy: [misc] Cannot infer value of type parameter "T" of "get"
  - ty: (nothing)
  - pyright: reveal `int`; [reportArgumentType] Argument of type "Literal['s']" cannot be assigned to parameter "default" of type "T@get" in function "get"
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194903-63b651c4:D2 [reveal_mismatch] line 32 `reveal_type(get({"a": 1}, "a", "s"))`
  - mypy: reveal `Any`
  - ty: reveal `Unknown | Literal["s"]`
  - pyright: reveal `int`; [reportArgumentType] Argument of type "Literal['s']" cannot be assigned to parameter "default" of type "T@get" in function "get"
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/overloads/genD_overlap_incompatible_return_05.py`
- case: 20261027-194906-7fff55c3 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194906-7fff55c3.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194906-7fff55c3.md`
- hypothesis: overlapping overloads with incompatible returns (bool/int, object/str)

- 20261027-194906-7fff55c3:D1 [only_mypy] line 7 `def f(x: bool) -> str: ...`
  - mypy: [overload-cannot-match] Overloaded function signature 2 will never be matched: signature 1's parameter type(s) are the same or broader
  - ty: (nothing)
  - pyright: [reportOverlappingOverload] Overload 2 for "f" will never be used because its parameters overlap overload 1
  - KB hints: TY-CHECK-MISSING-JUDGE-MYPY | decided_by: gate | symptom: None

- 20261027-194906-7fff55c3:D2 [only_mypy] line 15 `def g(x: str) -> str: ...`
  - mypy: [overload-cannot-match] Overloaded function signature 2 will never be matched: signature 1's parameter type(s) are the same or broader
  - ty: (nothing)
  - pyright: [reportOverlappingOverload] Overload 2 for "g" will never be used because its parameters overlap overload 1
  - KB hints: TY-CHECK-MISSING-JUDGE-MYPY | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/overloads/genD_union_literal_overlap_03.py`
- case: 20261027-194909-9d395167 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194909-9d395167.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194909-9d395167.md`
- hypothesis: Literal overlap with str fallback; unions of Literals

- 20261027-194909-9d395167:D1 [only_mypy] line 5 `def m(x: Literal["a"]) -> int: ...`
  - mypy: [overload-overlap] Overloaded function signatures 1 and 3 overlap with incompatible return types
  - ty: (nothing)
  - pyright: [reportOverlappingOverload] Overload 1 for "m" overlaps overload 3 and returns an incompatible type
  - KB hints: TY-CHECK-MISSING-JUDGE-MYPY | decided_by: gate | symptom: None

- 20261027-194909-9d395167:D2 [only_mypy] line 7 `def m(x: Literal["b", "c"]) -> bytes: ...`
  - mypy: [overload-overlap] Overloaded function signatures 2 and 3 overlap with incompatible return types
  - ty: (nothing)
  - KB hints: TY-CHECK-MISSING-JUDGE-MYPY | decided_by: gate | symptom: None

### paramspec_concatenate (7 items)

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/paramspec_concatenate/genB_paramspec_lambda_pass_09.py`
- case: 20261027-194913-e4300495 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194913-e4300495.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194913-e4300495.md`
- hypothesis: lambda with default through ParamSpec identity

- 20261027-194913-e4300495:D1 [reveal_mismatch] line 10 `reveal_type(g)`
  - mypy: reveal `def (x: Any, y: Any =) -> Any`
  - ty: reveal `(x: UnspecializedTypeVar, y: UnspecializedTypeVar = 2) -> Unknown`
  - pyright: reveal `(x: Unknown, y: int = 2) -> Unknown`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/paramspec_concatenate/genB_concat_decorator_inject_01.py`
- case: 20261027-202453-2f7c80a4 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-202453-2f7c80a4.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-202453-2f7c80a4.md`
- hypothesis: Concatenate injection drops first param; kw-only remainder

- 20261027-202453-2f7c80a4:D1 [only_mypy] line 25 `greet(Ctx(), "x")  # error (never executed)`
  - mypy: [call-arg] Too many positional arguments for "greet"; [arg-type] Argument 1 to "greet" has incompatible type "Ctx"; expected "str"; [arg-type] Argument 2 to "greet" has incompatible type "str"; expected "int"
  - ty: (nothing)
  - pyright: [reportCallIssue] Expected 1 positional argument
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/paramspec_concatenate/genB_paramspec_add_param_03.py`
- case: 20261027-202455-7ace9a83 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-202455-7ace9a83.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-202455-7ace9a83.md`
- hypothesis: wrapper prepends positional-only bool via Concatenate return

- 20261027-202455-7ace9a83:D1 [only_mypy] line 21 `area(3)  # error: flag missing / bool expected (never executed)`
  - mypy: [call-arg] Missing positional argument "w" in call to "area"; [arg-type] Argument 1 to "area" has incompatible type "int"; expected "bool"
  - ty: (nothing)
  - pyright: [reportCallIssue] Argument missing for parameter "w"
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/paramspec_concatenate/genB_paramspec_class_generic_07.py`
- case: 20261027-202457-24242682 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-202457-24242682.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-202457-24242682.md`
- hypothesis: generic class Task[**P, R] with `__call__`/method using P.args

- 20261027-202457-24242682:D1 [only_mypy] line 27 `t.run_twice("bad")  # error (never executed)`
  - mypy: [arg-type] Argument 1 to "run_twice" of "Task" has incompatible type "str"; expected "int"
  - ty: (nothing)
  - pyright: [reportArgumentType] Argument of type "Literal['bad']" cannot be assigned to parameter "a" of type "int" in function "run_twice"
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-202457-24242682:D2 [reveal_mismatch] line 22 `reveal_type(t)`
  - mypy: reveal `case.Task[[a: int, b: str =], str]`
  - ty: reveal `Task[(a: int, b: str = "z"), str]`
  - pyright: reveal `Task[(a: int, b: str = "z"), str]`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/paramspec_concatenate/genB_paramspec_kwonly_remainder_10.py`
- case: 20261027-202459-0415729d | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-202459-0415729d.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-202459-0415729d.md`
- hypothesis: remainder after Concatenate is keyword-only; positional call errors

- 20261027-202459-0415729d:D1 [only_mypy] line 21 `fn("k")  # error: keyword-only (never executed)`
  - mypy: [call-arg] Too many positional arguments for "fn"
  - ty: (nothing)
  - pyright: [reportCallIssue] Expected 0 positional arguments
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/paramspec_concatenate/genB_paramspec_method_decorator_04.py`
- case: 20261027-202500-cbaf33bb | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-202500-cbaf33bb.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-202500-cbaf33bb.md`
- hypothesis: Concatenate[S, P] on methods preserves self binding

- 20261027-202500-cbaf33bb:D1 [only_mypy] line 27 `a.add("x")  # error (never executed)`
  - mypy: [arg-type] Argument 1 to "add" of "Acc" has incompatible type "str"; expected "int"
  - ty: (nothing)
  - pyright: [reportArgumentType] Argument of type "Literal['x']" cannot be assigned to parameter "n" of type "int"
  - KB hints: - | decided_by: gate | symptom: None

### protocols (6 items)

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/protocols/genC_proto_class_object_callable_04.py`
- case: 20261027-194916-fc91b39d | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194916-fc91b39d.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194916-fc91b39d.md`
- hypothesis: Class object (type[C]) passed where protocol with __call__ or classmethod is expected

- 20261027-194916-fc91b39d:D1 [reveal_mismatch] line 41 `reveal_type(Widget.make)`
  - mypy: reveal `def (x: int) -> case.Widget`
  - ty: reveal `bound method <class 'Widget'>.make(x: int) -> Widget`
  - pyright: reveal `(x: int) -> Widget`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/protocols/genC_proto_method_vs_callable_attr_07.py`
- case: 20261027-194919-d2272171 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194919-d2272171.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194919-d2272171.md`
- hypothesis: Protocol method satisfied by instance Callable attribute / staticmethod / bound lambda

- 20261027-194919-d2272171:D1 [only_ty] line 27 `print(run(ViaAttr()))`
  - mypy: (nothing)
  - ty: [invalid-argument-type] Argument to function `run` is incorrect: Expected `Op`, found `ViaAttr`
  - pyright: [reportArgumentType] Argument of type "ViaAttr" cannot be assigned to parameter "o" of type "Op" in function "run"
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194919-d2272171:D2 [only_ty] line 30 `print(run(ViaClassAttr()))`
  - mypy: (nothing)
  - ty: [invalid-argument-type] Argument to function `run` is incorrect: Expected `Op`, found `ViaClassAttr`
  - pyright: [reportArgumentType] Argument of type "ViaClassAttr" cannot be assigned to parameter "o" of type "Op" in function "run"
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194919-d2272171:D3 [only_ty] line 33 `reveal_type(run(ViaAttr()))`
  - mypy: (nothing)
  - ty: [invalid-argument-type] Argument to function `run` is incorrect: Expected `Op`, found `ViaAttr`
  - pyright: reveal `int`; [reportArgumentType] Argument of type "ViaAttr" cannot be assigned to parameter "o" of type "Op" in function "run"
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/protocols/genC_proto_runtime_isinstance_05.py`
- case: 20261027-194925-f8dee053 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194925-f8dee053.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194925-f8dee053.md`
- hypothesis: runtime_checkable protocol with data member: isinstance narrowing and else branch

- 20261027-194925-f8dee053:D1 [reveal_mismatch] line 25 `reveal_type(x)`
  - mypy: reveal `case.Box`
  - ty: reveal `Box | (NoGrow & Sized2) | (int & Sized2)`
  - pyright: reveal `Box`
  - KB hints: TY-GRADUAL-GENERIC-NARROWING | decided_by: gate | symptom: None

- 20261027-194925-f8dee053:D2 [reveal_mismatch] line 28 `reveal_type(x)`
  - mypy: reveal `case.NoGrow | int`
  - ty: reveal `(NoGrow & ~Sized2) | (int & ~Sized2)`
  - pyright: reveal `NoGrow | int`
  - KB hints: - | decided_by: gate | symptom: None

### tuples_unpacking (7 items)

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/tuples_unpacking/genA_slice_variadic_04.py`
- case: 20261027-194929-2db6c3e6 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194929-2db6c3e6.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194929-2db6c3e6.md`
- hypothesis: indexing/slicing of mixed variadic tuples handled differently.

- 20261027-194929-2db6c3e6:D1 [only_mypy] line 7 `reveal_type(t[:2])`
  - mypy: [misc] Ambiguous slice of a variadic tuple
  - ty: (nothing)
  - pyright: reveal `tuple[int | str | bytes, ...]`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194929-2db6c3e6:D2 [reveal_mismatch] line 7 `reveal_type(t[:2])`
  - mypy: reveal `Any`
  - ty: reveal `tuple[int, str | bytes]`
  - pyright: reveal `tuple[int | str | bytes, ...]`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/tuples_unpacking/genA_star_unpack_variadic_02.py`
- case: 20261027-194931-6bad5d38 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194931-6bad5d38.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194931-6bad5d38.md`
- hypothesis: star-unpack of tuple[int, *tuple[str, ...], float] and fixed 3-unpack may differ.

- 20261027-194931-6bad5d38:D1 [only_mypy] line 8 `x, y, w = t`
  - mypy: [misc] Variadic tuple unpacking requires a star target
  - ty: (nothing)
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194931-6bad5d38:D2 [reveal_mismatch] line 9 `reveal_type(y)`
  - mypy: reveal `Any`
  - ty: reveal `str`
  - pyright: reveal `str`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/tuples_unpacking/genA_tuple_concat_mul_07.py`
- case: 20261027-194933-a206b9d4 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194933-a206b9d4.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194933-a206b9d4.md`
- hypothesis: tuple + and * result precision for fixed/variadic may differ.

- 20261027-194933-a206b9d4:D1 [reveal_mismatch] line 5 `reveal_type(a + b)`
  - mypy: reveal `tuple[int | str | float, ...]`
  - ty: reveal `tuple[int, str, *tuple[float, ...]]`
  - pyright: reveal `tuple[int, str, *tuple[float, ...]]`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194933-a206b9d4:D2 [reveal_mismatch] line 6 `reveal_type(b + a)`
  - mypy: reveal `tuple[object, ...]`
  - ty: reveal `tuple[*tuple[float, ...], int, str]`
  - pyright: reveal `tuple[*tuple[float, ...], int, str]`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194933-a206b9d4:D3 [reveal_mismatch] line 7 `reveal_type(a * 2)`
  - mypy: reveal `tuple[int, str, int, str]`
  - ty: reveal `tuple[int | str, ...]`
  - pyright: reveal `tuple[int | str, ...]`
  - KB hints: - | decided_by: gate | symptom: None

### typeddict (17 items)

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/typeddict/genA_readonly_override_03.py`
- case: 20261027-194942-40b2a3a0 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194942-40b2a3a0.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194942-40b2a3a0.md`
- hypothesis: ReadOnly mutation via update/setdefault/pop/del reporting differs.

- * 20261027-194942-40b2a3a0:D1 [reveal_mismatch] line 28 `reveal_type(s["name"])`
  - mypy: reveal `str`
  - ty: reveal `Literal["n"]`
  - pyright: reveal `str`
  - KB hints: LITERAL-WIDENING | decided_by: gate | symptom: None
  - strong evidence: runtime value "'x'" of type builtins.str does NOT inhabit ty's revealed type Literal["n"]
  - strong evidence: KB:LITERAL-WIDENING would explain this, but runtime value "'x'" (builtins.str) is outside ty's type Literal["n"]

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/typeddict/genA_extra_items_04.py`
- case: 20261027-194936-b05cf679 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194936-b05cf679.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194936-b05cf679.md`
- hypothesis: PEP 728 extra_items support: mypy vs ty differing acceptance.

- 20261027-194936-b05cf679:D1 [only_mypy] line 6 `class Movie(TypedDict, extra_items=int):`
  - mypy: [call-arg] Unexpected keyword argument "extra_items" for "__init_subclass__" of "TypedDict"
  - ty: (nothing)
  - pyright: [reportGeneralTypeIssues] TypedDict does not support __init_subclass__ parameter "extra_items"
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194936-b05cf679:D2 [only_mypy] line 11 `m: Movie = {"name": "x", "rating": 5}`
  - mypy: [typeddict-unknown-key] Extra key "rating" for TypedDict "Movie"
  - ty: (nothing)
  - pyright: [reportAssignmentType] Type "dict[str, str | int]" is not assignable to declared type "Movie"
  - KB hints: ERROR-CASCADE | decided_by: gate | symptom: None

- 20261027-194936-b05cf679:D3 [only_mypy] line 13 `reveal_type(m["rating"])`
  - mypy: [typeddict-item] TypedDict "Movie" has no key "rating"
  - ty: (nothing)
  - pyright: [reportGeneralTypeIssues] Could not access item in TypedDict; reveal `Unknown`
  - KB hints: ERROR-CASCADE | decided_by: gate | symptom: None

- 20261027-194936-b05cf679:D4 [concern_mismatch] line 14 `bad: Movie = {"name": "y", "rating": "no"}`
  - mypy: [typeddict-unknown-key] Extra key "rating" for TypedDict "Movie"
  - ty: [invalid-argument-type] Invalid argument to key "rating" with declared type `int` on TypedDict `Movie`: value of type `Literal["no"]`
  - pyright: [reportAssignmentType] Type "dict[str, str]" is not assignable to declared type "Movie"
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194936-b05cf679:D6 [reveal_mismatch] line 13 `reveal_type(m["rating"])`
  - mypy: reveal `Any`
  - ty: reveal `Literal[5]`
  - pyright: [reportGeneralTypeIssues] Could not access item in TypedDict; reveal `Unknown`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/typeddict/genA_generic_functional_07.py`
- case: 20261027-194938-5fa9e895 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194938-5fa9e895.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194938-5fa9e895.md`
- hypothesis: generic TypedDict inference and functional syntax with keyword key.

- 20261027-194938-5fa9e895:D1 [reveal_mismatch] line 22 `reveal_type(first(r))`
  - mypy: reveal `int`
  - ty: reveal `Unknown`
  - pyright: reveal `int`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194938-5fa9e895:D4 [reveal_mismatch] line 26 `reveal_type(first({"data": "s", "errors": []}))`
  - mypy: reveal `str`
  - ty: reveal `Unknown`
  - pyright: reveal `str`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/typeddict/genA_in_narrowing_02.py`
- case: 20261027-194939-2dd30a87 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194939-2dd30a87.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194939-2dd30a87.md`
- hypothesis: `in` narrowing on union of TypedDicts and discriminant narrowing may differ (mypy weaker).

- 20261027-194939-2dd30a87:D1 [only_mypy] line 24 `reveal_type(v["z"])`
  - mypy: [typeddict-item] TypedDict "A" has no key "z"
  - ty: (nothing)
  - pyright: reveal `int`
  - KB hints: TY-STRICT-EQUALITY | decided_by: gate | symptom: None

- 20261027-194939-2dd30a87:D2 [reveal_mismatch] line 19 `reveal_type(v)`
  - mypy: reveal `TypedDict(case.A, {'kind': Literal['a'], 'x': int})`
  - ty: reveal `A`
  - pyright: reveal `A`
  - KB hints: TY-STRICT-EQUALITY | decided_by: gate | symptom: None

- 20261027-194939-2dd30a87:D3 [reveal_mismatch] line 21 `reveal_type(v)`
  - mypy: reveal `TypedDict(case.B, {'kind': Literal['b'], 'y': str, 'z'?: int})`
  - ty: reveal `B`
  - pyright: reveal `B`
  - KB hints: TY-STRICT-EQUALITY | decided_by: gate | symptom: None

- 20261027-194939-2dd30a87:D4 [reveal_mismatch] line 23 `reveal_type(v)`
  - mypy: reveal `TypedDict(case.A, {'kind': Literal['a'], 'x': int}) | TypedDict(case.B, {'kind': Literal['b'], 'y': str, 'z'?: int})`
  - ty: reveal `(A & <TypedDict with items 'z'>) | B`
  - pyright: reveal `B`
  - KB hints: TY-STRICT-EQUALITY | decided_by: gate | symptom: None

- 20261027-194939-2dd30a87:D5 [reveal_mismatch] line 24 `reveal_type(v["z"])`
  - mypy: reveal `Any | int`
  - ty: reveal `object`
  - pyright: reveal `int`
  - KB hints: TY-STRICT-EQUALITY | decided_by: gate | symptom: None

- 20261027-194939-2dd30a87:D6 [reveal_mismatch] line 26 `reveal_type(v)`
  - mypy: reveal `TypedDict(case.A, {'kind': Literal['a'], 'x': int}) | TypedDict(case.B, {'kind': Literal['b'], 'y': str, 'z'?: int})`
  - ty: reveal `A | (B & <TypedDict with items 'x'>)`
  - pyright: reveal `A`
  - KB hints: TY-STRICT-EQUALITY | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/typeddict/genA_key_ops_08.py`
- case: 20261027-194941-85f73894 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194941-85f73894.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194941-85f73894.md`
- hypothesis: non-literal key indexing, `

- 20261027-194941-85f73894:D3 [reveal_mismatch] line 16 `reveal_type(t | {"a": 2})`
  - mypy: reveal `TypedDict(case.T, {'a': int, 'b': str, 'c'?: bytes})`
  - ty: reveal `T`
  - pyright: reveal `dict[str, object]`
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-194941-85f73894:D4 [reveal_mismatch] line 19 `reveal_type(t.copy())`
  - mypy: reveal `TypedDict(case.T, {'a': int, 'b': str, 'c'?: bytes})`
  - ty: reveal `T`
  - pyright: reveal `T`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/typeddict/genA_unpack_kwargs_06.py`
- case: 20261027-194945-8418bc65 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194945-8418bc65.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194945-8418bc65.md`
- hypothesis: Unpack[TypedDict] with inherited Required/NotRequired and **o call forwarding.

- 20261027-194945-8418bc65:D2 [reveal_mismatch] line 16 `reveal_type(kw)`
  - mypy: reveal `TypedDict(case.Opts2, {'verbose'?: bool, 'level': int, 'name'?: str})`
  - ty: reveal `Opts2`
  - pyright: reveal `Opts2`
  - KB hints: - | decided_by: gate | symptom: None

### typevartuple_unpack (8 items)

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/typevartuple_unpack/genB_tvt_two_tuples_concat_06.py`
- case: 20261027-194951-e477e717 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194951-e477e717.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194951-e477e717.md`
- hypothesis: two TypeVarTuples concatenated in return

- * 20261027-194951-e477e717:D1 [only_mypy] line 5 `return (*a, *b)`
  - mypy: [return-value] Incompatible return value type (got "tuple[object, ...]", expected "tuple[*A]")
  - ty: (nothing)
  - KB hints: - | decided_by: gate | symptom: None
  - strong evidence: operand `a`: runtime type builtins.tuple is outside mypy's inferred type tuple[*A]
  - strong evidence: operand `a`: runtime type builtins.tuple is outside ty's inferred type tuple[*A@cat]

- * 20261027-194951-e477e717:D2 [reveal_mismatch] line 8 `reveal_type(cat((1, "a"), (2.0,)))`
  - mypy: reveal `tuple[Literal[1]?, Literal['a']?]`
  - ty: reveal `tuple[object, ...]`
  - pyright: reveal `tuple[int, str, float]`
  - KB hints: - | decided_by: gate | symptom: None
  - strong evidence: runtime value "(1, 'a', 2.0)" of type builtins.tuple does NOT inhabit mypy's revealed type tuple[Literal[1], Literal["a"]]

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/typevartuple_unpack/genB_tvt_unbounded_tuple_04.py`
- case: 20261027-194952-e7e24cc6 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194952-e7e24cc6.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194952-e7e24cc6.md`
- hypothesis: TypeVarTuple matched against `tuple[int, ...]` and `tuple[int, *tuple[str, ...]]`

- * 20261027-194952-e7e24cc6:D1 [reveal_mismatch] line 14 `reveal_type(ident(x))`
  - mypy: reveal `tuple[int, *tuple[str, ...]]`
  - ty: reveal `tuple[Literal[1], Literal["a"], Literal["b"]]`
  - pyright: reveal `tuple[int, str, str]`
  - KB hints: - | decided_by: gate | symptom: None
  - strong evidence: runtime value "(1, 'a', 'b')" of type builtins.tuple does NOT inhabit mypy's revealed type tuple[int, *tuple[str, ...]]

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/typevartuple_unpack/genB_tvt_unpack_alias_07.py`
- case: 20261027-194953-8512cb21 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194953-8512cb21.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194953-8512cb21.md`
- hypothesis: PEP695 alias `Row[*Ts]` specialized with args, `()`, and Unpack of unbounded tuple

- * 20261027-194953-8512cb21:D2 [reveal_mismatch] line 16 `reveal_type(y)`
  - mypy: reveal `tuple[int, *tuple[str, ...]]`
  - ty: reveal `tuple[Literal[1]]`
  - pyright: reveal `tuple[Literal[1]]`
  - KB hints: - | decided_by: gate | symptom: None
  - strong evidence: runtime value '(1,)' of type builtins.tuple does NOT inhabit mypy's revealed type tuple[int, *tuple[str, ...]]

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/typevartuple_unpack/genB_tvt_prefix_suffix_02.py`
- case: 20261027-194950-41904e87 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194950-41904e87.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194950-41904e87.md`
- hypothesis: `tuple[F, *M, L]` with too-short tuple must error

- 20261027-194950-41904e87:D1 [reveal_mismatch] line 8 `reveal_type(first_last((1, "a", 2.0, b"x")))`
  - mypy: reveal `tuple[int, bytes]`
  - ty: reveal `tuple[Literal[1], Literal[b"x"]]`
  - pyright: reveal `tuple[int, bytes]`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/typevartuple_unpack/genB_tvt_two_tuples_concat_06.py`
- case: 20261027-194951-e477e717 | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194951-e477e717.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-194951-e477e717.md`
- hypothesis: two TypeVarTuples concatenated in return

- 20261027-194951-e477e717:D3 [reveal_mismatch] line 9 `reveal_type(cat((), ()))`
  - mypy: reveal `tuple[()]`
  - ty: reveal `tuple[object, ...]`
  - pyright: reveal `tuple[()]`
  - KB hints: - | decided_by: gate | symptom: None

**Program** `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/typevartuple_unpack/genB_tvt_callable_args_05.py`
- case: 20261027-202502-24d3a7be | json: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-202502-24d3a7be.json` | md: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out/20261027-202502-24d3a7be.md`
- hypothesis: `Callable[[*Ts], R]` with matching `*args: *Ts`

- 20261027-202502-24d3a7be:D1 [only_mypy] line 17 `call_with(add, 1, "x")  # error (never executed)`
  - mypy: [arg-type] Argument 1 to "call_with" has incompatible type "Callable[[int, int], int]"; expected "Callable[[int, str], int]"
  - ty: (nothing)
  - pyright: [reportArgumentType] Argument of type "tuple[Literal[1], Literal['x']]" cannot be assigned to parameter "args" of type "Ts@call_with" in function "call_with"
  - KB hints: - | decided_by: gate | symptom: None

- 20261027-202502-24d3a7be:D2 [only_mypy] line 18 `call_with(add, 1)  # error (never executed)`
  - mypy: [arg-type] Argument 1 to "call_with" has incompatible type "Callable[[int, int], int]"; expected "Callable[[int], int]"
  - ty: (nothing)
  - pyright: [reportArgumentType] Argument of type "tuple[Literal[1]]" cannot be assigned to parameter "args" of type "Ts@call_with" in function "call_with"
  - KB hints: - | decided_by: gate | symptom: None

## Crashes

None. Every checker invocation completed.

## Dismissed automatically (not for judging; for audit)

- 20261027-194724-6d82f30e:D1 async_generators (only_ty) DESIGN_DIVERGENCE/kb:SUPPRESSION-SEMANTICS `a = await g.asend(None)  # type: ignore[arg-type]`
- 20261027-194756-705a5b71:D1 dataclasses (reveal_mismatch) DESIGN_DIVERGENCE/kb:PRECISION-RUNTIME-CONSISTENT `reveal_type(v.__slots__)`
- 20261027-194804-07bd650d:D1 descriptors_properties (only_ty) CONFIG_ARTIFACT/kb:MYPY-OPTIONAL-CHECK `v: int = 5  # type: ignore`
- 20261027-194807-208af9db:D2 enums_literals (reveal_unpaired) DESIGN_DIVERGENCE/kb:MYPY-SKIPS-UNREACHABLE `reveal_type(b)`
- 20261027-194810-f2f1b453:D2 enums_literals (reveal_mismatch) DESIGN_DIVERGENCE/kb:LITERAL-WIDENING `reveal_type(K.C.value)`
- 20261027-194813-5e20afcd:D1 enums_literals (reveal_mismatch) DESIGN_DIVERGENCE/kb:LITERAL-WIDENING `reveal_type(Mixed.X == "x")`
- 20261027-194814-c8a4b97b:D1 enums_literals (reveal_mismatch) DESIGN_DIVERGENCE/kb:LITERAL-WIDENING `reveal_type(S.A.value)`
- 20261027-194815-fe3547f5:D1 enums_literals (reveal_unpaired) DESIGN_DIVERGENCE/kb:MYPY-SKIPS-UNREACHABLE `reveal_type(op)`
- 20261027-194815-fe3547f5:D2 enums_literals (reveal_mismatch) DESIGN_DIVERGENCE/kb:LITERAL-WIDENING `reveal_type(s)`
- 20261027-194815-fe3547f5:D3 enums_literals (reveal_mismatch) DESIGN_DIVERGENCE/kb:PRECISION-RUNTIME-CONSISTENT `reveal_type(y)`
- 20261027-194817-0d7e3503:D1 generics_variance (only_mypy) KNOWN_LIMITATION/kb:TY-CHECK-NOT-IMPLEMENTED `t = Stack.make()`
- 20261027-194817-0d7e3503:D2 generics_variance (reveal_mismatch) SPEC_AMBIGUITY/kb:BOTH-GRADUAL `reveal_type(t)`
- 20261027-194831-0dde95ca:D2 inheritance_mro (only_ty) CONFIG_ARTIFACT/kb:MYPY-OPTIONAL-CHECK `value: int  # type: ignore`
- 20261027-194831-0dde95ca:D3 inheritance_mro (only_ty) CONFIG_ARTIFACT/kb:MYPY-OPTIONAL-CHECK `print(sum(s.items))  # type: ignore`
- 20261027-194838-9ebd498c:D2 match_statement (reveal_unpaired) DESIGN_DIVERGENCE/kb:MYPY-SKIPS-UNREACHABLE `reveal_type(c)`
- 20261027-194840-b0b45d0c:D1 match_statement (reveal_unpaired) DESIGN_DIVERGENCE/kb:MYPY-SKIPS-UNREACHABLE `reveal_type(x)`
- 20261027-194842-20a180d2:D2 match_statement (reveal_unpaired) DESIGN_DIVERGENCE/kb:MYPY-SKIPS-UNREACHABLE `reveal_type(x)`
- 20261027-194850-2f3fc472:D4 narrowing_builtin (reveal_mismatch) DESIGN_DIVERGENCE/kb:TY-GRADUAL-GENERIC-NARROWING `reveal_type(x)`
- 20261027-194850-2f3fc472:D5 narrowing_builtin (reveal_unpaired) DESIGN_DIVERGENCE/kb:MYPY-SKIPS-UNREACHABLE `reveal_type(x)`
- 20261027-194858-7f55fffe:D2 narrowing_user (reveal_unpaired) DESIGN_DIVERGENCE/kb:MYPY-SKIPS-UNREACHABLE `reveal_type(x)`
- 20261027-194858-7f55fffe:D3 narrowing_user (reveal_unpaired) DESIGN_DIVERGENCE/kb:MYPY-SKIPS-UNREACHABLE `reveal_type(x)`
- 20261027-194900-2e32ef3d:D2 narrowing_user (reveal_mismatch) DESIGN_DIVERGENCE/kb:PRECISION-RUNTIME-CONSISTENT `reveal_type(x)`
- 20261027-194918-d2b0fdcd:D1 protocols (reveal_mismatch) DESIGN_DIVERGENCE/kb:PRECISION-RUNTIME-CONSISTENT `reveal_type(p2.make())`
- 20261027-194924-1f350f07:D1 protocols (reveal_mismatch) DESIGN_DIVERGENCE/kb:LITERAL-WIDENING `reveal_type(x.name)`
- 20261027-194927-c106c0ac:D1 tuples_unpacking (reveal_mismatch) DESIGN_DIVERGENCE/kb:PRECISION-RUNTIME-CONSISTENT `reveal_type(p._fields)`
- 20261027-194930-4bba23ad:D1 tuples_unpacking (reveal_mismatch) KNOWN_LIMITATION/kb:JOIN-VS-UNION `reveal_type(mid)`
- 20261027-194930-4bba23ad:D2 tuples_unpacking (reveal_mismatch) KNOWN_LIMITATION/kb:JOIN-VS-UNION `reveal_type(head)`
- 20261027-194930-4bba23ad:D3 tuples_unpacking (reveal_mismatch) KNOWN_LIMITATION/kb:JOIN-VS-UNION `reveal_type(rest)`
- 20261027-194936-b05cf679:D5 typeddict (reveal_mismatch) DESIGN_DIVERGENCE/kb:LITERAL-WIDENING `reveal_type(m["name"])`
- 20261027-194938-5fa9e895:D2 typeddict (reveal_mismatch) DESIGN_DIVERGENCE/kb:LITERAL-WIDENING `reveal_type(r["data"])`
- 20261027-194938-5fa9e895:D3 typeddict (reveal_mismatch) DESIGN_DIVERGENCE/kb:LITERAL-WIDENING `reveal_type(f["class"])`
- 20261027-194941-85f73894:D1 typeddict (reveal_mismatch) SPEC_AMBIGUITY/kb:BOTH-GRADUAL `reveal_type(t[k2])`
- 20261027-194941-85f73894:D2 typeddict (reveal_mismatch) DESIGN_DIVERGENCE/kb:PRECISION-RUNTIME-CONSISTENT `reveal_type(t.get(k2))`
- 20261027-194945-8418bc65:D1 typeddict (only_mypy) DESIGN_DIVERGENCE/kb:UPSTREAM-TY-4212 `f(level=1, other=2)`
- 20261027-194950-41904e87:D2 typevartuple_unpack (reveal_mismatch) DESIGN_DIVERGENCE/kb:PRECISION-RUNTIME-CONSISTENT `reveal_type(first_last((1, 2)))`
- 20261027-194953-8512cb21:D1 typevartuple_unpack (reveal_mismatch) DESIGN_DIVERGENCE/kb:PRECISION-RUNTIME-CONSISTENT `reveal_type(x)`
- 20261027-194954-96e41e8a:D1 typevartuple_unpack (reveal_mismatch) KNOWN_LIMITATION/kb:JOIN-VS-UNION `reveal_type(same_shape((1, "a"), (2, "b")))`
- 20261027-194954-96e41e8a:D2 typevartuple_unpack (reveal_mismatch) KNOWN_LIMITATION/kb:JOIN-VS-UNION `reveal_type(same_shape((1, "a"), (2, 3)))  # error or join?`
