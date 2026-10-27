# Judge 2 adjudications: fuzz/llm-run-2026-10-27

Role: LLM judge, branch 2. Input: `.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/disagreements.md`.

## Scope taken

`disagreements.md` has 17 feature-area groups, in file order:
1 async_generators, 2 callables, 3 constructors_metaclasses, 4 dataclasses, 5 descriptors_properties,
6 enums_literals, 7 generics_variance, 8 inheritance_mro, 9 match_statement, 10 narrowing_builtin,
11 narrowing_user, 12 overloads, 13 paramspec_concatenate, 14 protocols, 15 tuples_unpacking,
16 typeddict, 17 typevartuple_unpack.

I took the second half: **groups 10-17, narrowing_builtin through typevartuple_unpack**
(79 discrepancy items across 8 groups, 6 of the 10 "strong evidence" pipeline items).
Branch 1 should have groups 1-9 (17 is odd; I put the split after group 9, so match_statement is
branch 1's. If branch 1 split 8/9, group 9 is unjudged by me and I did not touch it).
I did not touch judge-1.md.

## Method / environment

- CPython 3.13.16, mypy 2.4.0, ty 0.0.84 (also re-ran two repros on ty 0.0.92, current PyPI), pyright 1.1.400.
- Harness (run from a clean dir with no pyproject/ty.toml, files copied to `/tmp/j2w`):
  ```
  .venv/bin/mypy --python-version 3.13 --check-untyped-defs --show-error-codes --no-incremental --no-error-summary F.py
  .venv/bin/ty check --python-version 3.13 --output-format concise F.py
  .venv/bin/pyright --pythonversion 3.13 F.py
  .venv/bin/python F.py
  ```
- Use `--python-version 3.13`. SETUP.md recommends 3.12; with 3.12, `from typing import TypeIs` is unresolved in mypy and ty,
  which makes every narrowing_user case look different for the wrong reason. I re-ran everything on 3.13 (as the pipeline did).
- Weights: runtime crash > tool self-contradiction > spec quote > "pyright agrees". Printed `bound method ...`, `Unknown` vs `Any`,
  `UnspecializedTypeVar`, mypy `X?` literal marks and expanded `TypedDict(...)` text are treated as display, not evidence.
- A TRUE BUG needs at least one verified STRONG item and no intended-behavior defense from the accused tool.

## Ranked TRUE BUG candidates (2)

| rank | tool | symptom | cases | confidence |
|---|---|---|---|---|
| 1 | mypy | A narrowing of an index expression (`xs[0]`, `d["k"]`) survives an assignment to that same index expression, so mypy keeps a stale narrowed type. Runtime crash that mypy does not report | narrowing_user `20261027-194856-5ce43559:D1` | 0.80 |
| 2 | ty | A TypeVar in a generic-TypedDict parameter (`Resp[T]`) is never solved. The call returns `Unknown`, even though ty distinguishes `Resp[int]` from `Resp[str]` elsewhere. Errors mypy and pyright report are silently lost | typeddict `20261027-194938-5fa9e895:D1`, `:D4` | 0.60 |

All other items in scope: 0 TRUE BUG (breakdown at the end).

---

## TRUE BUG 1: mypy keeps a stale narrowing after assigning to the narrowed index expression

Case: `20261027-194856-5ce43559:D1` (`reveal_type(b.items[0])` line 27, narrowing_user/genD_typeis_attribute_target_02.py).

- Verdict: TRUE BUG.
- Faulty tool: mypy 2.4.0. Symptom: after `if is_str(b.items[0]): b.items[0] = 3`, `b.items[0]` is still `str`, so mypy reveals `str` where the value is `int`.
  The same happens with plain `isinstance`, with `is not None`, and for `dict` keys, so it is not TypeIs-specific.
  mypy then misses a real runtime `AttributeError`/`TypeError`.
- Generalised minimal repro (`/tmp/j2w/m2.py`; `m1.py` has the isinstance/dict/member variants):
  ```python
  from typing import reveal_type

  def a(xs: list[int | None]) -> int:
      if xs[0] is not None:
          xs[0] = None
          reveal_type(xs[0])
          return xs[0] + 1  # TypeError at runtime

  def b(d: dict[str, int | None]) -> int:
      if d["k"] is not None:
          d["k"] = None
          return d["k"] + 1  # TypeError at runtime
  ```
- Checker output (3.13 harness):
  ```
  --- mypy
  m2.py:7: note: Revealed type is "int"           # no error on lines 8 or 15
  --- ty
  m2.py:7:21: R: `None`
  m2.py:8:16: error[unsupported-operator] Operator `+` is not supported between objects of type `None` and `Literal[1]`
  m2.py:15:16: error[unsupported-operator] Operator `+` is not supported between objects of type `None` and `Literal[1]`
  --- pyright
  m2.py:7:21 - information: Type of "xs[0]" is "None"
  m2.py:8:16 - error: Operator "+" not supported for types "None" and "Literal[1]" (reportOperatorIssue)
  m2.py:15:16 - error: Operator "+" not supported for types "None" and "Literal[1]" (reportOperatorIssue)
  ```
- Original case (`genD_typeis_attribute_target_02.py`, 3.13): mypy `25: str`, `27: str`; ty and pyright `25: str`, `27: Literal[3]`.
- Runtime:
  ```
  Runtime type is 'int'   # b.items[0] after b.items[0] = 3, program line 27
  m2.py: TypeError unsupported operand type(s) for +: 'NoneType' and 'int'   (both a() and b())
  m1.py: AttributeError: 'int' object has no attribute 'upper'                (items[0].upper() after items[0] = 3; mypy reports nothing)
  ```
- Self-consistency (STRONG): mypy resets the narrowing for member assignment (`b.v = 3` then `reveal_type(b.v)` gives `int`, m1.py line 26)
  but not for index assignment. `del xs[0]` also leaves the stale `str`, while ty resets to `int | str`.
- Source check: mypy `checker.py` ~line 3611 handles an index lvalue with `elif index_lvalue: self.check_indexed_assignment(...)` only.
  The binder-invalidating path is the `RefExpr`/`NameExpr` one. There is no comment or doc defending this, and the mypy docs
  (type_narrowing) do not mention it as a limitation.
- Spec quote: none needed. The typing spec has no index-expression narrowing rules, so this is a soundness bug against mypy's own behaviour for attributes, and it is the only checker that is wrong.
- Duplicate check: `gh search` in python/mypy for "narrowing index assignment", "binder index assignment", "stale narrowing setitem" and variants found no exact issue.
  Nearby, not the same: #7339 and #7905 (narrowing is not applied to index expressions), #9457 (attribute narrowing is not aware of side effects).
  Not in `known_upstream.json`. Needs a play.mypy.dev check on current master before filing.
- Confidence: 0.80. Remaining risk: maintainers may call it a known limitation of index binding.

---

## TRUE BUG 2: ty cannot solve a TypeVar from a generic TypedDict argument (returns `Unknown`)

Cases: `20261027-194938-5fa9e895:D1` (`reveal_type(first(r))` line 22) and `:D4` (`first({"data": "s", "errors": []})` line 26), typeddict/genA_generic_functional_07.py.

- Verdict: TRUE BUG (ty, missing/incorrect TypeVar solving; the consequence is lost type safety, not a false positive).
- Minimal repro (`/tmp/j2w/p3.py`, both old-style and PEP 695 generic TypedDicts):
  ```python
  class Resp(TypedDict, Generic[T]):
      data: T
      errors: list[str]

  def first(r: Resp[T]) -> T: return r["data"]

  def go(a: Resp[int], c: Resp[str]) -> None:
      reveal_type(first(a))   # expected int
      x: int = first(c)       # expected error
      y: str = first(a)       # expected error
  ```
- Checker output:
  ```
  --- mypy
  p3.py:25: note: Revealed type is "int"     p3.py:27: note: ... "str"
  p3.py:29: error: Incompatible types in assignment (expression has type "str", variable has type "int")  [assignment]
  p3.py:30: error: Incompatible types in assignment (expression has type "int", variable has type "str")  [assignment]
  --- ty 0.0.84
  p3.py:25:17: R: `Unknown`     (first2 with PEP 695 Resp2[U]: also `Unknown`; first(c): `Unknown`)
  p3.py:28:17: R: `int`         (a["data"])
  (no diagnostics on lines 29, 30)
  --- pyright
  p3.py:25:17 - information: Type of "first(a)" is "int"
  p3.py:29:14 - error: Type "str" is not assignable to declared type "int" (reportAssignmentType)
  p3.py:30:14 - error: Type "int" is not assignable to declared type "str" (reportAssignmentType)
  ```
- STRONG evidence (self-contradiction), from `/tmp/j2w/p4.py` on ty 0.0.84:
  ```
  p4.py:30:17: R: `Unknown`           # first(a) with a: Resp[int]
  p4.py:31:17: R: `int`               # control: unbox(b: Box[int]) with an ordinary Generic class
  p4.py:32:14: error[invalid-argument-type] ... Expected `Resp[int]`, found `Resp[str]`
  p4.py:33:20: error[invalid-assignment]  Object of type `Resp[str]` is not assignable to `Resp[int]`
  p4.py:40:17: R: `Unknown`           # lst([a]) with list[Resp[T]] -> T
  ```
  ty knows `Resp[int]` and `Resp[str]` differ (assignability), reads `a["data"]` as `int`, and solves TypeVars for ordinary generic classes, but cannot solve `T` from `Resp[T]`.
  The localisation (TypedDict only) suggests the TypedDict specialization is not part of the solver's constraint set.
- Runtime: program runs fine (`{'data': 1, 'errors': []} {'class': 1, 'ok': True}`). The bug is a static loss of precision plus missed errors. No crash.
- Re-ran on current ty 0.0.92 (temporary venv, deleted): `first(a)` is still `Unknown` (p4.py:30, 40, 41), so this is not fixed upstream.
- Spec quote (typeddict, generic TypedDicts): "A generic TypedDict can be created by inheriting from ``Generic`` with a list of type variables ... Or, in Python 3.12 and newer, by using the native syntax for generic classes". Generic functions over such types follow the ordinary solving rules in generics.
  The spec does not say what an unsolved TypeVar should produce, but `Unknown` for a fully specified argument is not a defensible solution.
- Intended-behavior defense: none found. The ty feature tracker (#1889) lists "Inheritance, generic TypedDicts" under TypedDict, and maintainers have treated neighbours as bugs.
- Duplicate check (no exact match, but the same area is active, so this may be merged into an existing issue):
  - astral-sh/ty#4134 (closed) "Missing type inference for generic TypedDict constructors": `C(value=1)` gave `C[Unknown]`. Constructor path, not parameter solving.
  - astral-sh/ty#4803 (open) "Regression in 0.0.90 when inferring a generic TypedDict through a union parameter": `dict[K, Burrow[T]] | Iterable[...]` solves `T` to `Unknown`. A union-parameter path, and the report says 0.0.89 was fine. Ours fails for a plain `Resp[T]` parameter on 0.0.84 and 0.0.92.
  - astral-sh/ty#2190 (closed), #4405 (closed), #4255 (closed): other generic-TypedDict problems.
  Not in `known_upstream.json`. Check play.ty.dev before filing, and consider commenting on #4803 instead of opening a new issue.
- Confidence: 0.60. Reasons for less than 0.8: an open neighbour (#4803) may share the root cause, and the observable result is `Unknown` (gradual), not a wrong type.

---

## Items judged and rejected (per group)

Legend: FP = pipeline FALSE_POSITIVE (generator/oracle/display artifact), SA = SPEC_AMBIGUITY (design divergence, no spec rule), KD = KNOWN_DUPLICATE or known limitation, KL = KNOWN_LIMITATION (missing feature).

### Pipeline-level artifacts worth fixing (affects several rows)

1. Guard `if len("") > 99:` makes the guarded code statically unreachable for ty (it folds `len("")` to `0` and `0 > 99` to false) but not for mypy or pyright. Check on a clean file: with `if len("") > 99: area(3)` ty reports nothing while mypy and pyright report the call error; with a reachable `area(3)` all three agree (`/tmp/j2w/p1.py`: mypy 19/23/28, ty 23/28, pyright 19/23/28).
   The guard that replaced `sys.argv` in 8 genB programs therefore produces fake `only_mypy` items in paramspec_concatenate and typevartuple_unpack (all marked FP below). A guard ty cannot fold is needed, e.g. `if input(): ...`.
2. The runtime-inhabitation oracle ("runtime value X does NOT inhabit mypy's revealed type") mishandles variadic tuples: `(1, 'a', 'b')` and `(1,)` both inhabit `tuple[int, *tuple[str, ...]]`.
   It also fires on ill-typed code (see typeddict readonly). 5 of the 6 strong items in my scope come from this (all rejected below).
3. ty shows several internal spellings in `reveal_type` (`UnspecializedTypeVar`, `float*`, `bound method <class 'X'>.m`). Display-only.

### narrowing_builtin (17 items)

| id | verdict | reason / evidence |
|---|---|---|
| 194847-1a61f79a:D1 `return v()` only_ty | KD | ty reports `invalid-return-type` (found `object`) after `callable(v)` on `str \| Callable[[], str]`. Reproduced with `int \| Callable[[], int]` (`/tmp/j2w/p5.py`: ty errors at lines 6, 12, 22 on both 0.0.84 and 0.0.92; mypy and pyright silent). Defended by ty maintainers: ty#2963 (closed as duplicate of #1578) shows a `class Sneaky(int)` with `__call__` that raises `TypeError` at runtime, and recommends `not isinstance(x, int)`. Runtime of the generated program is fine. Intended, so no bug. Conf 0.9 |
| :D2 :D3 :D4 :D5 reveal_mismatch | SA | Same cause: ty keeps `str & Top[(...) -> object]` intersections instead of dropping the arm. No spec rule for `callable()` narrowing (spec narrowing only covers TypeGuard/TypeIs). Display |
| 194849-4c0967e4:D1 D2 D3 (hasattr) | SA | mypy keeps `A \| B` / `B`; ty narrows to `A \| (B & <Protocol with members 'name'>)`; pyright does not narrow `hasattr` at all and reports `Cannot access attribute "name" for class "B"` at line 15 on code that runs fine (documented pyright choice). No spec rule. Runtime fine. ty#3081/#3753 are hasattr neighbours |
| 194850-2f3fc472:D1 D2 D3 (isinstance Mapping/Sequence) | SA | ty returns `(int & Mapping[Unknown, Unknown]) \| ...` because `int` is non-final (a subclass could be a Mapping). More precise, KB TY-GRADUAL-GENERIC-NARROWING. `reveal_type` at line 20 is `Never` in ty (mypy skips unreachable), correct since `list[int] \| str` are both Sequences |
| 194851-77099533:D1 D2 (isinstance tuple) | FP | `list[Any]` vs `list[Unknown]` is display. D2 `(int & ~bool) \| str` vs `int \| str`: ty is more precise (bool excluded by `and not isinstance(bool)`), runtime-consistent |
| 194852-a2c8adec:D1 D2 D3 D4 (issubclass) | SA | `type[Left \| Right] \| (type[int] & type[Base])` and `type[Base] & ~type[Left] & ~type[Right]` are valid intersections; mypy/pyright drop them. ty more precise |

### narrowing_user (9 items)

| id | verdict | reason / evidence |
|---|---|---|
| 194856-5ce43559:D1 | **TRUE BUG (mypy)**, see above | |
| 194857-bac95359:D1 (TypeIs callable/tuple) | SA | 3.13 re-run: first three reveals agree. Line 23 differs only in how the negative `Callable[[int], int]` complement is shown (`(int & ~...) \| ...` vs mypy `int \| (def (str) -> str)` vs pyright no narrowing) |
| 194858-7f55fffe:D1 (final class) | SA | `F \| (Q & ~P)` vs `F \| Q`. `Q` is not final, so a subclass of Q could also be a P, hence ty's complement is sound. The spec says negative TypeIs narrowing is "A and not R" (narrowing.txt: "should be narrowed to A ∧ ¬R"). mypy/pyright over-approximate; none is wrong at runtime |
| 194859-d8f036df:D1 D3 | SA | Same negative-complement display (`Sequence[int \| str] & ~Sequence[int]`) |
| :D2 line 24 `list[object]` / `list[int]` | SA (note) | mypy solves `T` of `is_list[T](x: Sequence[T]) -> TypeIs[list[T]]` from the union argument to `object`, giving `list[object]`. A repro (`/tmp/j2w/m3.py`) shows this lets `x.append("s")` pollute a caller's `list[int]` (runtime: `[1, 2, 's']` then `TypeError`). mypy and pyright (`list[int \| str]` subclass) both accept it, ty rejects it. The spec does not say how a TypeVar is solved from a union argument or what TypeIs narrowing produces for it, so I do not call it a bug in one tool. With `x: Sequence[int]` alone (`pollute3`), all three catch the append. Worth a note to the caller |
| 194900-2e32ef3d:D1 D3 D4 (method self) | FP | Display of negative intersections and `Any & Circle` vs `Circle` (gradual). Runtime fine |

### overloads (8 items)

| id | verdict | reason / evidence |
|---|---|---|
| 194902-55ef95db:D1 D2 | FP | `Any` vs `Unknown` display for an Any argument matching several overloads |
| 194903-63b651c4:D1 D2 (`get({"a": 1}, "a", "s")`) | SA | mypy "Cannot infer value of type parameter T" (the known mypy outcome for container-literal plus conflicting default), pyright errors on the default, ty accepts with `Unknown \| Literal["s"]`. The spec does not say whether a dict literal can be widened to `dict[str, int \| str]` to satisfy a later argument. Runtime fine (`1 None 4`). Not a wrong type: ty's `Unknown` member is gradual |
| 194906-7fff55c3:D1 D2 (overlap) | KD | ty does not implement overlapping-overload checks: astral-sh/ty#103 "Check for overlapping overloads" (open). mypy `overload-cannot-match`, pyright `reportOverlappingOverload` are optional checks; the spec (overload.txt) requires implementation-consistency checks but not overlap reporting. KB TY-CHECK-MISSING-JUDGE-MYPY |
| 194909-9d395167:D1 D2 (union_literal overlap) | KD | Same, ty#103 |

### paramspec_concatenate (7 items)

| id | verdict | reason / evidence |
|---|---|---|
| 194913-e4300495:D1 (`ident(lambda x, y=2: ...)`) | FP (display) | ty prints `(x: UnspecializedTypeVar, y: UnspecializedTypeVar = 2) -> Unknown`. Behaviour is consistent (`/tmp/j2w/p2.py`: ty reports too-many and missing-argument on the same calls as mypy and pyright, runtime matches). The leaked internal name is cosmetic, so I do not file it. Possible low-priority ty display issue |
| 202453-2f7c80a4:D1, 202455-7ace9a83:D1, 202457-24242682:D1, 202459-0415729d:D1, 202500-cbaf33bb:D1 (all `only_mypy`) | FP | All five error lines are inside `if len("") > 99:`, which ty folds to unreachable (see artifact 1). Checked on a reachable copy: ty reports both `missing-argument` and `invalid-argument-type` for `area(3)` (`p1.py` lines 23, 28). The revealed types before the guard agree in all three tools. KB: ty skipping dead code is the mirror of MYPY-SKIPS-UNREACHABLE |
| 202457-24242682:D2 | FP | `Task[[a: int, b: str =], str]` vs `Task[(a: int, b: str = "z"), str]`: ParamSpec display only |

### protocols (6 items)

| id | verdict | reason / evidence |
|---|---|---|
| 194916-fc91b39d:D1 | FP | `bound method <class 'Widget'>.make(x: int)` vs `def (x: int) -> Widget`: display of a classmethod access; assignability is the same everywhere |
| 194919-d2272171:D1 D2 D3 (only_ty `invalid-argument-type`) | KD / SA | `ViaAttr` has an instance attribute `Callable[[int], int]` for protocol method `apply(self, x: int)`. ty and pyright reject because a `Callable[[int], int]` cannot be called with `x=`; pyright's message says `Missing keyword parameter "x"`. mypy accepts by design: `mypy/subtypes.py:1321` `ignore_names = member != "__call__"  # __call__ can be passed kwargs` (positional names are deliberately ignored for protocol members). Runtime fine for `ViaAttr`. For `ViaClassAttr` (`apply: Callable[[int], int] = lambda x: x - 1` at class level) CPython binds it as a method, so `run(ViaClassAttr())` raises `TypeError` (the program catches it), and ty and pyright reject it correctly while mypy accepts. That is mypy's long-standing treatment of Callable-typed class attributes (not bound like methods), a documented ambiguity (see the mypy "Callable instance variable" discussions), not a ty bug. I could not locate one canonical mypy issue number; treat as known design divergence. Conf 0.7 that mypy considers it intended |
| 194925-f8dee053:D1 D2 (runtime_checkable isinstance) | SA | ty returns `Box \| (NoGrow & Sized2) \| (int & Sized2)` because `NoGrow` and `int` are non-final. KB TY-GRADUAL-GENERIC-NARROWING; runtime fine |

### tuples_unpacking (7 items)

| id | verdict | reason / evidence |
|---|---|---|
| 194929-2db6c3e6:D1 D2 (`t[:2]` on `tuple[int, *tuple[str, ...], bytes]`) | KL | mypy emits `Ambiguous slice of a variadic tuple` ([misc]) and `Any` (explicit unsupported message). ty `tuple[int, str \| bytes]` is exact (at least two elements, first two are int and then str or bytes); pyright `tuple[int \| str \| bytes, ...]` is sound but looser. Runtime `(1, 'a')`. Not a ty bug |
| 194931-6bad5d38:D1 D2 (`x, y, w = t`) | SA | mypy requires a star target: `Variadic tuple unpacking requires a star target` (explicit design message). ty and pyright accept and give `y: str`. Accepting is unsound for other lengths (the program only uses a 3-tuple), but the spec has no rule for unpacking variadic tuples into a fixed target list (tuples.txt only constrains the type forms). Neither is clearly wrong |
| 194933-a206b9d4:D1 D2 D3 (`a + b`, `b + a`, `a * 2`) | SA | Precision trade-off: mypy gives exact `tuple[int, str, int, str]` for `a * 2` but `tuple[int \| str \| float, ...]` and `tuple[object, ...]` for the concatenations; ty and pyright the reverse. All results are sound; the spec has no `+`/`*` rule for tuples beyond typeshed's `__add__`/`__mul__` |

### typeddict (17 items)

| id | verdict | reason / evidence |
|---|---|---|
| 194942-40b2a3a0:D1 (strong: `s["name"]` is `Literal["n"]` in ty, runtime `'x'`) | FP | The oracle result is real but the program is ill-typed: `edit()` assigns to a ReadOnly key (`m["name"] = "x"`, line 18) which all three checkers report (mypy `typeddict-readonly-mutated`, ty `invalid-assignment`, pyright `reportTypedDictNotRequiredAccess`), and `edit(s)` then mutates `s["name"]` at runtime. ty's `Literal["n"]` is what the ReadOnly contract and assignment narrowing of the dict literal give. Spec: ReadOnly items must not be mutated. KB LITERAL-WIDENING would also apply. Conf 0.9 |
| 194936-b05cf679:D1 D2 D3 D4 D6 (`extra_items`) | KL | mypy 2.4 does not support PEP 728 (`Unexpected keyword argument "extra_items" for "__init_subclass__"`), and cascades into D2 D3 D4 D6. ty implements it (`m["rating"]` is `Literal[5]`, `rating: "no"` is rejected with the declared `int`). The typing spec (typeddict.txt) documents `extra_items`, so ty follows the spec. pyright 1.1.400 also lacks it. Runtime fine. ty tracker #1889 lists it under TypedDict as in progress |
| 194938-5fa9e895:D1 D4 | **TRUE BUG (ty)**, see above | |
| 194939-2dd30a87:D1-D6 (`in` narrowing on `A \| B`) | SA | `A` is a non-final TypedDict, so a value of type `A` may carry a key `z` (structural typing). ty keeps `(A & <TypedDict with items 'z'>) \| B` and gives `v["z"]` as `object`, mypy keeps `A \| B` and errors `TypedDict "A" has no key "z"`, pyright drops `A` (unsound for non-final TypedDicts). The spec has no `in`-narrowing rule for non-final TypedDict. Runtime fine. ty#3461 (closed) shows ty deliberately moved to the sound form |
| 194941-85f73894:D3 D4 (`t \| {...}`, `t.copy()`) | FP | `TypedDict(case.T, {...})` vs `T`: mypy prints the expanded form; the type is the same |
| 194945-8418bc65:D2 (`kw` from `Unpack[Opts2]`) | FP | Same display difference (`Opts2`) |

### typevartuple_unpack (8 items)

| id | verdict | reason / evidence |
|---|---|---|
| 194951-e477e717:D1 D2 D3 (`def cat[*A, *B](...) -> tuple[*A, *B]`) | FP (invalid program, error cascade) | The annotation `tuple[*A, *B]` is itself a type error, and all three checkers report it: mypy `More than one variadic Unpack in a type is not allowed`, ty `Multiple unpacked variadic tuples are not allowed in a tuple specialization`, pyright `at most one unpacked TypeVarTuple or tuple`. Spec (tuples.txt): "An unpacked TypeVarTuple counts as an unbounded tuple in the context of this rule" followed by `t6: tuple[*tuple[str, ...], *Ts]  # Type error`. After that, mypy's extra `return-value` error and the three different call results are fallout. The strong-evidence runtime item is also an artifact (the type is invalid). Conf 0.95 |
| 194952-e7e24cc6:D1 (`ident(x)`, `x: tuple[int, *tuple[str, ...]] = (1, "a", "b")`) | FP (oracle) + SA | The runtime value `(1, 'a', 'b')` does inhabit mypy's `tuple[int, *tuple[str, ...]]`, so the "strong" item is an oracle bug (artifact 2). The real difference is assignment narrowing of a declared type: ty and pyright narrow to the assigned tuple (`Literal[1], Literal["a"], Literal["b"]` / `int, str, str`), mypy keeps the declared type. Known (assignment narrowing KB) and not wrong |
| 194953-8512cb21:D2 (`y: tuple[int, Unpack[tuple[str, ...]]] = (1,)`) | FP (oracle) + SA | Same: `(1,)` inhabits mypy's type; ty and pyright narrow to `tuple[Literal[1]]` on assignment |
| 194950-41904e87:D1 (`first_last((1, "a", 2.0, b"x"))`) | SA | `tuple[Literal[1], Literal[b"x"]]` vs `tuple[int, bytes]`: literal retention in TypeVar solving (KB LITERAL-WIDENING). Runtime `(1, b'x')` inhabits both |
| 202502-24d3a7be:D1 D2 (`call_with(add, 1, "x")`) | FP | The error lines sit under `if len("") > 99:` (artifact 1), so ty never checks them. mypy and pyright report both |

---

## Duplicate-check notes (not in `known_upstream.json`)

`typediff/data/known_upstream.json` has TY-1090, TY-4212, TY-2255 and MYPY-9658. None matches the two TRUE BUGs above.
`UPSTREAM-TY-4212` (Unpack[TypedDict] open TypedDict) applies to `unpack_kwargs_06` line 27 (mypy `Unexpected keyword argument "other"`, ty silent), which the pipeline had already dismissed.

## Verdict counts

- Items judged: 79 (8 groups). TRUE BUG: 2 candidates (mypy 1, ty 1), covering 3 items (`194856-5ce43559:D1`, `194938-5fa9e895:D1`, `:D4`).
- Of the 6 strong-evidence items in scope: 1 real (`194856-5ce43559:D1`, mypy stale narrowing); 5 are artifacts: variadic-tuple oracle bug x2 (`194952-e7e24cc6:D1`, `194953-8512cb21:D2`), ReadOnly mutation in an ill-typed program x1 (`194942-40b2a3a0:D1`), invalid `tuple[*A, *B]` annotation x2 (`194951-e477e717:D1`, `:D2`).
- Everything else: FP / SA / KD / KL as shown.
