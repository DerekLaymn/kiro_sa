# Minimized TRUE BUG candidates (fuzz/llm-run-2026-10-27)

Merged from judge-1.md and judge-2.md. All outputs below were re-run fresh on the minimized files (mypy 2.4.0, ty 0.0.84, pyright 1.1.400, CPython 3.13) in a clean dir (/tmp/mm, no pyproject/ty.toml). Full raw output: re-run the commands in each file header.

Common commands (`F` = reproducer file):
- mypy: `.venv/bin/mypy --python-version 3.13 --check-untyped-defs --show-error-codes --no-incremental F`
- ty: `.venv/bin/ty check --python-version 3.13 --output-format concise F`
- pyright: `.venv/bin/pyright --pythonversion 3.13 F`
- runtime: `.venv/bin/python F`

Dropped: judge-1 #4 (`genD_assert_never_enum_03`, mypy+pyright `case 1` vs `True`, conf 0.35): shared by pyright, plausibly known narrowing limitation, not minimized. The four KNOWN_DUPLICATE items and the judge-2 / judge-1 artefacts (variadic tuple, ReadOnly, `tuple[*A,*B]`) are excluded. No candidate lost its disagreement during minimization.

Duplicate-check status for all: not in `typediff/data/known_upstream.json`; judges' tracker searches found no exact match (details per entry). No fresh upstream search was done in this step.

## Ranking

| rank | conf | file | tool | symptom |
|---|---|---|---|---|
| 1 | 0.85 | bug-02-enums-ty-flag-or-literal-union.py | ty | `F.R \| F.W` on enum.Flag inferred `Literal[F.R, F.W]` |
| 2 | 0.80 | bug-01-narrowing-mypy-stale-index-narrowing.py | mypy | stale narrowing after index assignment |
| 3 | 0.70 | bug-03-generics-mypy-callable-attr-contravariant.py | mypy | PEP 695 variance: mutable Callable attr treated contravariant |
| 4 | 0.60 | bug-05-typeddict-ty-generic-typeddict-typevar-unknown.py | ty | TypeVar not solved from generic TypedDict (Unknown) |
| 5 | 0.40 | bug-04-dataclasses-mypy-initvar-default-class-attr.py | mypy (pyright agrees with mypy) | attr-defined on InitVar-with-default class access |

Note on ordering: judge-1 gave 0.85 to the Flag bug and judge-2 gave 0.80 to the index narrowing bug; I kept those. I lowered InitVar from judge-1's 0.6 to 0.4 because the fresh run shows pyright also rejects it (as "init-only field"), so it is mypy+pyright vs ty, and may be deliberate.

---

## 1. bug-02-enums-ty-flag-or-literal-union.py (ty, 0.85)
Path: findings/2026-10-27-llm-run/bug-02-enums-ty-flag-or-literal-union.py (source case enums_literals/genA_enum_value_types_02, 20261027-194814-c8a4b97b:D2)

mypy:
```
bug-02-enums-ty-flag-or-literal-union.py:18: note: Revealed type is "bug-02-enums-ty-flag-or-literal-union.F"
Success: no issues found in 1 source file
```
ty:
```
bug-02-enums-ty-flag-or-literal-union.py:18:13: info[revealed-type] Revealed type: `Literal[F.R, F.W]`
Found 1 diagnostic
```
pyright: `Type of "a" is "F"`
Runtime: `<F.R|W: 3> False False` (value is neither listed member).

Justification (judge-1): the typing spec, Enum Literal Expansion, says the rule does not apply to enum.Flag subclasses because flags combine arbitrarily. The runtime value is outside ty's reported type, so it is unsound. Consequence: `if a is F.R or a is F.W: ... else:` would be treated as exhaustive.
Duplicate check: not in known_upstream.json; no upstream ty issue found by judge-1. Needs a search of astral-sh/ty before filing.
Confidence: 0.85.

## 2. bug-01-narrowing-mypy-stale-index-narrowing.py (mypy, 0.80)
Path: findings/2026-10-27-llm-run/bug-01-narrowing-mypy-stale-index-narrowing.py (source case narrowing_user/genD_typeis_attribute_target_02, 20261027-194856-5ce43559:D1)

mypy:
```
bug-01-narrowing-mypy-stale-index-narrowing.py:14: note: Revealed type is "int"
Success: no issues found in 1 source file
```
ty:
```
bug-01-narrowing-mypy-stale-index-narrowing.py:14:21: info[revealed-type] Revealed type: `None`
bug-01-narrowing-mypy-stale-index-narrowing.py:15:16: error[unsupported-operator] Operator `+` is not supported between objects of type `None` and `Literal[1]`
Found 2 diagnostics
```
pyright:
```
14:21 - information: Type of "xs[0]" is "None"
15:16 - error: Operator "+" not supported for types "None" and "Literal[1]" (reportOperatorIssue)
```
Runtime: `TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'` at `return xs[0] + 1`.

