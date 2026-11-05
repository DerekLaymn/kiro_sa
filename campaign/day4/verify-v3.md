# Day 4 verification, batch v3 (Plan §6 checklist)

Candidates: the four rows 'IntEnum alias', 'metaclass reflected operator * and |', 'recursive TVT-default alias tuple reveal' and '__hash__ None reveal' of `campaign/day3-report.md` §4.2.
Date of runs: 2026-11-05. Everything below was run by hand; the programs and the raw outputs live in `/tmp/d4v3/` (not tracked). Day-3 inputs read: report §4.1/§4.2, `runs/day3/out/seed-{0de4710c02b5,229f1d38c10b,83edc0d9bc6c,4d6aa9e30260,a43a619b6518}.md`, the five generated programs and `campaign/day3-triage.txt`.

## 0. Setup and conventions

| Tool | Pinned (project venv) | Latest, `/tmp/d3v-latest` | Master |
|---|---|---|---|
| mypy | 2.4.0 (compiled) | 2.4.1 (compiled) | 2.5.0+dev.879da562a4bba1ff8023799afad195bc364b730a (not compiled), `/tmp/d3v-master` |
| ty | 0.0.84 | 0.0.97 | not available |
| pyright | 1.1.414 | 1.1.414 | n/a |
| CPython | 3.13.16 | | |

Command pattern (cwd `/tmp/d4v3`; `F.py` is the program under test). The pinned binaries in `.venv/bin` are memguard shims already; latest and master go through `memguard.sh`:

```
V=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.venv/bin
G=/home/derek/.config/kiro-hooks/memguard.sh
$V/python F.py
$V/mypy --python-version 3.13 --no-incremental F.py
$V/ty check --python-version 3.13 F.py
$V/pyright --pythonversion 3.13 F.py
$G /tmp/d3v-latest/bin/mypy --python-version 3.13 --no-incremental F.py
$G /tmp/d3v-latest/bin/ty check --python-version 3.13 F.py
$G /tmp/d3v-latest/bin/pyright --pythonversion 3.13 F.py
$G /tmp/d3v-master/bin/mypy --python-version 3.13 --no-incremental F.py
```

Pinned, latest and master gave identical diagnostics for every program in this file, so each output is shown once. The `ty` output below is reduced to the `reveal_type`/diagnostic text (ty prints a multi-line source frame around each; the raw files `/tmp/d4v3/out_*.txt` keep it). `python` prints `Runtime type is '...'` to stderr for each `typing.reveal_type` call; I drop those lines unless they matter.

Bottom line:

