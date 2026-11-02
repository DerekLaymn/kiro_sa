# crash25 triage: kb-loop round-1 checker crashes

Date of work: 2026-11-01. Read-only: no tracked repo file was modified, nothing was posted or filed. Scratch work is in `/tmp/crash25/` (minimal repros in `/tmp/crash25/min/`, raw run logs `pinned.jsonl`, `newest.jsonl`). One exception to "work in /tmp/crash25": a ruff checkout and `cargo build -p ty` of ruff `23a16fa` (2026-10-31) was started in `/home/micropp/crash25-build/` because `/tmp` is a 6.8 GB tmpfs. That build had not finished when this report was written, so **ty main was NOT tested** (see "Limits").

## 1. Summary answer

* All 25 findings **reproduce 3/3** on the pinned tools in a clean directory with no config. None is flaky. The three "timeouts" I could not prove infinite are exponential-time (ty), and the others are provably unbounded (mypy loop/recursion).
* **5 are already fixed**: ty 0.0.85 (one release after the pinned 0.0.84) fixes rows 1, 11, 12, 13, 18. They are ruff-mdtest regression tests written for a newer ty than the pin.
* **2 are known duplicates**: row 2 = astral-sh/ty#4676 (open, fix PR ruff#29198 open); row 4 = python/mypy#21123 (open, fix PR mypy#22032 open).
* **8 rows (5 distinct signatures) look new** and reportable: 4 mypy signatures (rows 9+19, 17, 21+25) and 2 ty signatures (rows 20; rows 14+15). All still fail on the newest releases (ty 0.0.95, mypy 2.4.1) and on mypy master (uncompiled, `934e703`). Best candidates: the two mypy segfaults (3-line and 2-line repros) and the ty protocol stack overflow (8-line repro).
* **8 rows are pyright** (1.1.414, which is also the newest). Seven are one `RangeError: Maximum call stack size exceeded` family, minimal repro 4 lines. No duplicate found in a keyword search of microsoft/pyright, but that search was weak (see Limits). You asked for ty/mypy, so I list pyright as out of scope and did not write a draft.
* **1 row needs a human** (row 16, mypy hang on a `TypeVarTuple` default alias): probably the same root cause as mypy#21123 but not the same repro.
* **1 row is a false alarm in our pipeline** (row 5, pyright timeout counted twice). 15 of 25 rows were also *mislabelled by our pipeline* (signal deaths and pyright `RangeError` stored as `NEEDS_HUMAN`, confidence 0) even though they are genuine crashes. See section 6.
* Counts: FIXED_IN_NEWER 5, KNOWN_DUPLICATE 2, NEW_REPORTABLE 8 rows (ty 3, mypy 5; 5 signatures) + pyright 8 rows (candidate, unconfirmed), NEEDS_HUMAN 1, FALSE_ALARM 1, FLAKY_ENV 0.

## 2. How the 25 were selected

`scripts/kbloop_stats.py` (`summarize`) counts a "crash finding" as a live finding whose `discrepancy_id` is not in the report's `discrepancies` list (these come from `typediff/rules.py::crash_findings`). I applied the same selection to `runs/round1/out/seed-*.json` and got exactly 25, with the header comment `# origin:` of each program giving its source. Source texts were extracted from the `source` field to `/tmp/crash25/src/NN.py` (NN = row number). Row numbers below follow the sorted file order of `/tmp/crash25/table.txt`.

Note the metric counts findings, not programs or tool/program pairs: row 4, 5, 6 are one program (`ty__pep695_type_aliases__70`) with three findings (mypy timeout, pyright `exitNone`, pyright timeout).

Environment of the original run (from the JSON): mypy 2.4.0 compiled, ty 0.0.84, pyright 1.1.414, Python 3.13. Flags are from `typediff/runners.py` (`ToolConfig`), original timeout 120 s.

## 3. Method