Justification (judge-2): the spec has no index-narrowing rules; this is a soundness bug. mypy invalidates the narrowing on member assignment but not index assignment (self-inconsistent). Also reproduces with isinstance, dict keys, and `del xs[0]`; not TypeIs-specific.
Duplicate check: judge-2's gh searches in python/mypy found no exact issue. Related but different: #7339, #7905, #9457. Needs a play.mypy.dev check on master.
Confidence: 0.80 (risk: maintainers call it a known limitation).

## 3. bug-03-generics-mypy-callable-attr-contravariant.py (mypy, 0.70)
Path: findings/2026-10-27-llm-run/bug-03-generics-mypy-callable-attr-contravariant.py (source case generics_variance/genB_pep695_callable_attr_variance_04, 20261027-194819-b0b61389:D1)

mypy:
```
Success: no issues found in 1 source file
```
ty:
```
bug-03-generics-mypy-callable-attr-contravariant.py:21:5: error[invalid-argument-type] Argument to function `use` is incorrect: Expected `Handler[int]`, found `Handler[float]`
Found 1 diagnostic
```
pyright:
```
21:5 - error: Argument of type "Handler[float]" cannot be assigned to parameter "h" of type "Handler[int]" in function "use"
  Type parameter "T@Handler" is invariant, but "float" is not the same as "int" (reportArgumentType)
```
Runtime: `AttributeError: 'float' object has no attribute 'bit_length'`.

Justification (judge-1): spec Auto variance infers variance via normal assignability; a mutable attribute is invariant. Control from judge-1: a mutable `T` attribute is invariant in mypy; only the Callable-typed attribute is treated like a method.
Duplicate check: not in known_upstream.json. Related, not the same: python/mypy#14869, #17623. Needs search for "variance inference" + mutable Callable attribute.
Confidence: 0.70 (risk: mypy's Callable-attribute special case may be intended).

## 4. bug-05-typeddict-ty-generic-typeddict-typevar-unknown.py (ty, 0.60)
Path: findings/2026-10-27-llm-run/bug-05-typeddict-ty-generic-typeddict-typevar-unknown.py (source case typeddict/genA_generic_functional_07, 20261027-194938-5fa9e895:D1, D4)

mypy:
```
:23: note: Revealed type is "int"
:24: error: Incompatible types in assignment (expression has type "str", variable has type "int")  [assignment]
:25: error: Incompatible types in assignment (expression has type "int", variable has type "str")  [assignment]
```
ty:
```
bug-05-typeddict-ty-generic-typeddict-typevar-unknown.py:23:17: info[revealed-type] Revealed type: `Unknown`
Found 1 diagnostic
```
pyright: `first(a)` is `int`; errors on lines 24 and 25 (reportAssignmentType), same as mypy.
Runtime: runs without error (the bugs are static-only; no runtime witness).

Justification (judge-2): the TypeVar in `Resp[T]` should be solved from `Resp[int]`; ty returns Unknown, so real errors are silently lost, while ty elsewhere distinguishes Resp[int] from Resp[str]. Also reproduces with PEP 695 TypedDict.
Duplicate check: not in known_upstream.json (TY-1090, TY-4212, TY-2255 do not match). No upstream search yet.
Confidence: 0.60 (ty may treat this as a known unsupported/incomplete feature, and Unknown is gradual so no false positive).

## 5. bug-04-dataclasses-mypy-initvar-default-class-attr.py (mypy, 0.40)
Path: findings/2026-10-27-llm-run/bug-04-dataclasses-mypy-initvar-default-class-attr.py (source case dataclasses/genA_postinit_initvar_07, 20261027-194757-edc14252:D1, D2)

mypy:
```
bug-04-...py:17: error: "type[Sub]" has no attribute "extra"  [attr-defined]
bug-04-...py:17: note: Revealed type is "Any"
bug-04-...py:18: error: "type[Sub]" has no attribute "extra"  [attr-defined]
Found 2 errors in 1 file (checked 1 source file)
```
ty:
```
bug-04-...py:17:13: info[revealed-type] Revealed type: `int`
Found 1 diagnostic
```
pyright: errors on 17 and 18, `"extra" is an init-only field (reportAttributeAccessIssue)`.
Runtime: prints `0` (the default stays a class attribute).

Justification (judge-1): runtime evidence only, with a no-default control that correctly raises AttributeError. No spec quote. Both mypy and pyright reject it, which suggests intended "init-only" semantics rather than a bug; the report would be about a runtime-valid access being rejected.
Duplicate check: not in known_upstream.json; judge-1 did not search mypy's tracker. Not searched here.
Confidence: 0.40 (lowered from 0.6 because pyright agrees with mypy).
