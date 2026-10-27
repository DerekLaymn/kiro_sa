# Differential bug hunt, final review: mypy vs ty (pyright as tie-breaker)

Run: `fuzz/llm-run-2026-10-27`. Reviewer pass on 2026-10-27, all evidence re-run from scratch.
Directory: `findings/2026-10-27-llm-run/`.

## Bottom line

Four of the five candidates are confirmed as real differential bugs, and I found a fifth while re-verifying (entry 3 below). The fifth candidate falls. Two of the five confirmed bugs are not reported upstream as far as I could find.

| rank | conf | reproducer | faulty tool | symptom | upstream status |
|---|---|---|---|---|---|
| 1 | 0.95 | `bug-01-narrowing-mypy-stale-index-narrowing.py` | mypy | stale narrowing after index assignment, misses a runtime `TypeError` | KNOWN: python/mypy#20969 (open) |
| 2 | 0.90 | `bug-02-enums-ty-flag-or-literal-union.py` | ty | `F.R \| F.W` on `enum.Flag` typed `Literal[F.R, F.W]`, runtime value is neither | KNOWN: ty#3765 (closed, "not supported yet"), ty#876 (open) |
| 3 | 0.85 | `bug-06-enums-mypy-flag-is-narrowing-else-unreachable.py` (added by reviewer) | mypy | `is`-narrowing treats `enum.Flag` as exhausted by its members, skips a reachable branch | same root cause as python/mypy#21937 (open) |
| 4 | 0.80 | `bug-03-generics-mypy-callable-attr-contravariant.py` | mypy | PEP 695 variance inference makes a mutable `Callable[[T], None]` attribute contravariant | NOT FOUND upstream |
| 5 | 0.75 | `bug-05-typeddict-ty-generic-typeddict-typevar-unknown.py` | ty | TypeVar never solved from a generic `TypedDict` argument (`Unknown`), real errors lost | NOT FOUND upstream (nearest: ty#4803, different path) |

Not confirmed: `bug-04-dataclasses-mypy-initvar-default-class-attr.py` (known duplicate mypy#19889, and pyright rejects it deliberately, so it is a design divergence).

The two bugs that are new to the trackers, as far as the search shows, are entry 4 (mypy) and entry 5 (ty). Both have a CPython crash that the faulty tool does not predict, and both have the other two checkers on the correct side.

Watch for: entry 3 was found by me and has had no second judge. "Not found upstream" for entries 4 and 5 rests on GitHub issue and PR search only; discuss.python.org, play.ty.dev and mypy-play were not checked. Pyright is 1.1.400, not the newest.

**Verdict**: APPROVED. The report is complete, every claim below was re-run with pasted output, and the duplicate check was done by body-text search. Follow-ups for earlier steps are listed next; none blocks.

<details>
<summary>Issues (8)</summary>

1. **Duplicate search missed exact matches** (confirmed) — `candidates.md` says "no exact match" for bug-01 and bug-04, but python/mypy#20969 and #19889 are the same programs. Correct the notes, and add MYPY-20969, MYPY-19889, MYPY-21937 and TY-3765/TY-876 to `known_upstream.json`.
2. **bug-02 oracle is display text** (confirmed) — `reveal_type` text comparison is weak, and judge-1's "else is unreachable in ty" consequence is not ty-only. Use `reviewer-min/bug-02-ty-flag-or-assert-type.py` as the reproducer.
3. **bug-05 reproducer not minimal, no runtime witness** (confirmed) — drop the second parameter and the `go()` wrapper, and add the crash. `reviewer-min/bug-05-ty-generic-typeddict-crash-witness.py` does this.
4. **bug-06 never judged** (confirmed) — reviewer-found, skeptic pass is mine alone. Have a judge confirm it and record it in `candidates.md`; the generator should cover declared-type `is` exhaustion on `Flag`.
5. **bug-04 should stay out of the confirmed list** (likely) — pyright's "init-only field" message looks deliberate. Comment on mypy#19889 instead of filing.
6. **Novel bugs need a pre-filing check** (possible) — entries 4 and 5 should be re-run on play.ty.dev (main) and mypy-play (master), and discuss.python.org searched, before anything is filed.
7. **Pyright pin differs from the docs** (confirmed) — venv has 1.1.400, DESIGN.md says 1.1.414. Re-run tie-break results on 1.1.414 before citing them in a write-up.
8. **Stray file `-l` in the repo root** (confirmed) — empty and untracked; delete it before committing.

</details>

## Environment and commands

- CPython 3.13.16, mypy 2.4.0 (compiled), ty 0.0.84, pyright 1.1.400, all from `.venv/bin/`. Pyright 1.1.414 exists on PyPI and was not run.
- Cross-checks on the newest releases at review time: ty 0.0.89 and ty 0.0.92 (pinned, run through `uvx`, nothing installed into the project). mypy 2.4.0 is the newest release on PyPI.
- Every file was copied to a clean directory (`/tmp/rv`, no `pyproject.toml`, no `ty.toml`) before checking. These commands are the baseline flags of `typediff/runners.py` minus the display-only flags. `F` is the file:

```
mypy    .venv/bin/mypy --python-version 3.13 --check-untyped-defs --show-error-codes --no-incremental F
ty      .venv/bin/ty check --python-version 3.13 --output-format concise F
pyright .venv/bin/pyright --pythonversion 3.13 F
runtime .venv/bin/python F
```

Pasted ty output has the progress bar removed, pyright paths are shortened to the file name, and `...` inside a file name marks an elided middle.

## How the gate was applied

DESIGN.md section 1 asks for one verified strong evidence item and a skeptic pass that does not argue "intended". I accepted these as strong: a CPython crash the tool did not predict, a tool contradicting its own behaviour on a control, and a verbatim spec quote. "Pyright agrees" counted for nothing on its own. For each bug I played the maintainer and looked for a cited defence in the trackers and in the tool source. FUZZING_PLAN.md section 6 step 5 (duplicates) was done by body-text search, see the end of this file.

---

## CONFIRMED differential bugs

### 1. mypy keeps a stale narrowing after assigning to the same index (conf 0.95, known)

Reproducer: `bug-01-narrowing-mypy-stale-index-narrowing.py`

```python
def a(xs: list[int | None]) -> int:
    if xs[0] is not None:
        xs[0] = None
        reveal_type(xs[0])
        return xs[0] + 1
    return 0
a([1])
```

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
bug-01-narrowing-mypy-stale-index-narrowing.py:14:21 - information: Type of "xs[0]" is "None"
bug-01-narrowing-mypy-stale-index-narrowing.py:15:16 - error: Operator "+" not supported for types "None" and "Literal[1]" (reportOperatorIssue)
```
CPython:
```
TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'      (line 15, return xs[0] + 1)
```

Verdict: mypy is faulty, symptom FALSE_NEGATIVE. ty 0.0.92 gives the same output as ty 0.0.84.

Justification: the typing spec has no index-narrowing rule, so the oracle is the runtime crash plus mypy contradicting itself. A variants file (`reviewer-min/probe-bug01-index-variants.py`, run on all three) shows mypy resets the narrowing for an attribute assignment (`b.v = None` reveals `None`) but not for `xs[0] = None`, `d["k"] = None`, an `isinstance` guard, or `del xs[0]`; all four stay at the stale `int`. ty and pyright reset in every case. A non-literal index (`xs[i]`) is never narrowed by mypy, which is why it does not show the bug.

Skeptic pass: no defence found. In the open issue the maintainers concede it. ilevkivskyi: "this is pretty bad inconsistency, we should either narrow an expression, or not. If we narrow it with `isinstance()` it should be also narrowed by an assignment, or at least invalidate the previous narrowing".

Duplicate check: KNOWN. python/mypy#20969 "Unsound typing using isinstance" (open, 2026-08-09) has the same mechanism (`assert isinstance(t[0], int); t[0] = "coucou"; return t[0]` type-checks). JelleZijlstra's comment there: "the indexed assignment doesn't narrow the inferred type for `t[0]`". The earlier judge note ("no exact issue found") was wrong. Related, not the same: python/mypy#7339 (index expressions not narrowed at all). Not in `known_upstream.json`.

### 2. ty types `F.R | F.W` on an `enum.Flag` as `Literal[F.R, F.W]` (conf 0.90, known)

Reproducer: `bug-02-enums-ty-flag-or-literal-union.py`, plus a stronger witness `reviewer-min/bug-02-ty-flag-or-assert-type.py`.

Original file (`a = F.R | F.W; reveal_type(a)`):

```
mypy:    bug-02-enums-ty-flag-or-literal-union.py:18: note: Revealed type is "bug-02-enums-ty-flag-or-literal-union.F"
ty:      bug-02-enums-ty-flag-or-literal-union.py:18:13: info[revealed-type] Revealed type: `Literal[F.R, F.W]`
pyright: Type of "a" is "F"
CPython: <F.R|W: 3> False False
```
ty 0.0.89 and ty 0.0.92 print the same `Literal[F.R, F.W]`.

Witness using `assert_type`, which is spec-defined and needs no text comparison:

```python
v = F.R | F.W
assert_type(v, F)
print(repr(v), v is F.R, v is F.W)
```
```
mypy:    Success: no issues found in 1 source file
ty:      bug-02-ty-flag-or-assert-type.py:18:1: error[type-assertion-failure] Type `Literal[F.R, F.W]` does not match asserted type `F`
pyright: 0 errors, 0 warnings, 0 informations
CPython: <F.R|W: 3> False False
```
ty 0.0.92 prints the same `type-assertion-failure` for the witness. Other operators show the same fault in ty (`reviewer-min/probe-bug02-flag-operators.py`): `F.R & F.W` is also `Literal[F.R, F.W]` and `F.R ^ F.R` is `Literal[F.R]`, while CPython gives `<F: 0>` for both.

Verdict: ty is faulty, symptom INCORRECT_INFERENCE. The runtime value lies outside the revealed type.

Justification: spec, Enums, "Enum Literal Expansion": "This rule does not apply to classes that derive from enum.Flag because these enums allow flags to be combined in arbitrary ways". The type of a combination must be `F`. The likely cause is that `Flag.__or__(self, other: Self) -> Self` is solved from the two literal operands.

Skeptic pass: ty has a family of "Self solved jointly with the receiver" decisions that were closed as intended (TY-4656 in `known_upstream.json`). That defence does not carry over: those decisions are about which calls are accepted, here the inferred result is provably not inhabited at runtime, and the spec text above covers it. The maintainers do not call the Flag behaviour intended either, they call it unsupported.

Duplicate check: KNOWN. astral-sh/ty#3765 "`enum.IntFlag` type narrowed too much when left operand is of type `int` and right operand is a canonical flag" (closed) was answered by sharkdp with "We do not support `enum.Flag` yet, please see #876". astral-sh/ty#876 "Enums: advanced features" (open) lists "[ ] Handling of `enum.Flag`". Related symptom: ty#4590 (open, `Literal[MyFlag.a]` vs `Container[MyFlag]`). Do not file a new issue; at most add the `assert_type` witness to #876 or #3765.

Correction to judge-1: its remark that ty would treat `else` after `is F.R` / `is F.W` as unreachable is not a ty-only effect. mypy does it as well (entry 3 below), and ty keeps the branch reachable when `x` is declared `F`.

### 3. mypy treats `enum.Flag` as exhausted by its members in `is` narrowing (conf 0.85, reviewer-found, same root cause as an open issue)

Reproducer: `bug-06-enums-mypy-flag-is-narrowing-else-unreachable.py`. This one was not in `candidates.md`. I found it while checking the Flag candidate, and no judge has seen it, so the skeptic pass below is mine alone.

```python
def h(x: F) -> str:
    if x is F.R:
        return "R"
    elif x is F.W:
        return "W"
    else:
        return 1 + "bad"
print(h(F.R | F.W))
```

mypy: `Success: no issues found in 1 source file`
ty:
```
bug-06-enums-mypy-flag-is-narrowing-else-unreachable.py:26:16: error[unsupported-operator] Operator `+` is not supported between objects of type `Literal[1]` and `Literal["bad"]`
Found 1 diagnostic
```
pyright: `26:16 - error: Operator "+" not supported for types "Literal[1]" and "Literal['bad']" (reportOperatorIssue)`
CPython:
```
  File ".../bug-06-...py", line 26, in h
    return 1 + "bad"
TypeError: unsupported operand type(s) for +: 'int' and 'str'
```

Verdict: mypy is faulty, symptom FALSE_NEGATIVE with a runtime crash. mypy prints no `reveal_type` and no error for the `else` branch, so it considers the branch dead. The same `x` revealed inside that branch is `F & ~Literal[F.R] & ~Literal[F.W]` in ty and `F` in pyright (`reviewer-min/probe-bug06-flag-param-and-local.py`).

Justification: same spec sentence as entry 2. In mypy's source, `mypy/typeops.py` `try_expanding_sum_type_to_union` expands any `typ.type.is_enum` into `[LiteralType(name, typ) for name in typ.type.enum_members]` and has no `enum.Flag` exemption. The same expansion is why mypy accepts `name_of(F.R | F.W)` for a parameter typed `Literal[F.R, F.W]` (the runtime raises `KeyError: <F.R|W: 3>`), which only pyright rejects. In that witness ty is also silent, so it is not a ty-versus-mypy difference and I did not use it as the oracle.

Skeptic pass: no defence found. The maintainer comment in the open issue calls the behaviour wrong: A5rocks, "I think something must be wrong with narrowing logic, since it doesn't make sense to narrow flags like that!".

Duplicate check: python/mypy#21937 "Incorrect narrowing of Enum.Flag" (open, 2026-09-05) has the same root cause. Its trigger is `==` on a `Flag` followed by `in`, not an `is` chain. I found no issue with the `is`/`else` variant, so treat this as a duplicate of the root cause. Not in `known_upstream.json`.

### 4. mypy infers a mutable `Callable[[T], None]` attribute as contravariant (conf 0.80, NOT found upstream)

Reproducer: `bug-03-generics-mypy-callable-attr-contravariant.py`

```python
class Handler[T]:
    def __init__(self, cb: Callable[[T], None]) -> None:
        self.cb = cb

def use(h: Handler[int]) -> None:
    h.cb = lambda v: print(v.bit_length())

hf = Handler[float](lambda x: print(x.is_integer()))
use(hf)
hf.cb(1.5)
```

mypy: `Success: no issues found in 1 source file`
ty: `bug-03-generics-mypy-callable-attr-contravariant.py:21:5: error[invalid-argument-type] Argument to function `use` is incorrect: Expected `Handler[int]`, found `Handler[float]``
pyright:
```
21:5 - error: Argument of type "Handler[float]" cannot be assigned to parameter "h" of type "Handler[int]" in function "use"
    "Handler[float]" is not assignable to "Handler[int]"
      Type parameter "T@Handler" is invariant, but "float" is not the same as "int" (reportArgumentType)
```
CPython: `AttributeError: 'float' object has no attribute 'bit_length'` (line 22, via the lambda assigned in `use`)

ty 0.0.92 gives the same error as ty 0.0.84.

Verdict: mypy is faulty, symptom FALSE_NEGATIVE.

Justification, three independent pieces:
- Runtime: the program above is accepted by mypy and crashes.
- Self-contradiction, from `reviewer-min/probe-bug03-variance-variants.py` run on all three tools. In mypy, a mutable `T` attribute (`Plain`) and a mutable `Callable[[], T]` attribute (`Producer`) are invariant, while `CbInit[int]` is assignable to `CbInit[bool]`, and a class-level annotation `cb: Callable[[T], None]` behaves the same. ty and pyright reject all five assignments. All three tools agree that a `Final` attribute and a method taking `T` are contravariant.
- Source, the likely cause (read, not executed under a debugger): `mypy/subtypes.py` `infer_variance` has the settable handling on one side only:
  ```python
  if not is_subtype(typ, typ2):
      co = False
  if not is_subtype(typ2, typ):
      contra = False
      if settable:
          co = False
  ```
  There is no mirrored `if settable: contra = False` in the first branch, so a writable member whose type is contravariant in `T` stays contravariant.
- Spec: Generics, Variance Inference, step 3, "using normal assignability rules". The conformance test `generics_variance_inference.py` requires `ShouldBeInvariant5[T]` (public `self.x = x`) to be invariant. A writable `Callable[[T], None]` attribute is the same case.

Skeptic pass: mypy could say Callable attributes are treated like methods. That does not hold, because the variants show mypy already separates `Final` attributes and methods (contravariant) from writable ones, and per `get_member_flags` a plain `Var` is `IS_SETTABLE`. I found no comment, doc entry or issue defending it.

Duplicate check: NOT FOUND. About 30 queries over python/mypy issues and PRs (variance inference, infer_variance, PEP 695 variance, Callable attribute, mutable attribute, settable). Read in full and rejected: #18147 (instance attribute without annotation, different cause), #19439 (polymorphic classmethod), #20501 (underscore-prefixed attributes are exempt on purpose). Nearby by title only: #14869, #17623, #17782, #17786, #19466, #20997. Not in `known_upstream.json`. A mypy maintainer could still point to a discussion I did not find (see limits below).

### 5. ty cannot solve a TypeVar from a generic `TypedDict` argument (conf 0.75, NOT found upstream)

Reproducer: `bug-05-typeddict-ty-generic-typeddict-typevar-unknown.py`. Runtime witness: `reviewer-min/bug-05-ty-generic-typeddict-crash-witness.py`.

Original file, `reveal_type(first(a))` with `a: Resp[int]`:

mypy:
```
bug-05-...py:23: note: Revealed type is "int"
bug-05-...py:24: error: Incompatible types in assignment (expression has type "str", variable has type "int")  [assignment]
bug-05-...py:25: error: Incompatible types in assignment (expression has type "int", variable has type "str")  [assignment]
```
ty:
```
bug-05-typeddict-ty-generic-typeddict-typevar-unknown.py:23:17: info[revealed-type] Revealed type: `Unknown`
Found 1 diagnostic
```
pyright: `23:17 - information: Type of "first(a)" is "int"`, errors on lines 24 and 25 (reportAssignmentType).
CPython: runs, `Runtime type is 'int'`.

Minimal crash witness:
```python
class Resp(TypedDict, Generic[T]):
    data: T
def first(r: Resp[T]) -> T:
    return r["data"]
a: Resp[int] = {"data": 1}
y: str = first(a)
print(y.upper())
```
```
mypy:    bug-05-ty-generic-typeddict-crash-witness.py:23: error: Incompatible types in assignment (expression has type "int", variable has type "str")  [assignment]
ty:      All checks passed!
pyright: 23:10 - error: Type "int" is not assignable to declared type "str" (reportAssignmentType)
CPython: AttributeError: 'int' object has no attribute 'upper'
```
ty 0.0.92: `All checks passed!` for the witness, so it is not fixed in the newest release.

Verdict: ty is faulty, symptom FALSE_NEGATIVE (the cause is an unsolved TypeVar, the revealed type is `Unknown`).

Justification: a fully annotated argument `Resp[int]` against a parameter `Resp[T]` must give `T = int` under ordinary solving, and mypy and pyright agree. Localisation, from `reviewer-min/probe-bug05-typeddict-variants.py` on ty 0.0.84, 0.0.89 and 0.0.92: the same function over an ordinary generic class (`Box[T]`) is solved, while both an old-style `Generic[T]` `TypedDict` and a PEP 695 `TypedDict` give `Unknown`. ty also knows `Resp[int]` and `Resp[str]` differ elsewhere: passing a `Resp[str]` to a `Resp[int]` parameter gives `invalid-argument-type` and assigning it gives `invalid-assignment` (`reviewer-min/probe-bug02-bug05-runtime-and-assignability.py`, ty 0.0.84). The tool contradicts itself.

Skeptic pass: `Unknown` is gradual, so there is no false positive, and the cost is silent acceptance. ty's own tracker treats `Unknown` specialisations of generic `TypedDict`s as defects: ty#4134 (closed, `C(value=1)` revealed `C[Unknown]`) and ty#4803 (open regression, same symptom on another path). No statement that this is intended.

Duplicate check: NOT FOUND for the direct-parameter case. About 20 queries over astral-sh/ty issues and astral-sh/ruff PRs. Read: ty#4803 (regression in 0.0.90 for `dict[K, Burrow[T]] | Iterable[...]`; on my machine that exact program passes on 0.0.84 and 0.0.89 and fails on 0.0.92, while the direct-parameter case fails on all three, so they are different paths), ty#4134, ty#154 ("[x] Implement / write tests for generic TypedDicts"), ty#3935. Open ruff PRs #29236 and #26680 touch call inference and might change the result; I did not test them. Not in `known_upstream.json`. Suggest commenting on #4803 with the direct case, or opening a new issue after a play.ty.dev check.

---

## NOT confirmed

### `bug-04-dataclasses-mypy-initvar-default-class-attr.py` (mypy `attr-defined` on `Sub.extra`)

Reproduces exactly as described, so this is not a pipeline artefact:

mypy:
```
bug-04-...py:17: error: "type[Sub]" has no attribute "extra"  [attr-defined]
bug-04-...py:17: note: Revealed type is "Any"
bug-04-...py:18: error: "type[Sub]" has no attribute "extra"  [attr-defined]
```
ty: `17:13: info[revealed-type] Revealed type: `int``
pyright: `17:13 - information: Type of "Sub.extra" is "Unknown"`, and errors on lines 17 and 18: `Cannot access attribute "extra" for class "type[Sub]"` / `"extra" is an init-only field (reportAttributeAccessIssue)`
CPython: `0`

Why it falls:
- Known duplicate. python/mypy#19889 "attr-defined error is raised when reading default value of an `InitVar` field of a dataclass" (open since 2025-09-20, mypy 1.18.2) is this exact program shape. The earlier note "no duplicate found" was wrong.
- Design divergence. Pyright rejects it with a purpose-written message ("is an init-only field"), so two of three checkers treat class access to an `InitVar` as invalid by design. The typing spec has no rule for it, and the only oracle is a CPython implementation detail (the default stays as a class attribute). That is a defensible maintainer answer, which fails the skeptic step.

---

## Duplicate-check method and its limits

- Tooling: `gh` 2.102.0, authenticated as DerekLaymn, using the REST search endpoint (title, body and comments) and `gh issue view`/`gh api` for bodies. Searched python/mypy, astral-sh/ty and astral-sh/ruff (issues and PRs). Only short keyword queries left the machine, no project code.
- `typediff/data/known_upstream.json` read in full (including the uncommitted edits). None of TY-1090, TY-4212, TY-2255, MYPY-9658 or the prior stances TY-4656, TY-4673, TY-1172, TY-4152 match any candidate. TY-4656 was considered as a defence for bug 2 and rejected above.
- GitHub search treats multi-word queries conjunctively, so an empty result is weak evidence of absence. Issues named above were read in full; other hits were judged by title only.
- Not done: discuss.python.org and python/typing discussions (UNVERIFIED-DUPLICATE-CHECK for that venue), play.ty.dev and mypy-play (replaced by running the newest releases locally: ty 0.0.92, mypy 2.4.0), pyright 1.1.414.

## Corrections to the earlier steps

- `candidates.md` says all five have "no exact upstream match". That is false for bug-01 (mypy#20969) and bug-04 (mypy#19889), and bug-02 is tracked in ty#3765/#876. The duplicate searches in judge-1 and judge-2 used too few keywords.
- `candidates.md` ranks InitVar last at 0.40. It is demoted from the confirmed list above.
- The bug-02 reproducer relies on `reveal_type` text. The `assert_type` witness in `reviewer-min/` is a sounder differential oracle.
- The bug-05 reproducer has no runtime witness and carries a second parameter and a `go()` wrapper that the bug does not need. The `reviewer-min/` version is shorter and crashes.
- The other reproducers (bug-01, bug-03, bug-04) are already minimal; I did not shrink them further.

## Housekeeping

- Pinned versions: README pins `ty==0.0.84 mypy==2.4.0`, DESIGN.md says it was calibrated on pyright 1.1.414 and CPython 3.12, while the venv has pyright 1.1.400 and CPython 3.13.16. The pyright results here are therefore from the older release.
- An empty untracked file named `-l` sits in the repo root (a mistyped `ls -l`). Remove it before committing.
- Nothing was committed. New files in this directory: `REPORT.md`, `review.json`, `bug-06-...py`, and `reviewer-min/` (two minimal witnesses plus six `probe-*.py` variant files cited above). Scratch output in `/tmp` was removed.