* Pinned: `/tmp/kbloop/venv` (ty 0.0.84, mypy 2.4.0 compiled, pyright 1.1.414). 3 runs per (program, tool), each in a fresh temp dir containing only `case.py`, env without `VIRTUAL_ENV/PYTHONPATH/TY_CONFIG_FILE/MYPYPATH`, `XDG_CONFIG_HOME` pointed at the temp dir, 60 s limit (`/tmp/crash25/repro.py`, results `pinned.jsonl`). Machine load average was 15 to 58 on a 16-core box during runs, because other jobs (including a pyright running since Oct 31 and the kb-loop) were active.
* Newest: `/tmp/crash25/venv-new`: ty 0.0.95, mypy 2.4.1, pyright 1.1.414 (PyPI and npm latest, verified via the PyPI and npm registry APIs). 2 runs each (`newest.jsonl`).
* mypy master: `/tmp/crash25/venv-main`, `mypy 2.5.0+dev.934e703` (commit of 2026-10-30), **uncompiled**. Uncompiled mypy raises `RecursionError` where compiled mypy (mypyc) segfaults, which gave me tracebacks (`/tmp/crash25/min/t/tb2/`). mypyc has no Python recursion limit, so a RecursionError becomes a C stack overflow (this is also stated in python/mypy#16940).
* Hang classification: row is "hang" only if it also timed out in the newest-version run at lower load (load about 15), or if I captured a stack proving an unbounded loop (`PYTHONFAULTHANDLER=1 timeout -s ABRT`, see M-B).
* Minimization: `/tmp/crash25/ddmin.py` (line-based ddmin, predicate = same exit code / timeout / regex), then manual edits. I did not use `typediff/reducer.py`; my own predicate on exit code was simpler.
* Duplicate search: `gh` works (authenticated). I downloaded **all** ty issues (4028, title+body, up to #4863), all 345 ruff issues labelled `ty`, all 12229 mypy issues (up to #22339), and the 859 mypy `crash` issues, then ran regexes over title+body, plus `gh search issues/prs` queries and reading the likely candidates in full (listed per signature). No microsoft/pyright bulk download.

## 4. Summary table (all 25)

Group codes: **TX** = ty fixed in 0.0.85. **TS** = ty #4676 match slowdown. **TA** = ty nested tuple comparison. **TB** = ty protocol stack overflow. **MA** `type X = Meta[X]` (segfault). **MB** `type X = Id[X]` (hang). **MC** Concatenate alias (hang/RecursionError). **MD** TypeVarTuple default alias (hang). **ME** self-referential TypeVar default (segfault). **PR** pyright constructor recursion. Pinned = 3/3 reproduces for every row. "Newest" = ty 0.0.95 / mypy 2.4.1 / pyright 1.1.414.

| # | Program (origin) | Tool | Category (pinned) | Still fails on newest? | Group | Classification (conf) |
|---|---|---|---|---|---|---|
| 1 | narrowing_builtin `ty__narrow__type_guards__45` (ruff mdtest) | ty | hang (>60 s) | No, fixed in 0.0.85 | TX | FIXED_IN_NEWER (0.95) |
| 2 | match_statement `pyright__matchSequence2` (pyright sample) | ty | hang (>60 s) | Yes (hang) | TS | KNOWN_DUPLICATE ty#4676 (0.7) |
| 3 | constructors `ty__call__constructor__24` (mdtest) | pyright | exit 2, RangeError | Yes | PR | pyright candidate (0.5) |
| 4 | recursive_aliases `ty__pep695_type_aliases__70` (mdtest) | mypy | hang (>60 s) | Yes (hang) | MC | KNOWN_DUPLICATE mypy#21123 (0.85) |
| 5 | same program as 4 | pyright | `exitNone` = same timeout as row 6 | n/a | none | FALSE_ALARM (double count, pipeline bug P2) (0.95) |
| 6 | same program as 4 | pyright | hang (>60 s) | Yes | none | pyright NEEDS_HUMAN (not minimized) (0.4) |
| 7 | constructors `ty__call__constructor__15` | pyright | exit 2, RangeError | Yes | PR | pyright candidate |
| 8 | constructors `ty__call__constructor__14` | pyright | exit 2, RangeError | Yes | PR | pyright candidate |
| 9 | gradual_any `ty__call__type__5` | mypy | SIGSEGV (-11) | Yes (-11) | MA | NEW_REPORTABLE (0.7) |
| 10 | constructors `ty__call__constructor__21` | pyright | exit 2, RangeError | Yes | PR | pyright candidate |
| 11 | async_generators `ty__with__async__43` | ty | SIGABRT stack overflow (-6) | No, fixed in 0.0.85 | TX | FIXED_IN_NEWER |
| 12 | gradual_any `ty__annotations__intersection_types__6` | ty | SIGABRT stack overflow (-6) | No, fixed in 0.0.85 | TX | FIXED_IN_NEWER |
| 13 | gradual_any `ty__annotations__union__7` | ty | panic exit 101, `salsa-0.28.5/src/function/execute.rs:751:9` "too many cycle iterations" in `infer_definition_types` | No, fixed in 0.0.85 | TX | FIXED_IN_NEWER |
| 14 | tuples_unpacking `pyright__tupleComparisonResource_deep_nonbool` | ty | hang (>60 s) | Yes | TA | NEW_REPORTABLE (perf) (0.6) |
| 15 | tuples_unpacking `pyright__tupleComparisonResource_repeated_nested_types` | ty | hang (>60 s) | Yes | TA | NEW_REPORTABLE (perf) (0.6) |
| 16 | recursive_aliases `ty__generics__pep695__aliases__17` | mypy | hang (>60 s) | Yes (hang) | MD | NEEDS_HUMAN (likely same family as mypy#21123/#21572) (0.4) |
| 17 | recursive_aliases `ty__pep695_type_aliases__55` | mypy | hang (>60 s) | Yes (hang) | MB | NEW_REPORTABLE (0.65) |
| 18 | narrowing_builtin `ty__narrow__type_guards__46` | ty | hang (>60 s) | No, fixed in 0.0.85 | TX | FIXED_IN_NEWER |
| 19 | gradual_any `ty__call__type__4` | mypy | SIGSEGV (-11) | Yes (-11) | MA | NEW_REPORTABLE (0.7) |
| 20 | protocols `mypy check-protocols testTwoUncomfortablyIncompatibleProtocolsWithoutRunningInIssue9771` | ty | SIGABRT stack overflow (-6) | Yes (-6) | TB | NEW_REPORTABLE (0.6, ty main untested) |
| 21 | recursive_aliases `pyright__typeVarDefaultTypeAlias2` | mypy | SIGSEGV (-11) | Yes (-11) | ME | NEW_REPORTABLE (0.7) |
| 22 | constructors `ty__call__constructor__22` | pyright | exit 2, RangeError | Yes | PR | pyright candidate |
| 23 | constructors `ty__call__constructor__25` | pyright | exit 2, RangeError | Yes | PR | pyright candidate |
| 24 | constructors `ty__call__constructor__16` | pyright | exit 2, RangeError | Yes | PR | pyright candidate |
| 25 | generics_variance `pyright__typeVarDefaultClass2` | mypy | SIGSEGV (-11) | Yes (-11) | ME | NEW_REPORTABLE (0.7) |

Per-row detail: rows 1, 2, 14, 15, 18 (ty, `None` exit) time out at 60 s on every pinned run; row 13 prints `fatal[panic] Panicked at .../salsa-0.28.5/src/function/execute.rs:751:9 when checking case.py: infer_definition_types(Id(405)): execute: too many cycle iterations` with exit 101. Rows 11, 12, 20 print `thread '<unknown>' (N) has overflowed its stack` / `fatal runtime error: stack overflow, aborting`. mypy exit -11 prints nothing (even `--show-traceback`). Pyright prints `An internal error occurred while type checking file ...: RangeError: Maximum call stack size exceeded` plus a JS stack and exits 2 with no JSON.

Validity of the inputs: all programs are stdlib-only (or `typing_extensions`/`ty_extensions`-free, except row 21 which imports `typing_extensions`, installed in the venv). Several are intentionally invalid test fragments: rows 4, 9, 16, 17, 19 (cyclic or diverging aliases that a checker must reject), row 12 (intersection syntax inside a string), rows 3, 7, 22, 23, 24 (recursive `__new__`/`__init__`/`__call__` declarations), rows 14, 15 (resource stress tests from pyright). A checker should still not crash on invalid code, so none of these is excluded.

## 5. Distinct signatures and classification

### 5.1 Fixed in newer ty (TX, rows 1, 11, 12, 13, 18): FIXED_IN_NEWER, conf 0.95
Fresh venvs for ty 0.0.85 to 0.0.86 already pass all five (bisect aborted after 0.0.86 once the pattern was clear; the pinned 0.0.84 fails, 0.0.85 passes; `/tmp/crash25/bisect_ty.txt`). These are ruff mdtest blocks that exist to prevent regressions; ty issues in the same family: #4565, #4608, #4694, #4768, #4863. I did not identify the exact fixing PR for each. Cause for us: the corpus was harvested from ruff main (Oct 31) but ty is pinned at 0.0.84 (Sep 24), see P5.

### 5.2 TS, row 2: KNOWN_DUPLICATE astral-sh/ty#4676 (open), conf 0.7
`match` on a tuple of two unions of plain classes, one pair pattern per case. #4676 ("Slow check for match on a tuple of two class unions") reports steep time and memory growth with the same shape; open PR astral-sh/ruff#29198 ("Preserve tuple shape when pattern expansion exceeds its budget", fixes ty#4676) targets exactly the tuple-pattern expansion that pyright's `matchSequence2.py` stress-tests. My generator `/tmp/crash25/min/ty_match_pairs_n12.py` (n = number of classes) takes 0.35 s at n=4, 0.6 at n=6, 1.3 at n=10, 2.5 s at n=12 on ty 0.0.95, so growth is steep but I did not reproduce the exact 60 s hang with a small n. Uncertainty: row 2 has 16 classes plus `reveal_type` calls and `type` aliases, which differ from #4676's file; I did not run #4676's exact file. Recommendation: do not file; add a comment on #4676 only if you want, with the matchSequence2 file as an extra benchmark.

### 5.3 MC, row 4: KNOWN_DUPLICATE python/mypy#21123 (open), conf 0.85
Minimal repro (`min/mypy_C_concatenate_alias.py`):
```python
from typing import Callable, Concatenate
type RecursiveParamspec[**P] = Callable[[], RecursiveParamspec[Concatenate[int, P]]]
```
mypy 2.4.0 and 2.4.1 (compiled): no output for 40 s (hang). mypy master (uncompiled): `RecursionError` (`has_placeholder` -> `visit_callable_type` -> `visit_type_alias_type` ... `expand_type_list_with_unpack` -> `visit_param_spec`). Issue #21123 is `type A[**P] = Callable[[Callable[P, None]], A[Concatenate[int, P]]]` with `RecursionError`; maintainer reply says to prohibit such aliases like `detect_diverging_alias()`. Open PR python/mypy#22032 "Reject recursive aliases that grow through `Concatenate`" fixes #21123. Row 4 fits this exactly.

### 5.4 MD, row 16: NEEDS_HUMAN, conf 0.4
One line (`min/mypy_D_tvt_default_alias.py`):
```python
type ValidDefault[*Ts = *tuple[ValidDefault[int]]] = tuple[ValidDefault[*Ts, int]]
```
Hangs in compiled 2.4.0/2.4.1 (40 s); `RecursionError` on master (`has_placeholder` -> `visit_type_var_tuple` -> default -> alias expansion). Related, not identical: python/mypy#21125 (closed, "NotImplementedError crash on mutually recursive TypeVarTuple type aliases", fixed by merged PR #21572 "Fix crash on invalid recursive variadic alias", which itself says the non-normalizable-tuple case only avoids "an immediate crash"), #21123/PR #22032 (diverging alias detector), #21269 and #21128 (closed, recursive TypeVar default / bound). Decision needed: file separately or add as a comment on #21123. I did not find an issue with this exact repro.

### 5.5 MA, rows 9 and 19: NEW_REPORTABLE (mypy), conf 0.7
Minimal repro (2 lines, `min/mypy_A_typealias_segfault.py`):
```python
type Meta[T] = type[T]
type X = Meta[X]
```
| mypy | Result |
|---|---|
| 2.4.0 compiled (pinned) | Segmentation fault, exit 139 (-11), 3/3 |
| 2.4.1 compiled (newest) | Segmentation fault |
| master `934e703` uncompiled | `error: INTERNAL ERROR`, `RecursionError: maximum recursion depth exceeded` |

Top frames on master (`--show-traceback`): `semanal.visit_type_alias_stmt` -> `disable_invalid_recursive_aliases` -> `types_utils.is_invalid_recursive_alias` -> `types.get_proper_type` -> `TypeAliasType._expand_once` -> `expandtype.visit_type_type` -> `TypeType.make_normalized` -> `get_proper_type` -> `_expand_once` (repeats about 3270 times). `type X = type[X]` is rejected cleanly (`type[...] can't contain "Type[...]"`), and `type A = A` gives `Cannot resolve name "A" (possible cyclic definition)`, so the expected result here is an error, not a crash.
Duplicate search (all 12229 mypy issues, regex for `type X = Alias[X]`, `type Alias[T] = type[T]`, plus label `crash` list, plus PR search): no match. Closest, all closed and with different repros: #20107 (fixed by PR #20127, `list[OneClass|int]` + `isinstance`), #20227 (segfault with `tuple[Hashable | HashableArg]`), #17236, #17220 (open, `Annotated` recursive alias hang/crash), #16940 (open, self-referential TypeVar bound segfault). It is plausibly "another instance of the unbounded alias expansion class", so the maintainers may treat it as related to #17220/#21123, but it is not a duplicate of any listed issue.

### 5.6 MB, row 17: NEW_REPORTABLE (mypy), conf 0.65
Minimal repro (2 lines, `min/mypy_B_typealias_hang.py`):
```python
type Id[T] = T
type X = Id[X]
```
No output and no exit after 40 to 60 s on 2.4.0, 2.4.1 and master (rc 124 under `timeout`). Not recursion: a faulthandler dump on master after 20 s shows a flat loop with constant stack:
`types._expand_once` (types.py:404) <- `get_proper_type` (3780) <- `types_utils.is_invalid_recursive_alias` (68) <- `semanal.disable_invalid_recursive_aliases` (4492) <- `visit_type_alias_stmt` (5950). `Identity[X]` expands to `X`, which expands to `Identity[X]`, so `get_proper_type` never reaches a proper type. The old-style form `Id: TypeAlias = "T"; X: TypeAlias = "Id[X]"` also hangs (`min/t/e1.py`). Duplicate search: nothing matching; #18505 (closed) is a hang with a different trigger (undefined name plus class-scope `type`). Conf is lower than MA because the issue could be merged into MA by maintainers (same function, same missing check).

### 5.7 ME, rows 21 and 25: NEW_REPORTABLE (mypy), conf 0.7
ddmin reduced row 25 to 3 lines and row 21 to 7 lines; both are the same thing. Minimal repro (`min/mypy_E_typevar_default_self.py`):
```python
from typing import Generic, TypeVar

T = TypeVar("T", default="T")

class C(Generic[T]): ...
```
2.4.0 and 2.4.1 compiled: segfault. Master: `RecursionError`; frames `semanal.analyze_class` -> `semanal_shared.has_placeholder` -> `TypeQuery.visit_type_var` -> `query_types` -> `visit_instance` -> `query_types` -> `visit_type_var` ... (about 13350 frames). `T = TypeVar("T", default="T")` alone passes, and `def f(x: T)` passes; the crash needs the TypeVar as a class type parameter (or a generic alias `list[T]`, as in row 21). This is not valid user code (PEP 696 says a default must not refer to itself), so the expected result is an error. Duplicate search: closest are #16940 (open, `TypeVar("T", bound=Callable[..., "T"])` segfault, same mechanism, bound instead of default), #21269 and #21128 (closed, PEP 695 recursive default or bound: `Must not defer during final iteration` and an iteration-count error), #17716 (closed, default naming the generic itself). No issue with `default="T"` self-reference. I would file it and link #16940.

### 5.8 TA, rows 14 and 15: NEW_REPORTABLE (ty performance hang), conf 0.6
Comparing two nested-tuple values of aliases that double at each level takes time exponential in the depth. Generator `min/ty_TA_nested_tuple_compare.py` (n=20, 22 lines; `tuple[T(i-1), T(i-1)]` for i=1..n, `a < b` on two `T(n)`):

| ty 0.0.95 | n=8 | n=12 | n=16 | n=18 | n=20 |
|---|---|---|---|---|---|
| `a < b` wall time | 0.13 s | 0.24 s | 1.5 s | 5.9 s | 21 s |

Times roughly double per level. `a == b` is also exponential (13.4 s at n=18), `a + b` is not (0.3 s). mypy 2.4.1 handles n=16 in 1.8 s total (not exponential at that size). The original rows use n=32, which would need about 2^32 element comparisons. Even though both operands have identical types, there is no memoization of the comparison.
Honest caveats: rows 14/15 come from pyright's "Resource" samples, which are written as adversarial stress tests, so the ty maintainers may see this as low priority or as intended limits. Duplicate search: no ty issue about nested tuple comparison; related perf issues #1870 (closed, big tuple `+`), #71 (closed), #4676, #3926. Open ruff PRs #29428 ("Reuse completed type operations") and #29410 may change this; I could not test ty main.

### 5.9 TB, row 20: NEW_REPORTABLE (ty stack overflow), conf 0.6
Minimal repro (8 lines, class definitions only, no use sites; `min/ty_TB_protocol_stack_overflow.py`):
```python
from typing import Protocol, TypeVar

T1 = TypeVar("T1", covariant=True)
T2 = TypeVar("T2")

class P1(Protocol[T1]):
    def b(self) -> int: ...
    def a(self, other: "P1[T2]") -> T1: ...

class P2(Protocol[T1]):
    def a(self, other: "P1[T2] | P2[T2]") -> T1: ...
```
`ty check --python-version 3.13 case.py`: `thread '<unknown>' has overflowed its stack` / `fatal runtime error: stack overflow, aborting`, exit 134 (SIGABRT), on ty 0.0.84, 0.0.85, 0.0.86 and 0.0.95. The PEP 695 spelling (`class P1[T1](Protocol)`, `def a[T2]`, `Union[P1[T2], "P2[T2]"]`) also overflows. Removing method `b`, or removing the `P2` union member (`other: "P1[T2]"` only), or both, makes it pass. Release binaries are stripped, so gdb shows only a repeating 15-frame address cycle (infinite recursion, no symbol names). Without `TY_LOG` output (it prints only `Checking file`).
Duplicate search (all 4028 ty issues plus 345 ruff `ty` issues, body regex for `overflowed its stack`, 24 hits): none has this repro. Read in full: #4694 and #4863 (closed, `Stream[Stream[T]]`/`window`/`flatten` generic factory), #4691 and #4099 (open, intersection `A[T & ~A[...]]`), #3015, #1736, #3397/#3398 (closed). The nearest are the recursive-protocol family #4863/#4694, which were fixed after 0.0.84/0.0.93 respectively but this repro still fails on 0.0.95. Risk: the underlying cause may be fixed on ty main (not tested), or may be filed as part of the open protocol-overflow issues; check `cargo build` result before filing.

### 5.10 PR, rows 3, 7, 8, 10, 22, 23, 24 (and rows 5 and 6): pyright
All seven exit-2 rows print `RangeError: Maximum call stack size exceeded`, with frames in `constructors.ts` (`validateConstructorArgs`, lines 133, 176/177, 263, 427/430, 504, 605/606), `typeEvaluator.ts` 4660/4676/11138/11142/11830 and, for row 22, `typeUtils.ts` 2193/1510/2004. Minimal repros (3 to 6 lines; `min/pyright_*.py`), identical on pyright 1.1.414 pinned and newest:
```python
class C:
    __init__: type["C"]
C()
```
```python
class A:
    __new__: type["A"]
A()
```
```python
class Meta(type):
    __call__: type["C"]
class C(metaclass=Meta): ...
C()
```
(Without the `C()` call, pyright is fine.) ty 0.0.95 and mypy 2.4.1 do not crash on these. I searched microsoft/pyright by keywords (`RangeError`, `validateConstructorArgs`, `__call__`/`__new__`/`__init__` recursion) and found only old, closed, unrelated stack-overflow reports (#9283, #6783, #3399 and others); that search was `gh search` keyword-only, so a duplicate could exist. Not verified further because pyright was outside the requested scope. Rows 5 and 6 are the pyright timeout on the row 4 program (recursive aliases); not minimized.

## 6. Pipeline defects found (our crash detection)

All demonstrated with the repo code (`/tmp/crash25/pipeline_demo.txt`, run from the worktree with `/tmp/kbloop/venv/bin/python`).

* **P1. Signal deaths and pyright internal errors are never classed as crashes (15 of 25 rows).** `typediff/parsers.py::_mypy_crash`, `_ty_crash` and `parse_pyright` return `Crash(kind="abnormal_exit")` for exit codes outside the normal set when there are no diagnostics, and `typediff/rules.py::crash_findings` turns every `abnormal_exit` into `Verdict.NEEDS_HUMAN`, `Tier.REVIEW`, `confidence=0.0`, with the comment "could be a config/usage problem". Negative exit codes (-11 SIGSEGV, -6 SIGABRT) cannot be usage errors. Affected: mypy -11 x4 (rows 9, 19, 21, 25), ty -6 x3 (rows 11, 12, 20), pyright 2 x7. Repro: `parse_mypy("", "", -11, "case.py")[1]` -> `[Crash(kind='abnormal_exit', signature='mypy:exit-11')]`; `crash_findings(...)` -> `NEEDS_HUMAN`, 0.0. Fix: treat `exit_code < 0` as a confirmed crash (kind `signal`); for pyright, detect `internal error occurred while type checking` in stderr even when stdout is not JSON (the existing check in `parse_pyright` is only reached after JSON parsing succeeds).
* **P2. Pyright timeout is reported twice (row 5 = FALSE_ALARM).** `parse_pyright` gets stdout empty and stderr `TIMEOUT after 120s` and emits `pyright:exitNone` (`abnormal_exit`); `Runners.check` then appends its own `Crash(..., "timeout", "pyright:timeout")` because `code is None`. mypy and ty do not double-count because their parsers return nothing for `exit_code=None`. Repro: `parse_pyright("", "TIMEOUT after 120s", None, "case.py")` returns one `abnormal_exit` with signature `pyright:exitNone`. Fix: skip the abnormal-exit branch when `exit_code is None`.
* **P3. Excerpt is the tail of the output, so the cause is cut off.** `parse_pyright` stores `(stderr or stdout)[-2000:]`; for a 128-line JS stack the header `RangeError: Maximum call stack size exceeded` is lost (excerpt starts mid-frame: `typeEvaluator.ts:23478:28)\n    at n.timeOperation ...`). Same tail-cut for the `Evidence` (`excerpt[-1500:]`). Fix: keep the first lines plus the last lines.
* **P4. Signatures are too coarse to group.** `mypy:exit-11` covers MA and ME (different bugs), `ty:exit-6` covers TX and TB, `mypy:timeout` covers MB, MC, MD, `ty:timeout` covers TS, TA and TX, `pyright:exit2` covers everything. Result: a signature-based dedup would merge unrelated bugs, and the count 25 hides 11 distinct causes. Fix: for signal deaths and timeouts, add an optional second-stage signature (e.g. run uncompiled mypy or `PYTHONFAULTHANDLER` / `timeout -s ABRT`).
* **P5. Version skew between harvested seeds and the pinned checker.** Rows 1, 11, 12, 13, 18 (5 of 11 ty rows) are ruff mdtests that already pass on ty 0.0.85. The harvest is from ruff main, the pin is 4 weeks older. Fix: before any crash is reported, re-run on the newest release (as done here), or harvest mdtests from the tag matching the pinned ty.
* **P6 (observation, not a defect in logic).** mypyc-compiled mypy segfaults where uncompiled mypy raises `RecursionError`, and some uncompiled recursion appears as a hang when compiled (rows 4 and 16). Compiled mypy loses the traceback; consider running crash candidates once with `--show-traceback` on an uncompiled mypy.
* No false positive from the text `INTERNAL ERROR`/`timeout` appearing inside a diagnostic was found: `_MYPY_INTERNAL` is anchored (`^[^:\n]+: error: INTERNAL ERROR`), and a diagnostic quoting `Literal['INTERNAL ERROR']` yields no crash (checked). The `ty` branch `"internal error" in stderr.lower()` could in principle match stderr text, but no row hit it.

## 7. Ready-to-file issue drafts (NOT filed)

I cannot create play.ty.dev playground links or mypy-play gists. For ty, please paste the code into https://play.ty.dev and add the link; for mypy, add a https://mypy-play.net gist link if you want one. All of the versions below are exactly what I ran. Check ty main (or the playground) first for TB and TA.

### 7.1 mypy: segfault for a type alias that refers to itself through another generic alias (MA)

**Crash Report**
`type X = Meta[X]` where `Meta[T] = type[T]` makes the compiled mypy segfault; the uncompiled one raises RecursionError.

**Traceback** (mypy master `934e703`, uncompiled, `--show-traceback`; compiled gives only `Segmentation fault`)
```
error: INTERNAL ERROR -- Please try using mypy master on GitHub:
RecursionError: maximum recursion depth exceeded
  ... mypy/semanal.py in visit_type_alias_stmt
  ... mypy/semanal.py in disable_invalid_recursive_aliases
  ... mypy/types_utils.py in is_invalid_recursive_alias
  ... mypy/types.py in get_proper_type
  ... mypy/types.py in _expand_once
  ... mypy/expandtype.py in visit_type_type
  ... mypy/types.py in make_normalized
  (get_proper_type -> _expand_once -> visit_type_type -> make_normalized repeats until the limit)
```

**To Reproduce**
```python
type Meta[T] = type[T]
type X = Meta[X]
```
`mypy case.py`

**Expected Behavior**
An error such as `Cannot resolve name "X" (possible cyclic definition)` or `Invalid recursive alias`, as for `type A = A` and `type X = type[X]`.

**Actual Behavior**
`Segmentation fault (core dumped)` (exit 139) with compiled mypy.

**Your Environment**
- mypy 2.4.1 (compiled: yes) and 2.4.0 (compiled: yes): segfault. Master 2.5.0+dev.934e703a861cfa3b0d29f1e87d9cf7d016001618 (compiled: no): RecursionError.
- Command line: `mypy --python-version 3.13 case.py`; no config file.
- Python 3.13.15, Linux (Fedora).
- Related: #17220, #20107, #20227, #21123 (similar alias expansion crashes, different repros).

### 7.2 mypy: infinite loop (hang) for `type X = Id[X]` with `type Id[T] = T` (MB)

**Bug Report**
mypy never terminates.

**To Reproduce**
```python
type Id[T] = T
type X = Id[X]
```
`mypy case.py` (also hangs with `X: TypeAlias = "Id[X]"`.)

**Expected Behavior**
An error such as `Cannot resolve name "X" (possible cyclic definition)`, as for `type A = A`.

**Actual Behavior**
No output, 100% CPU, no exit (timeout 60 s). On mypy master a `faulthandler` dump shows a constant-depth loop: `semanal.visit_type_alias_stmt` -> `disable_invalid_recursive_aliases` -> `types_utils.is_invalid_recursive_alias` (`get_proper_type(target)`) -> `types.get_proper_type` -> `TypeAliasType._expand_once`. `X` expands to `Id[X]`, which expands to `X`, so no proper type is reached.

**Your Environment**
- mypy 2.4.1 (compiled: yes), 2.4.0 (compiled: yes) and master 2.5.0+dev.934e703 (compiled: no) all hang.
- `--python-version 3.13`, no config. Python 3.13.15, Linux.
- Related, not duplicates: #18505 (hang with an undefined name), #21123.

### 7.3 mypy: segfault for a TypeVar whose default is itself (ME)

**Crash Report**
Compiled mypy segfaults on a class parameterised by `TypeVar("T", default="T")`.

**To Reproduce**
```python
from typing import Generic, TypeVar

T = TypeVar("T", default="T")

class C(Generic[T]): ...
```
`mypy case.py`

**Traceback** (master, uncompiled): `RecursionError: maximum recursion depth exceeded`; frames `semanal.analyze_class` -> `semanal_shared.has_placeholder` -> `type_visitor.TypeQuery.visit_type_var` -> `query_types` -> `visit_instance` -> `query_types` -> `visit_type_var` (repeats). Compiled 2.4.x: `Segmentation fault`.

**Expected Behavior**
An error about an invalid or self-referential default.

**Actual Behavior**
Segmentation fault (exit 139) on mypy 2.4.0 and 2.4.1. `T = TypeVar("T", default="T")` alone and `def f(x: T) -> T` do not crash. Same family as #16940 (`bound=Callable[..., "T"]`).

**Your Environment**
- mypy 2.4.1 (compiled: yes); 2.4.0 (compiled: yes); master 2.5.0+dev.934e703 (compiled: no).
- `--python-version 3.13`, no config. Python 3.13.15, Linux.

### 7.4 ty: stack overflow on two protocol definitions (TB) (check ty main/playground first)

**Summary**
`ty check` aborts with a stack overflow on a file that only defines two generic protocols. No call or assignment is needed.

```py
from typing import Protocol, TypeVar

T1 = TypeVar("T1", covariant=True)
T2 = TypeVar("T2")

class P1(Protocol[T1]):
    def b(self) -> int: ...
    def a(self, other: "P1[T2]") -> T1: ...

class P2(Protocol[T1]):
    def a(self, other: "P1[T2] | P2[T2]") -> T1: ...
```
```
$ ty check --python-version 3.13 case.py
thread '<unknown>' (...) has overflowed its stack
fatal runtime error: stack overflow, aborting
```
Exit status 134. It also happens with PEP 695 syntax. Removing `b` from `P1` or the `P1[T2] |` part from `P2.a` makes it pass. Origin: mypy's `check-protocols.test` case `testTwoUncomfortablyIncompatibleProtocolsWithoutRunningInIssue9771`.

**Version**
ty 0.0.95 (also 0.0.84, 0.0.85, 0.0.86). Linux x86_64, installed from PyPI, `uvx ty@0.0.95`. play.ty.dev link: not created (I cannot create one; please add it). Related but different repros: #4863, #4694, #4691, #4099.

### 7.5 ty: exponential time comparing deeply nested tuple types (TA) (perf; maintainers may not want it)

**Summary**
Comparing two values of the same nested tuple type takes time exponential in the nesting depth, even though both operands have the identical type.

Generator for depth N (N=20 takes 21 s, N=32 never finishes):
```py
type T0 = tuple[int]
type T1 = tuple[T0, T0]
type T2 = tuple[T1, T1]
# ... one line per level up to TN = tuple[T(N-1), T(N-1)]
def compare(a: TN, b: TN) -> bool:
    return a < b
```
| depth | 8 | 12 | 16 | 18 | 20 |
|---|---|---|---|---|---|
| ty 0.0.95 `a < b` | 0.13 s | 0.24 s | 1.5 s | 5.9 s | 21 s |

`a == b` is also exponential (13.4 s at depth 18); `a + b` is not. mypy 2.4.1 finishes depth 16 in under 2 s. Origin: pyright test `tupleComparisonResource_repeated_nested_types.py` and `_deep_nonbool.py` (depth 32).

**Version**
ty 0.0.95 and 0.0.84, Linux x86_64. play.ty.dev link: not created. I found no existing issue (nearest: #1870, #71, #4676).

## 8. Limits and uncertainty

* **ty main was not tested.** `cargo build -p ty` of ruff `23a16fa` was still compiling (it needs the pinned Rust 1.99 toolchain download first). Outcome for rows 2, 14, 15, 20 on main is unknown. The open ruff PRs #29198, #29410, #29428 could change them.
* Hangs were tested with 60 s limits, not 120 s, under load. I called them hangs only where they also timed out on the newest tool at lower load (about 15) or where I have a stack proving an unbounded loop (MB). Rows 14, 15 and 2 are exponential, not infinite. MC and MD are "hang" in compiled mypy and RecursionError in uncompiled mypy; I did not capture a stack from the compiled hang.
* Duplicate search for mypy and ty was a bulk regex over every issue body plus keyword searches and reading of the likely candidates; PR search used `gh search prs` keyword queries only. It cannot exclude an issue that describes the same bug with other words or code. Pyright was only keyword searched.
* The corpus pins `pyright` at 1.1.414 and so does the newest PyPI/npm release, so no "fixed in newer" is possible for pyright.
* ty 0.0.85 was identified as the first fixed version only by running 0.0.85 and 0.0.86; I did not read the fixing PRs.

## 9. Recommendations

1. File, after checking ty main/playground: the three mypy issues (7.1 to 7.3) and the ty protocol overflow (7.4). They are short, deterministic, and fail on the newest releases.
2. Comment on mypy#21123 only if you want to add row 16's one-liner; do not file rows 2 or 4 as new issues (ty#4676, mypy#21123).
3. Treat rows 14, 15 (7.5) as optional perf reports.
4. Fix the pipeline: P1 (signals are crashes), P2 (double timeout), P3 (keep the error header), P5 (re-run on newest before reporting). These change how 15 of the 25 findings are labelled, and are independent of any filing decision.
5. Artifacts: minimal repros in `/tmp/crash25/min/`; raw runs `/tmp/crash25/pinned.jsonl`, `/tmp/crash25/newest.jsonl`; issue caches `/tmp/crash25/{ty_issues,ruff_ty_issues,mypy_all}.json`; table `/tmp/crash25/table.txt`.

---
## 10. Pyright follow-up (added 2026-11-01, in progress)

Status: the main report above (sections 1 to 9) is complete for ty/mypy. Pyright items below are partly done. Repros are copied to `.agents/tasks/crash25-repros/` (also `src25/NN.py` = the 25 original programs, `table.txt`).

**Version check (done).** npm `pyright@latest` = 1.1.414 (published 2026-09-09; GitHub release 1.1.414 also 2026-09-09), same as the PyPI wrapper. `npm i pyright@latest` then `pyright --version` prints `pyright 1.1.414`. Pyright `main` has commits up to 2026-10-29, but `constructors.ts` last changed 2026-09-11 (revert a07bbdeae), so main is unlikely to differ here (not run).

**Re-run on npm 1.1.414 (done).** Rows 3, 7, 8, 10, 22, 23, 24 still exit 2 with `An internal error occurred while type checking file ".../case.py": RangeError: Maximum call stack size exceeded` and a 130-line JS stack, no JSON output. Rows 5 and 6 (row 4 program) are a hang, not a RangeError (not minimized).

**Signatures (top frames, source locations):**
| Sig | Rows | Trigger | Frames |
|---|---|---|---|
| PS1 `__new__` declared as `type[...]` | 7, 10, 23, 24 | `class A: __new__: type["A"]` then `A()` | `typeEvaluator.ts:23484`, `constructors.ts:427, 263, 176/177, 133` (validateConstructorArgs -> validateNewAndInitMethods -> validateNewMethod) |
| PS2 metaclass `__call__` declared as `type["C"]` | 3 | `Meta.__call__: type["C"]`, `C()` | `constructors.ts:605/606, 133` (metaclass `__call__` path) |
| PS3 `__init__` declared as `type["C"]` | 22 | `class C: __init__: type["C"]`, `C()` | `typeUtils.ts:1804/1789`, `constructors.ts:504, 333, 93` |
| PS4 decorated `__new__` returning `type[C]` | 8 | `@decorate def __new__(cls)` with `decorate[T](cb: Callable[[T], None]) -> T` | `typeUtils.ts:1497/2004`, `constructors.ts:599, 430, 133` |
All are one root cause family: a constructor method whose declared type is a class that needs the same constructor, so `validateConstructorArgs` recurses without a cycle guard. ty 0.0.95 and mypy 2.4.1 do not crash on these.

**Minimal repros (verified on 1.1.414, all exit 2):** `crash25-repros/p1.py` (`__init__: type["C"]`; `C()`), `p2.py` (`__new__: type["A"]`; `A()`), `p3.py` (metaclass `__call__`), `q8a.py` (decorated `__new__`, 11 lines), `q8c.py` (`C.__new__: "Factory"`, `Factory.__call__: type[C]`), `q8f.py` (two classes). Without the `C()` call, or with only `reveal_type(C.__new__)`, pyright does not crash.

**Duplicate search (done, bulk):** downloaded 7628 microsoft/pyright issues (open and closed, up to #11955) and regex-searched title+body for `Maximum call stack`, `constructors.ts`, `__new__/__init__/__call__ : type[`, recursion+constructor. No issue has this trigger. Read: #4798 (closed, RangeError in expandSubtype/doForEachSubtype, v1.1.298, different frames), #7786 (closed, OOM with datetype library, fixed 1.1.361), #5139, #5154 (older constructors.ts "Debug Failure"). Conclusion: no duplicate found, conf 0.6 that it is new (the body search cannot rule out a differently worded report; PR search not done).

**TODO (in progress / not done):**
- [ ] since-which-version bisect with `pyright@1.1.300 ... 1.1.413` (running, output `/tmp/crash25/pyver.txt`).
- [ ] pyright `main` build (`/home/micropp/crash25-build/pyright`, log `/tmp/crash25/pybuild.log`); not yet checked.
- [ ] ty `main` build (`/tmp/crash25/cargo.log`); not yet checked.
- [ ] pyright issue draft (below is the draft; template `.github/ISSUE_TEMPLATE/bug_report.md` headings: Describe the bug / Code or Screenshots / VS Code extension or command-line).

### Draft pyright issue (NOT filed)
**Describe the bug**
Pyright's command-line tool exits with status 2 and `RangeError: Maximum call stack size exceeded` when a class declares `__new__` (also `__init__`, or a metaclass `__call__`) with a type that refers back to the same class and the class is then instantiated. Expected: a normal diagnostic or no diagnostic, not an internal error. Related minimal cases:

**Code or Screenshots**
```python
class A:
    __new__: type["A"]

A()
```
```python
class C:
    __init__: type["C"]

C()
```
```python
class Meta(type):
    __call__: type["C"]

class C(metaclass=Meta): ...

C()
```
Output (pyright 1.1.414):
```
An internal error occurred while type checking file "case.py": RangeError: Maximum call stack size exceeded
    at ... pyright-internal/src/analyzer/typeEvaluator.ts:23484:36
    at ... pyright-internal/src/analyzer/constructors.ts:427:34   (validateNewMethod)
    at ... constructors.ts:263:31
    at ... constructors.ts:176:36
    at ... constructors.ts:133:29 (validateConstructorArgs)
```
The recursion goes validateConstructorArgs -> validateNewAndInitMethods -> validateNewMethod -> validateArgTypesWithExpectedType -> validateConstructorArgs, with no cycle detection. The same inputs come from ruff's ty mdtests (`call/constructor.md`).

**VS Code extension or command-line**
Command-line, `pyright --pythonversion 3.13 case.py`, pyright 1.1.414 (npm `pyright@latest` and PyPI `pyright==1.1.414`), Node v24.19.0, Linux. A pyright playground link is not included: I cannot create playground links; the reporter should paste the code at https://pyright-play.net and add the link.

## 11. Update: ty main and pyright bisect (2026-11-01)

* **ty main tested** (built `cargo build -p ty` from ruff `23a16fa` 2026-10-31, dev profile with opt-level 1, so absolute times are about 3-5x slower than release; `ty unknown (23a16fa01 2026-10-31)`):
  * TB (row 20, `min/ty_TB_protocol_stack_overflow.py`) and its PEP 695 spelling (`t20a.py`): **still stack overflow, exit 134**. Not fixed on main, so section 7.4 stands (the "check ty main first" condition is satisfied). Conf for NEW_REPORTABLE raised to 0.7. Caveat: a dev build uses larger stack frames, but the overflow is an unbounded recursion (15-frame cycle) also seen in the release 0.0.95.
  * TA (rows 14/15): generator n=16 takes 10.8 s and n=18 31 s on main (release 0.0.95: 1.5 s and 5.9 s), so exponential growth persists.
  * Row 2 (TS): still times out at 90 s on main, consistent with PR ruff#29198 still being open.
  * The 5 TX rows were not re-run on main (already fixed in 0.0.85).
* **pyright bisect**: the three minimal repros (`p1`, `p2`, `p3`) exit 2 with the RangeError on every npm version tried: 1.1.300, 1.1.340, 1.1.380, 1.1.400, 1.1.410, 1.1.413, 1.1.414. So this is long-standing, not a recent regression. Pyright `main` build (`/home/micropp/crash25-build/pyright`) was started but not verified; `constructors.ts` has not changed since 1.1.414 except a revert.
* Everything above is also logged in `crash25-progress.md`. Remaining TODO: pyright main verification (optional).
* **pyright main: NOT tested.** The source build (`npm ci` in `/home/micropp/crash25-build/pyright`, commit 74743ab17 of 2026-10-29) never ran; treat "still fails on pyright main" as unknown. Evidence for it is only that `constructors.ts` has no change after 1.1.414 other than a revert.
* Scratch builds live in `/home/micropp/crash25-build/` (ruff checkout plus `target/`, several GB). Delete when no longer needed.