| # | Candidate | ty | mypy | pyright | New bug? |
|---|---|---|---|---|---|
| 1 | IntEnum alias | NOT_BUG (ty is right; Day-3 impression "ty wrong" refuted) | NOT_BUG, DUPLICATE mypy#16830 / mypy#21117 | NOT_BUG, KNOWN_LIMITATION, DUPLICATE pyright#11100 | no |
| 2 | metaclass reflected operator `*` and `\|` | `*`: NOT_BUG (right). `\|`: NOT_BUG, DUPLICATE ty#4683 | **BUG, FALSE_POSITIVE / INCORRECT_INFERENCE**, conf 0.7 | NOT_BUG, DESIGN_DIVERGENCE | **yes, mypy** (draft 1) |
| 3 | recursive TVT-default alias tuple reveal | NOT_BUG | NOT_BUG, DESIGN_DIVERGENCE (display `...`; no narrowing on initial assignment = mypy#2008) | NOT_BUG | no |
| 4 | `__hash__` None reveal | reveal: NOT_BUG. Underlying **BUG, FALSE_NEGATIVE**, conf 0.7 | NOT_BUG, DUPLICATE mypy#20230 | NOT_BUG (right) | **yes, ty** (draft 2) |

known_upstream.json was checked against all four (entries ty#4882 #4883 #4884 #4898 #4899 #4900, mypy#22339 #22343 #22344 #22360 #22361, mypy#20969 #21937 #19889, ty#3765, ty#876). None covers these candidates. Closest: ty#876 "Enums: advanced features" (tracking issue, ty already handles the enum cases here) and mypy#22343 (a crash on a self-referencing alias; different symptom than candidate 3).

---

## 1. 'IntEnum alias'

Day-3 program: `enums_literals/d3p_enums_literals_intenum_true_aliases_one__mut1_2f2cf71e.py` (seed-0de4710c02b5), L21 `reveal_type(Integer.TRUE)`. Claim: mypy `Literal[Integer.TRUE]`, ty `Literal[Integer.ONE]`, pyright like mypy, runtime `<Integer.ONE: 1>`, so "runtime value does not inhabit mypy's type" (strong, bug).

### 1.1 REPRODUCE

`c1_a.py` (12 lines):

```python
from enum import IntEnum
from typing import reveal_type


class Integer(IntEnum):
    ONE = 1
    TRUE = True


reveal_type(Integer.TRUE)
reveal_type(Integer.TRUE.value)
print(Integer.TRUE is Integer.ONE, Integer.TRUE, list(Integer))
```

| Tool (pinned = latest = master) | L10 `Integer.TRUE` | L11 `Integer.TRUE.value` |
|---|---|---|
| CPython 3.13 | prints `True 1 [<Integer.ONE: 1>]` (alias of `ONE`; `.value` is the int `1`) | |
| mypy 2.4.0 / 2.4.1 / master | `Literal[c1_a.Integer.TRUE]?` | `Literal[True]?` |
| ty 0.0.84 / 0.0.97 | `Integer` | `int` |
| pyright 1.1.414 | `Literal[Integer.TRUE]` | `Literal[True]` |

Exit codes: all checkers 0 (they only emit notes/infos). `ty` prints `Integer` (not `Literal[Integer.ONE]`) because the enum has a single distinct member after aliasing, and the literal of the only member is displayed as the class.

The disagreement only becomes a decision difference (error vs. no error) when the alias is used in an assignment or exhaustiveness check. `c1_b.py` (19 lines):

```python
from enum import Enum
from typing import Literal, assert_type


class E(Enum):
    A = 1
    B = 1  # same value as A: runtime alias, E.B is E.A
    C = 2


def f(e: E) -> int:
    if e is E.A:
        return 1
    if e is E.C:
        return 2
    return 3  # reachable only if the checker thinks E.B is a separate member


x: Literal[E.A] = E.B
assert_type(E.B, Literal[E.A])
print(E.B is E.A, f(E.B), x)
```

```
$ $V/python c1_b.py
True 1 E.A
$ $V/mypy ... c1_b.py            (pinned, latest and master identical)
c1_b.py:19: error: Incompatible types in assignment (expression has type "Literal[E.B]", variable has type "Literal[E.A]")  [assignment]
c1_b.py:20: error: Expression is of type "Literal[E.B]", not "Literal[E.A]"  [assert-type]
Found 2 errors in 1 file (checked 1 source file)
$ $V/ty check ... c1_b.py        (pinned and latest)
All checks passed!
$ $V/pyright ... c1_b.py         (pinned and latest)
c1_b.py:19:19 - error: Type "Literal[E.B]" is not assignable to declared type "Literal[E.A]"
c1_b.py:20:13 - error: "assert_type" mismatch: expected "Literal[E.A]" but received "Literal[E.B]" (reportAssertTypeFailure)
2 errors, 0 warnings, 0 informations
```

### 1.2 SPEC

Spec text (typing.python.org/en/latest/spec/enums.html, fetched 2026-11-05; same as the local corpus `~/.cache/typediff/docs/spec/enums.txt` lines 173 to 183): "An attribute that is assigned the value of another member of the same enum is not a member itself. Instead, it is an alias for the first member", with the example `AMBER = YELLOW  # Alias for YELLOW` and `reveal_type(TrafficLight.AMBER)  # Revealed type is Literal[TrafficLight.YELLOW]`.

The spec defines aliases only for an attribute assigned *another member* (`AMBER = YELLOW`). It is silent about members that merely repeat an earlier *value* (`B = 1` after `A = 1`), which is the Day-3 shape. The spec says nothing on `.value` for aliases (it only says the revealed value type may be `Literal[1]` "or int or object or Any").

Documentation by the tools: pyright maintainers state that pyright does not track enum values (pyright#1885: "doesn't have knowledge that `SQUARE` and `ALIAS_FOR_SQUARE` happen to have the same value") and decline value-based aliasing (pyright#11100: "such extreme edge cases"). mypy has no statement for in-class aliases; ilevkivskyi's comment in mypy#8657 ("no such thing as enum member aliases, these are just variables") is about module-level variables such as `BLACK = Color.BLACK`, not about aliases inside the enum body.

### 1.2b Accused tool's side (mypy, pyright)

- Value-based aliasing needs the checker to evaluate and hash the right-hand sides (`True` and `1` collide because `hash(True) == hash(1)` and `True == 1`), including `auto()`, mixins and `_generate_next_value_`. Pyright treats this as too much special casing for too little use; that is a legitimate cost argument.
- The spec requires aliasing only for the explicit form, so for the Day-3 program neither tool violates a written rule.
- A checker that keeps `Literal[E.B]` as a separate type is conservative in one direction: it rejects `x: Literal[E.A] = E.B` (false positive) and reports `assert_never(e)` after `E.A`/`E.C` as reachable. Both only create noise; neither hides a runtime error.
- Against the defence: the rule for the explicit alias is in the spec, and mypy gets that one wrong too (see 1.4 variant `c1_e`).

`spec_desugar` and `lsp_probe` do not apply: no desugaring is involved and no editor feature is in question; the difference is in the inferred literal type.

### 1.3 STRONGEST ORACLE

Runtime: `E.B is E.A` is `True`, `list(E)` has two members, `f(E.B)` returns 1, `x` is `E.A`. So `Literal[E.B]` and `Literal[E.A]` denote the same single object, and `x: Literal[E.A] = E.B` is valid. This is an executed counter-example for mypy and pyright, not a spec quote (the spec is silent for the value-duplicate form). For the explicit-alias form the oracle is a spec quote (1.4).

### 1.4 GENERALISE

| Variant | CPython | mypy | ty | pyright |
|---|---|---|---|---|
| `c1_b` value-duplicate `B = 1`, `Literal[E.A] = E.B`, `assert_type` | ok | 2 errors (L19, L20) | passes | 2 errors |
| `c1_c` same enum, `else: assert_never(e)` after `E.A`/`E.C` | prints 1 | L17 `arg-type`: `Literal[E.B]` not `Never` | passes | L17 error |
| `c1_d` `StrEnum` `CRIMSON = "red"`; `IntEnum` `ALSO_ONE = 1` | `S.CRIMSON is S.RED` True, `N.ALSO_ONE is N.ONE` True | `Literal[c1_d.S.CRIMSON]?`, `Literal[c1_d.N.ALSO_ONE]?` | `S`, `Literal[N.ONE]` | `Literal[S.CRIMSON]`, `Literal[N.ALSO_ONE]` |
| `c1_e` **explicit** alias `B = A` (spec form), `reveal_type(E.B)` | `E.B is E.A` True | `Literal[c1_e.E.B]?` (**spec says `Literal[E.A]`**) | `Literal[E.A]` | `Literal[E.A]` |
| `c1_f` program of mypy#16830 (`YELLOW = AMBER`) with `--strict-equality --warn-unreachable`, mypy 2.4.0 and master | prints `alias identical` | L20 `comparison-overlap`: `Literal[TrafficLight.AMBER]` vs `Literal[TrafficLight.YELLOW]` for an `is` that is true at runtime; else-branch type still contains `YELLOW` | n/a | n/a |

Which pass: ty passes every variant. pyright passes the explicit alias only. mypy fails every variant, including the explicit alias that the spec describes.

### 1.5 DUPLICATES

- ty: not the accused tool. `/tmp/d3v-trk/ty.json` (4060 issues): regexes `enum.{0,80}alias|alias.{0,40}enum member` and `duplicate (enum )?value` give nothing relevant (ty#3531 and ty#3446 concern Literal subsets of enums and PEP 695 aliases of enum literals, not member aliasing). ty#876 is the enum tracking issue.
- `gh search issues` (no `--state`), unquoted terms, 5 s spacing (my first batch quoted whole phrases, which `gh` matches as exact strings, so it returned nothing and part of it hit the rate limit; rerun below):
  - python/mypy: `enum alias duplicate values`, `enum same value alias`, `enum member alias Literal`, `enum alias assert_never`, `enum alias for member reveal_type`, `enum members alias spec conformance`.
  - microsoft/pyright: `enum alias duplicate values`, `enum same value alias`, `enum member alias Literal`, `enum alias exhaustive` (no hits).
- Best three read with `gh issue view`:
  - mypy#16830 (closed COMPLETED, 0 comments), "`Enum` member aliases are treated as never-equal": same root cause (aliases and duplicate values are distinct members), explicit `YELLOW = AMBER` plus duplicate values. It is closed but still reproduces on master 879da56 (variant `c1_f`).
  - mypy#21117 (open), "Interaction between an `enum` alias and `assert_never()` seems to fail": explicit alias `DEFAULT = V2`, same error text as `c1_c`.
  - pyright#11100 (open), "Enum member alias is wrongly considered a canonical member of the enum": exactly `a = 1; a_alias = 1`. Maintainer reply: alias the member rather than the value, special casing already large, will not add. Also pyright#1885 (closed): "doesn't have any knowledge" of values.
  - Related only: mypy#8657 (open; aliases through module-level variables and `Literal`).
- `gh search prs --repo astral-sh/ruff` `enum alias ty`: nothing about enum aliasing.

### 1.6 PLAYGROUND

UNVERIFIED-PLAYGROUND: no link created (no write to external services). Program for mypy-play / pyright playground: `c1_b.py` above.

### 1.7 VERDICT

| Tool | Verdict | Dismissal | Confidence | faulty_tool |
|---|---|---|---|---|
| ty | NOT_BUG | none (ty matches CPython) | 0.9 | none |
| mypy | NOT_BUG (underlying FALSE_POSITIVE / INCORRECT_INFERENCE) | DUPLICATE https://github.com/python/mypy/issues/16830 and https://github.com/python/mypy/issues/21117 | 0.85 | mypy (already reported) |
| pyright | NOT_BUG | KNOWN_LIMITATION, DUPLICATE https://github.com/microsoft/pyright/issues/11100 | 0.85 | pyright (maintainer declines) |

Note for the pipeline: the Day-3 "strong" evidence (runtime value does not inhabit mypy's `Literal[Integer.TRUE]`) is only a literal-identity artefact; it hides that ty, not mypy, is right here. Hit: `runs/hits/d4v_enum_value_alias.py`.

---

## 2. 'metaclass reflected operator * and |'

Day-3 programs: `constructors_metaclasses/..._reflected_operator_on_metaclass__mut0_848753c0.py` (seed-229f1d38c10b, L25 `A * B`) and `__mut1_714d2273.py` (seed-83edc0d9bc6c, L25 `A | B`). Claims: `A * B` mypy `Literal['left']`, ty `Literal["right"]`, pyright like mypy, runtime `'right'`. `A | B` mypy `Literal['left']`, ty `types.UnionType special-form`, pyright like mypy, runtime `'right'`. (The report's text says "pyright like ty" for `|`; my run shows pyright `Literal['left']`, like mypy.)

### 2.1 REPRODUCE

`c2_a.py` (17 lines):

```python
from typing import Literal, reveal_type


class LeftMeta(type):
    def __mul__(cls, other: object) -> Literal["left"]:
        return "left"


class RightMeta(LeftMeta):
    def __rmul__(cls, other: object) -> Literal["right"]:
        return "right"


class A(metaclass=LeftMeta): ...
class B(metaclass=RightMeta): ...


reveal_type(A * B)
reveal_type(A * A)
print(A * B, A * A)
```

| Tool (pinned = latest = master) | `A * B` | `A * A` |
|---|---|---|
| CPython 3.13 | `right` | `left` |
| mypy | `Literal['left']` | `Literal['left']` |
| ty | `Literal["right"]` | `Literal["left"]` |
| pyright | `Literal['left']` | `Literal['left']` |

To turn the display difference into an accept/reject difference, `c2_f.py` (19 lines) gives the two operator methods different return types:

```python
from typing import assert_type


class LeftMeta(type):
    def __mul__(cls, other: object) -> int:
        return 1


class RightMeta(LeftMeta):
    def __rmul__(cls, other: object) -> str:
        return "s"


class A(metaclass=LeftMeta): ...
class B(metaclass=RightMeta): ...


s: str = A * B
assert_type(A * B, str)
print(type(A * B).__name__)
```

```
$ $V/python c2_f.py
str
$ $V/mypy ... c2_f.py            (pinned, latest, master identical)
c2_f.py:18: error: Incompatible types in assignment (expression has type "int", variable has type "str")  [assignment]
c2_f.py:19: error: Expression is of type "int", not "str"  [assert-type]
Found 2 errors in 1 file (checked 1 source file)
$ $V/ty check ... c2_f.py        (pinned and latest)
All checks passed!
$ $V/pyright ... c2_f.py         (pinned and latest)
c2_f.py:18:10 - error: Type "int" is not assignable to declared type "str"
c2_f.py:19:13 - error: "assert_type" mismatch: expected "str" but received "int" (reportAssertTypeFailure)
2 errors, 0 warnings, 0 informations
```

The `|` form (`c2_c.py`, same shape with `__or__`/`__ror__`; `# type: ignore[override]` on both methods to silence the mypy STUB-SKEW `[override]` diagnostics of the Day-3 report):

| Tool | `A \| B` | `A \| A` |
|---|---|---|
| CPython | `right` | `left` |
| mypy | `Literal['left']` | `Literal['left']` |
| ty | `<types.UnionType special-form 'A \| B'>` | `<class 'A'>` |
| pyright | `Literal['left']` | `Literal['left']` |

### 2.2 SPEC

The typing spec has no rule for binary operator dispatch. Its only mention is in the concepts chapter: "`a + b` is (roughly, eliding some details) syntactic sugar for either `type(a).__add__(a, b)` or `type(b).__radd__(b, a)`" (`spec/concepts.html`, local corpus `concepts.txt` line 316). Spec silent. The rule that the right operand's reflected method runs first when its type is a subclass of the left operand's type and provides a different implementation is in the Python language reference (data model, `object.__radd__` note), and the checkers cite it: mypy's `check_op_reversible` comment, and pyright#3368/#4088.

Documentation by the tools: pyright maintainers call the instance case "as designed" (pyright#4088, #3368, #10644, all closed). mypy implements the rule (checkexpr.py `check_op_reversible`, STEP 2a: "When we do `A() + B()` where B is a subclass of A, we'll actually try calling B's `__radd__` method first"). ty compares the operands' runtime classes for this since ruff#26434 ("Prefer reflected operators by runtime class", merged) and ruff#26474 ("Preserve uncertain reflected operator dispatch", merged).

### 2.2b Accused tool's side

- pyright: its maintainer argues a declared type `Foo` means "Foo or a subclass", so the static type cannot tell which path the runtime takes (pyright#4088, #10644). For *instances* that is true. For the expressions `A` and `B` written as class names the argument does not hold: a class name denotes exactly that class, and its metaclass is exactly known (`type(A) is LeftMeta`, `type(B) is RightMeta`). But pyright has declined even the instance case, so it is very unlikely to accept this one; I classify it as DESIGN_DIVERGENCE.
- mypy: the rule is implemented for `Instance` operands (`c2_g.py`, below). For class objects the left and right types are callable "type object" types. `check_op_reversible` guards the priority branch with `covers_at_runtime(right_type, left_type)`; for type objects that compares `def () -> B` with `def () -> A`, which is false, so the metaclass relation is never consulted. The defence "it is a rare construct" is fair; the defence "static types cannot know" fails because mypy already makes the same call for instances.
- ty: for `type[A]`/`type[B]` operands (`c2_d.py`) the static type is "A or subclass" and the true answer depends on the runtime class; ty answers `Literal["left"]`, so does everyone else, and CPython prints `right`. That variant is the general inexactness that pyright's argument is about, not specific to any tool.

### 2.3 STRONGEST ORACLE

Self-contradiction of mypy plus runtime. `c2_g.py` (same hierarchy, plain instances):

```python
class L:
    def __mul__(self, other: object) -> int: ...      # returns 1
class R(L):
    def __rmul__(self, other: object) -> str: ...     # returns "s"
s: str = L() * R()
assert_type(L() * R(), str)
```

mypy: `Success: no issues found` (pinned, latest, master). CPython prints `str`. pyright: 2 errors (it declines the rule). ty: `error[invalid-assignment]: Object of type 'str | int' is not assignable to 'str'` and a `type-assertion-failure` (ty is conservative here: it returns the union, which is sound).

So mypy applies the reflected-priority rule to `L() * R()` and does not apply it to `A * B` when the same relation holds between the two metaclasses. CPython evaluates both with the reflected method first.

### 2.4 GENERALISE

| Variant | CPython | mypy | ty | pyright |
|---|---|---|---|---|
| `c2_a` `*`, class objects | `right` | `left` (wrong) | `right` | `left` |
| `c2_f` `*` with different return types, `str = A * B` | ok | 2 false errors | passes | 2 errors |
| `c2_g` control, plain instances | `str` | passes (correct) | `str \| int` errors (conservative) | 2 errors |
| `c2_c` `\|` on metaclass, class objects | `right` / `left` | `left` / `left` (first wrong) | UnionType / `<class 'A'>` (both wrong, ty#4683) | `left` / `left` (first wrong) |
| `c2_d` operands typed `type[A]`, `type[B]` (inexact) | `right` | `left` | `left` | `left` |
| `c2_d` `b = B; b * A` (right operand is not a subclass metaclass) | `left` | `left` | `left` | `left` (correct everywhere) |

### 2.5 DUPLICATES

- ty: `/tmp/d3v-trk/ty.json` regexes `metaclass.{0,120}__r?or__|__r?or__.{0,120}metaclass`, `metaclass.{0,100}(binary|operator)`, `__rmul__|__radd__`, `reflected (operator|dunder|method)`. `gh search issues --repo astral-sh/ty`: `metaclass __or__`, `metaclass __ror__`, `reflected operator subclass`, `UnionType metaclass`. Hit: ty#4683 (open) "Class `|` expressions ignore custom metaclass `__or__`", same symptom as the `|` row: `A | B` is inferred as a union special form although the metaclass defines `__or__`. Duplicate of the ty `|` half. `gh search prs --repo astral-sh/ruff`: `reflected operator ty` gives ruff#26434 and #26474 (merged; they explain why ty gets the `*` case right), `metaclass __or__ ty` nothing relevant.
- mypy (12 phrases, none found a match): `metaclass reflected operator`, `metaclass __rmul__`, `metaclass __ror__`, `reflected operator subclass`, `__radd__ subclass priority`, `metaclass binary operator class object`, `reverse operand metaclass`, `__rmul__ subclass`, `right operand subclass reflected`, `operator metaclass type object`, `__ror__ metaclass type`, `reverse operator subclass priority`. Read: mypy#4789 (closed; operators on `Type[Foo]` with a metaclass, unrelated to priority), mypy#4929 (closed; `x * 0` on `Type[S]`), mypy#19006 (closed; subclass priority fixed for `tuple` subclasses, shows the maintainers treat priority bugs as bugs). No duplicate.
- pyright: `metaclass reflected operator`, `metaclass __ror__`, `reflected operator subclass`, `__radd__ subclass right operand`, `reverse operand subclass`. Read: pyright#4088 (closed COMPLETED, instance case, "as designed"), #3368 (closed, same), #10644 (closed NOT_PLANNED, same). None is about class-object operands.

### 2.6 PLAYGROUND

UNVERIFIED-PLAYGROUND: no link created. Program for mypy-play: `c2_f.py` above.

### 2.7 VERDICT

| Tool | Verdict | Dismissal / symptom | Confidence | faulty_tool |
|---|---|---|---|---|
| mypy | **BUG**, FALSE_POSITIVE (shows as INCORRECT_INFERENCE with equal return types) | none; new. Draft 1 | 0.7 | mypy |
| pyright | NOT_BUG | DESIGN_DIVERGENCE (maintainer: by design; pyright#4088, #3368, #10644) | 0.7 | none |
| ty, `*` | NOT_BUG | none (ty is right) | 0.9 | none |
| ty, `\|` | NOT_BUG | DUPLICATE https://github.com/astral-sh/ty/issues/4683 (underlying INCORRECT_INFERENCE) | 0.9 | ty (already reported) |

Why 0.7 for mypy and not higher: the construct is rare, and mypy's maintainers could close it as an edge case; the evidence for it being a defect is CPython's result plus mypy's own implementation of the same rule for instances. The location in `covers_at_runtime` is a hypothesis from reading the source, not verified with a patch. Hit: `runs/hits/d4v_metaclass_reflected_op.py`.

---

## 3. 'recursive TVT-default alias tuple reveal'

Day-3 program: `recursive_aliases/d3p_crash_mypy_segv_recursive_tvt_default_alias__mut0_9fca6f47.py` (seed-4d6aa9e30260), L20 `reveal_type(sample)`. Claim: mypy `tuple[int, tuple[str, ...]] | None`, ty fully literal nested tuple, pyright like ty, runtime nested tuple does not inhabit mypy's type (strong).

### 3.1 REPRODUCE

`c3_b.py` (16 lines; the `type Shape[*Ts = *tuple[int]]` line of the Day-3 program is not needed, see 3.4):

```python
from typing import reveal_type

type Left = tuple[int, Right] | None
type Right = tuple[str, Left]

sample: Left = (1, ("a", (2, ("b", None))))
reveal_type(sample)


def g(n: Left) -> None:
    reveal_type(n)
    if n is not None:
        reveal_type(n[1])
        reveal_type(n[1][1])


g(sample)
print(sample)
```

| Line | mypy (pinned = latest = master) | ty (pinned = latest) | pyright |
|---|---|---|---|
| 7 `sample` | `tuple[int, tuple[str, ...]] \| None` | `tuple[Literal[1], tuple[Literal["a"], tuple[Literal[2], tuple[Literal["b"], None]]]]` | same as ty (with `'a'` quotes) |
| 11 `n` | `tuple[int, tuple[str, ...]] \| None` | `tuple[int, Right] \| None` | `tuple[int, tuple[str, Left]] \| None` |
| 13 `n[1]` | `tuple[str, tuple[int, tuple[str, ...]] \| None]` | `tuple[str, Left]` | `tuple[str, tuple[int, Right] \| None]` |
| 14 `n[1][1]` | `tuple[int, tuple[str, tuple[int, ...] \| None]] \| None` | `tuple[int, Right] \| None` | `tuple[int, tuple[str, Left]] \| None` |

CPython prints `(1, ('a', (2, ('b', None))))`. No checker reports an error.

### 3.2 SPEC

The spec silently covers recursive aliases in `aliases.html` (they are allowed) and says of narrowing only: "Type checkers should narrow the types of expressions in certain contexts. This behavior is currently largely unspecified" (`spec/narrowing.html`, local `narrowing.txt` lines 7 to 8). It does not specify how `reveal_type` prints a type or whether a declared union is narrowed on assignment. Spec silent.

Documentation: pyright's `mypy-comparison.md` states that mypy "skips assignment-based type narrowing when the target variable includes a type annotation" and links mypy#2008 as the plan to remove the inconsistency. For the printing: mypy's own source (`mypy/types.py`, `TypeStrVisitor.visit_type_alias_type`, master 879da56) returns the string `"..."` when it meets a recursive alias that is already being expanded.

### 3.2b Accused tool's side (mypy)

- The `...` in `tuple[str, ...]` is the recursive alias placeholder `Left`, not a variadic tuple. Evidence: `n[1]` in the table prints `tuple[str, tuple[int, tuple[str, ...]] | None]`; the `Right` alias is `tuple[str, Left]`, a 2-tuple, and the inner `...` stands where `Left` repeats. So the type mypy holds is correct; the text is ambiguous.
- `| None` and the missing literal types come from mypy not narrowing a declared type on its initial assignment (`p: tuple[int] | None = (1,)` reveals `tuple[int] | None`, variant `c3_h`), the long-standing mypy#2008. mypy treats the declared type as authoritative at that point; that is a documented difference, not a recursion problem.
- ty and pyright narrow on assignment, which matches CPython here, so there is nothing to defend on their side.

### 3.3 STRONGEST ORACLE

No bug oracle exists. The Day-3 oracle ("runtime value does not inhabit mypy's type") rests on reading `tuple[str, ...]` as "tuple of any length of str". The runtime value `("a", (2, ...))` inhabits `tuple[str, Left]`, which is what mypy holds. There is no runtime error, no self-contradiction and no spec statement against mypy's behaviour.

### 3.4 GENERALISE

| Variant | mypy | ty | pyright |
|---|---|---|---|
| `c3_a` Day-3 shape with `type Shape[*Ts = *tuple[int]]` and `default_shape: Shape = (5,)` | `sample`: as above; `default_shape`: `tuple[int]` | literal tuples; `tuple[Literal[5]]` | literal tuples; `tuple[Literal[5]]` |
| `c3_c` old-style `TypeAlias` strings instead of `type` | same `...` text | literal tuple | literal tuple |
| `c3_d` TypeVarTuple default alone: `Shape` / `Shape[str, str]` | `tuple[int]`, `tuple[str, str]` | `tuple[Literal[5]]`, `tuple[Literal["x"], Literal["y"]]`; param `tuple[int]` | same as ty |
| `c3_e` `b: Left = None`, `c: Right = ("a", (1, ("b", None)))` | `tuple[int, tuple[str, ...]] \| None` for `None`; `tuple[str, tuple[int, ...] \| None]` for `c` | `None`, literal tuple | `None`, literal tuple |
| `c3_f` non-recursive alias `type Plain = tuple[int, str] \| None`, `p: Plain = (1, "a"); p[0]` | `tuple[int, str] \| None` and `error: Value of type "tuple[int, str] \| None" is not indexable [index]` (mypy#2008) | no error | no error |
| `c3_h` `x: tuple[int] \| None = (1,)`, `y: list[int] \| None = [1]` | `tuple[int] \| None`, `list[int] \| None`, 2 `[index]` errors | `tuple[Literal[1]]`, `list[int]` | like ty |

The TypeVarTuple default plays no part: `c3_b` and `c3_e` have none and show the same mypy text, and `c3_d` shows all three tools agree on the default itself. The mypy `[index]` errors in `c3_f`/`c3_h` are a false positive in the mypy#2008 family and appear without any alias; they are known and not part of this candidate.

### 3.5 DUPLICATES

- ty is not the accused tool: `/tmp/d3v-trk/ty.json` regexes for recursive alias reveal give ty#3699 / ty#3837 (different: `Divergent`, cycle panic). `gh search issues --repo astral-sh/ty` `recursive alias reveal`: nothing matching.
- mypy: `gh search issues`: `recursive alias reveal_type tuple`, `narrowing initial assignment`, `declared type narrow on assignment tuple`, `Optional tuple not narrowed assignment`, `recursive type alias Revealed type`, `tuple[ ... recursive alias print`. Read: mypy#2008 (open, 37 comments), "Types not added to binder on initial assignment", which is the `| None` part exactly. No issue about the `...` rendering ambiguity.
- pyright: not accused.
- `gh search prs --repo astral-sh/ruff` `recursive alias`: ruff#29057 "Preserve recursive aliases when rebuilding intersections" (merged) concerns ty only.
- known_upstream.json: mypy#22343 is a segfault on an alias that refers to itself through another generic alias; no overlap with this program (mypy does not crash on it).

### 3.6 PLAYGROUND

UNVERIFIED-PLAYGROUND: no link created. Program for mypy-play: `c3_b.py` above.

### 3.7 VERDICT

| Tool | Verdict | Dismissal | Confidence | faulty_tool |
|---|---|---|---|---|
| mypy | NOT_BUG | DESIGN_DIVERGENCE (no narrowing on annotated assignment, mypy#2008 DUPLICATE; the recursive placeholder prints as `...`) | 0.85 | none |
| ty | NOT_BUG | none (matches CPython) | 0.9 | none |
| pyright | NOT_BUG | none | 0.9 | none |

Possible low-priority DIAGNOSTIC_DEFECT for mypy (printing a recursive placeholder as `...` is indistinguishable from a variadic tuple); it is a display convention, I do not claim it and I found no existing issue. Pipeline note: the Day-3 evidence rule "runtime value does not inhabit the revealed type" mis-fires when the revealed text contains the recursive-alias `...`; a normalizer rule that treats `tuple[X, ...]` inside a recursive alias as opaque would remove this class. Hit (instructive): `runs/hits/d4v_recursive_alias_dots.py`.

---

## 4. '__hash__ None reveal'

Day-3 program: `inheritance_mro/d3p_inheritance_mro_hash_none_from_eq__mut1_fdf751d0.py` (seed-a43a619b6518), L28 `reveal_type(Keyed().__hash__())`. Claim: mypy prints nothing, ty `Never`, pyright `int`; medium evidence "mypy treats reachable code as unreachable".

### 4.1 REPRODUCE

`c4_a.py` (16 lines):

```python
from typing import reveal_type


class Plain:
    def __eq__(self, value: object) -> bool:
        return True


class Keyed(Plain):
    def __hash__(self) -> int:
        return 1


assert Plain.__hash__ is None
reveal_type(Keyed().__hash__())
print("after", hash(Keyed()))
```

| Tool (pinned = latest = master) | Result |
|---|---|
| CPython 3.13 | prints `after 1` (the assert passes: `Plain.__hash__` is `None`) |
| mypy | `Success: no issues found`, no `reveal_type` note |
| ty | `Revealed type: Never` |
| pyright | `Type of "Keyed().__hash__()" is "int"` |

Without the assert (`c4_c.py`): CPython `1`, mypy `int`, ty `int`, pyright `int`. So the difference is caused by the assert.

`c4_d.py` (assert, then `reveal_type(1)`): mypy silent, ty `Literal[1]`, pyright `Literal[1]`. `c4_e.py` (a class that really has `__hash__` as a method, `assert Other.__hash__ is None` fails at runtime with `AssertionError`): mypy silent, ty `Literal[1]`, pyright prints nothing for line 14 (it marks the code unreachable).

The decision-level symptom is `c4_m.py` (23 lines):

```python
from collections.abc import Hashable


class Plain:
    def __eq__(self, value: object) -> bool:
        return True


class Sub(Plain): ...


class Keyed(Plain):
    def __hash__(self) -> int:
        return 1


def need(x: Hashable) -> int:
    return hash(x)


need(Keyed())  # fine at runtime
need(Plain())  # TypeError: unhashable type: 'Plain' at runtime
need(Sub())  # TypeError: unhashable type: 'Sub' at runtime
```

```
$ $V/python c4_m.py
TypeError: unhashable type: 'Plain'
$ $V/mypy ... c4_m.py            (pinned, latest, master identical)
Success: no issues found in 1 source file
$ $V/ty check ... c4_m.py        (pinned and latest)
All checks passed!
$ $V/pyright ... c4_m.py         (pinned and latest)
c4_m.py:22:6 - error: Argument of type "Plain" cannot be assigned to parameter "x" of type "Hashable" in function "need"
c4_m.py:23:6 - error: Argument of type "Sub" cannot be assigned to parameter "x" of type "Hashable" in function "need"
2 errors, 0 warnings, 0 informations
```

### 4.2 SPEC

The typing spec says nothing about `__hash__` or implicit `__hash__ = None` (`grep` of the whole local corpus finds `Hashable` only in an unrelated protocol example, `protocol.txt` line 457 to 464). Spec silent. The rule is in the Python language reference (data model, `object.__hash__`): a class that overrides `__eq__()` and does not define `__hash__()` has its `__hash__()` implicitly set to `None`.

Documentation by the tools: pyright models it (it reports `Plain.__hash__` as `None`). mypy: open feature request, mypy#2455 "MyPy does not enforce Hashability", where erictraut notes that pyright added the check once typeshed gained the needed stub changes and that adding it to mypy "should be relatively easy". ty: ruff#27441 (merged 2026-08-05) rejects `Hashable` for classes that set `__hash__: ClassVar[None]`, built-in containers and mutable dataclasses; it does not mention `__eq__`.

### 4.2b Accused tool's side (ty, mypy)

- mypy: it reveals `def (self: object) -> int` for `Plain.__hash__` (variant `c4_b`) because typeshed declares `object.__hash__` as a method; synthesizing `__hash__: None` is on the open list (mypy#2455, #18622, #20230). The silence at L28 of the Day-3 program is not an extra bug: `assert <method> is None` makes the rest of the module unreachable in mypy, which prints nothing for unreachable code by default.
- ty: the `Never` at L28 comes from the same assert. Evidence from `c4_k.py` (`assert A.f is None`, with `f` a plain method, then reveals of unrelated `B.f`, `B.g`, `B().g()`): every non-literal expression after the assert is `Never`, only the literal `3` keeps `Literal[3]`. That matches ty treating the code after a statically impossible assert as unreachable; it is not a leak of narrowing onto `Keyed`. The reveal itself is therefore not a bug.
- ty and `Hashable`: ty already implements the rule for dataclasses (`Record.__hash__` is `None`, and `Record("a")` is rejected for `Hashable`, variant `c4_n`). The `__eq__` rule is the same mechanism with a different trigger; no document says ty leaves it out on purpose.

`spec_desugar` and `lsp_probe` do not apply (no desugaring or editor feature involved).

### 4.3 STRONGEST ORACLE

Runtime crash that no checker except pyright reports: `hash(Plain())` and `{Plain()}` raise `TypeError: unhashable type: 'Plain'`; `need(Plain())` above fails at runtime while mypy and ty accept it. pyright, which implements the data-model rule, rejects it. The oracle is the CPython exception.

### 4.4 GENERALISE

| Variant | CPython | mypy | ty | pyright |
|---|---|---|---|---|
| `c4_m` `Hashable` parameter, `Plain`, `Sub(Plain)`, `Keyed` | `TypeError` for `Plain`, `Sub` | accepts all | accepts all | rejects `Plain`, `Sub`, accepts `Keyed` |
| `c4_n` control: mutable `@dataclass` `Record`, `Ne` (only `__ne__`), `Lt` (only `__lt__`) | `TypeError` for `Record`; `hash(Ne())` and `hash(Lt())` succeed (checked separately) | accepts all | rejects `Record` only | rejects `Record` and `Plain`; accepts `Ne`, `Lt` |
| `c4_b` `reveal_type(Plain.__hash__)`, `reveal_type(Record.__hash__)`, `{Plain()}`, `{Record("a")}`, `h1: Hashable = Plain()` | `{Plain()}` raises `TypeError` | `def (self: object) -> int` for both; no errors | `def __hash__(self) -> int` for `Plain`, `None` for `Record`; rejects only `h2: Hashable = Record("a")`; no set errors | `None` for both; errors on both `Hashable` assignments and both set displays (`reportUnhashable`) |
| `c4_f`/`c4_k` reveals after a statically false assert | n/a | silent | `Never` for non-literal expressions | pyright treats the code as unreachable or evaluates normally, depending on whether it can decide the assert |
| `c4_h` `if Base.f is None:` branch | n/a | branch skipped | `Never` inside the branch | skipped |

Which pass: pyright passes everything. ty passes only the dataclass case. mypy passes none.

### 4.5 DUPLICATES

- ty: `/tmp/d3v-trk/ty.json` regexes `__eq__.{0,200}__hash__|__hash__.{0,200}__eq__`, `unhashable`, `__hash__\s*=\s*None`, `hashab`, `defines? `?__eq__`?`, `implicit.{0,40}__hash__`. `gh search issues --repo astral-sh/ty`: `__eq__ __hash__ unhashable`, `__hash__ __eq__ Hashable`, `implicit __hash__`, `__hash__ None class`, `Hashable class __eq__`. Hits:
  - ty#3781 (open) "Flag non-hashable objects as error in `set`/`dict`": mutable dataclass in a set; reported as a missing check for set/dict display, not for `Hashable`, not for `__eq__` classes.
  - ty#4157 (closed by ruff#27441) "Overriding `__hash__` does not make the object unhashable": `__hash__: ClassVar[None]` and `list` against `Hashable`.
  - ty#4748 (closed) "False invalid-attribute-override when subclass restores `__hash__` on a dataclass".
  None covers implicit `__hash__ = None` from `__eq__`. `gh search prs --repo astral-sh/ruff`: `__hash__ ty`, `unhashable ty` give ruff#27441, ruff#29471 (merged: "Allow subclasses to restore hashability"), ruff#26040 (closed: union simplification). None mentions `__eq__`.
- mypy: `gh search issues`: `__eq__ __hash__ unhashable`, `unhashable dataclass`, `__hash__ None __eq__`, `Hashable __eq__`. Read: mypy#20230 (open) "Hashing of unhashable objects is not detected" (exact `__eq__`-only class, `hash`, `in set()`, set and dict display), mypy#18622 (open) "Incorrect inference for types with `__eq__` and no `__hash__`" (proposes `ClassVar[None]`), mypy#2455 (open, long thread). Also mypy#11463 (dataclass not Hashable), mypy#4266.
- pyright: not accused.

### 4.6 PLAYGROUND

UNVERIFIED-PLAYGROUND: no link created. Program for the ty playground: `c4_m.py` above.

### 4.7 VERDICT

| Tool | Verdict | Dismissal / symptom | Confidence | faulty_tool |
|---|---|---|---|---|
| mypy | NOT_BUG for the reveal; underlying FALSE_NEGATIVE | DUPLICATE https://github.com/python/mypy/issues/20230 (also #18622, #2455) | 0.9 | mypy (already reported) |
| ty, the Day-3 reveal (`Never`) | NOT_BUG | NOISE (unreachable-code evaluation after a statically false assert) | 0.8 | none |
| ty, `Hashable` parameter accepts `__eq__`-only classes | **BUG, FALSE_NEGATIVE** | none found; new. Draft 2 | 0.7 | ty |
| pyright | NOT_BUG | none (matches CPython) | 0.9 | none |

Why 0.7 for ty: the data-model rule is unambiguous and ty already implements its dataclass sibling, but the ty maintainers may treat it as part of the open hashability work (ty#3781) and I could not read their intent beyond the merged PR text. Hit: `runs/hits/d4v_eq_no_hash_hashable.py`.

---

## 5. Notes on process

- Searches: the first two `gh` batches wrapped whole phrases in quotes (exact-phrase matching) and then hit the API rate limit because other verification agents share the account; they returned no results and are not used as evidence. All search results above come from reruns with unquoted terms, 5 s apart, retried after 30 s on a rate-limit message.
- `runs/` is git-ignored in this repo, so the four `runs/hits/d4v_*.py` files exist on disk but are not part of the commit. All four have the three header lines, a valid AREAS key, compile under the venv python, and pass `typediff.generator.preflight` with no blocking entry (checked with a script modelled on `campaign/day3m/check_hits.py`).
- Nothing was filed, pushed or posted. All playground links are placeholders.
