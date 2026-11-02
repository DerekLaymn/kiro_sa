# Triage of the top 5 typediff patterns, day-1 harvest (ty 0.0.84, mypy 2.4.0, pyright 1.1.414, CPython 3.13.15)

Read-only. All experiments ran on copies in /tmp/tri. No repo file, no harvest-out file and no issue was touched.

## Summary

| # | Pattern | Verdict | Confidence | One-line reason |
|---|---|---|---|---|
| 1 | only_ty / unresolved-reference | HARNESS NOISE (plus a real, known mypy design gap) | high | The test fragments use `x: T` (never assigned) or a forward reference. ty, pyright and CPython all agree the name is unbound. The "strong bug evidence" is the NameError that confirms ty, but it is blamed on mypy. |
| 2 | reveal_mismatch / gradual | HARNESS NOISE + DESIGN DIFFERENCE (Any vs Unknown) | high for the bulk, low for the 133 "strong" | The harvest replays each tool's own test suite in the other tool. Strong evidence is mostly NameError on cascades, `None` from stub-bodied functions, or mypy's `__new__` handling. |
| 3 | reveal_mismatch / different | DESIGN DIFFERENCE + KNOWN UPSTREAM (mypy#15182), with one sub-case NEEDS MORE WORK | medium | `__new__` returning a non-subtype is a spec-backed ty reading that mypy rejects. One sub-case (metaclass attribute vs a declared-only class attribute) contradicts the runtime in ty and pyright. |
| 4 | runtime_miss | HARNESS NOISE (anchoring, cascades, `type: ignore`, stub bodies) with 1-2 KNOWN LIMITATIONS | medium-high | None of the 55 is a clean false negative. About 17 have a checker diagnostic inside the compound statement that the traceback blames. |
| 5 | reveal_mismatch / uncomparable | DESIGN DIFFERENCE (mypy joins, ty and pyright keep unions) + HARNESS NOISE | high | `join()` has a `pass` body, so the runtime value is `None` and "does not inhabit" is meaningless. |

Key systemic finding: the harvested files keep the original expectation comments (`# N: Revealed type is "..."` for mypy, `# revealed: ...` for ty). That gives a free oracle that typediff does not use. In patterns 2, 3 and 5, the tool the test came from matches its own expectation in about 96% of members where a comparison is possible (table in section "Pattern 2"). So these patterns are "tool A's test suite run through tool B". They measure how much the two tools differ, not bugs.

## How the classification columns work

Sources: `typediff/typenorm.py` (class `Relation`, `relation()`, `gradual_diff()`), `typediff/cli.py::cmd_triage`, `typediff/rules.py::attach_runtime_evidence`, `typediff/parsers.py::classify_exception`.

- `reveal_mismatch | <relation>` is the `Relation` between the two normalised revealed types.
  - `gradual`: at least one side contains Any, Unknown, @Todo or Divergent, and the differences are only where one or both sides are gradual (`gradual_diff` returns "both" or "one"). Most are mypy `Any` against ty `Unknown`, or `Any` against a concrete type.
  - `different`: neither side is gradual, and neither refines the other.
  - `uncomparable`: a side is unparsable or not "comparable". That means callables, overloads, `type[...]`/`<class ...>` forms, or an opaque text.
  - `ty_more_precise` and `mypy_more_precise` are the strict refinements (patterns 7 and 8 in the list).
- `strong bug evidence` (the `*` in triage output) means: the finding has an Evidence item with `supports == "bug"`, `verified`, and `strength == "strong"`. Only two producers exist in `attach_runtime_evidence`:
  1. "CPython raised X with this statement on the stack", used when the exception class is in `STRONG_TYPE_EXC` (TypeError, AttributeError, NameError, UnboundLocalError) and the statement is a frame anchor.
  2. "runtime value ... does NOT inhabit <tool>'s revealed type", from the `reveal_type` probe.
- Blame logic: for `only_ty` the blame is hard-coded to `mypy` (`blame = {ONLY_MYPY: "ty", ONLY_TY: "mypy", RUNTIME_MISS: "both"}`), whether or not the exception is the very thing the reporting tool said. This is the root of pattern 1.
- `runtime_miss | ()` means CPython raised a strong exception at a statement that neither checker had a diagnostic on (`discrepancy.py:120`, anchored on the statement in the traceback frame).

## Pattern 1: only_ty, unresolved-reference (661 findings, 167 "strong")

Verdict: HARNESS NOISE. Confidence: high. A real mypy gap sits underneath (mypy accepts a read of a declared but unassigned variable).

Evidence:
- Example `mypy__check_abstract__testInstantiationAbstractsInTypeForFunctions.py` L22-23: `x: Type[B]` then `f(x)`. Results on a /tmp copy:
  - ty: `L23:3 error[unresolved-reference] Name x used when not defined`.
  - pyright: `"x" is unbound (reportUnboundVariable)`.
  - mypy: no diagnostic for L23.
  - python: `NameError: name 'x' is not defined`.
- Same for `...testNewReturnTypeCallableInference.py` L12/L14 (`ta: type[A]` then `foo(ta)`), which also produces ty `Unknown` reveals (feeds pattern 2).
- Minimal repro, tested with mypy 2.4.0 even with `--enable-error-code possibly-undefined --enable-error-code used-before-def`:
  ```python
  x: int
  print(x)
  def f() -> None:
      y: int
      print(y)
  ```
  mypy: "no issues". ty: 2 errors (`unresolved-reference`). pyright: 2 `reportUnboundVariable`. CPython: NameError.
- Census of the 661 members (AST analysis of each program, /tmp/analysis.py): about 380 are annotation-only names (declared, never assigned). Most of the rest (about 250) are forward references in variable annotations (see `testSubtypingWithGenericTypeSubclassingGenericAbstractClass.py`: `acd: A[C, D]` before `class A`). Only about 10 are truly never bound. Pyright agrees with ty on essentially all of them (the "pyright flagged the same line" column was true for about 640 of 661).
  - Forward references: ty reports them at `--python-version 3.13` and CPython 3.13 raises NameError. This is correct for 3.13 (deferred annotations arrive in 3.14, PEP 649/749). mypy and pyright both accept them (pyright is lenient here).
- "167 strong bug evidence" breakdown: all are `CPython raised NameError ... Checker output here: error[unresolved-reference]`. The exception message names the same name the checker flagged. That supports ty's report, but `rules.py:124` assigns `blame="mypy"` and `supports="bug"`.

Argue the accused tool's side (mypy): mypy does not do definite-assignment analysis for declared-only variables. Its `possibly-undefined` check works on branches and does not cover a bare annotation. The mypy test suite relies on that: `x: Type[B]` is the idiom for "give me a value of this type" in `check-*.test` files. It is test scaffolding, not a program that anyone runs. No reasonable reading calls ty wrong here.

Systemic? Yes. This one rule inflates about 160 of the 167 "strong" starred items here, and 82+ more in pattern 2 (reveal statements that raise NameError).

Proposed fixes (not applied):
1. `rules.py::attach_runtime_evidence`: when the exception is NameError/UnboundLocalError and the exception's name appears in the reporting tool's own message (ty "Name `x` used when not defined", mypy `Name "x" is not defined`, pyright "x is unbound"), emit Evidence with `supports="neutral"` or a new "reporter confirmed" type, strength weak. Do not blame the silent tool.
2. Extend `agreed_undefined_names` (rules.py:~95) from "both checkers" to "any one checker plus runtime NameError for the same name", and mark the case `valid=False` with problem "test fragment uses names it never binds" so the findings are dismissed as invalid test.
3. In `scripts/harvest_seeds.py::usable()`, either skip or rewrite programs with module-level annotation-only variables that are later read (rewrite: `x: T = cast(T, ...)`/`x = ...`) and add `from __future__ import annotations` when the program has forward references. Rewriting mypy fragments is a bigger change; the cheap option is skipping.
4. known_upstream.json: add a `prior_stances` entry (stance `intended`, no URL found) for mypy "no definite-assignment check for annotation-only variables", kind `only_ty`, codes `["unresolved-reference"]`, message regex "used when not defined", source regex `^\w+\s*:\s*[^=\n]+$`. Per the file's own docs, prior_stances never dismiss, they only cap at REVIEW. For dismissal use a KB rule (item 5).
5. kb.py: new entry "ANNOTATION-ONLY-READ" (dismissal DESIGN_DIVERGENCE), matching `only_ty` + unresolved-reference where the AST has `AnnAssign(value=None)` for that name at module or function scope with no later assignment before the use.

Not verified: I did not search whether mypy has an open issue for definite assignment on bare annotations. Three queries (two body-text, one title) returned nothing relevant. Not a ty bug either way.

## Pattern 2: reveal_mismatch, gradual (1332 findings, 133 "strong")

Verdict: HARNESS NOISE for the "strong" part, DESIGN DIFFERENCE (mypy `Any` vs ty `Unknown`, plus version skew) for the rest. Confidence: high for the first, medium for the second.

Evidence:
- Origin check (/tmp/an3.py, compares each tool's reveal with the test's own expectation comment after stripping `builtins.`, `__main__.`, `case.`): of the 1332, 816 are ty-origin where ty matches its own `# revealed:` and mypy differs; 212 are mypy-origin where mypy matches its own `# N:` and ty differs. Only 33 + 6 + 225 have the origin tool differing from its own expectation (see version skew below).
- "Strong" breakdown (/tmp/analysis.py): 82 `CPython raised NameError` (same cause as pattern 1: `reveal_type(foo(ta))` with `ta` unbound, so ty reveals `Unknown` while mypy reveals `int`); 24 + 6 "does NOT inhabit" and 21 TypeError/AttributeError.
- `ty__call__constructor__17.py`: `class C: __new__: type[Left] | type[Right]` is a declaration only; runtime has plain `object.__new__`, so `C()` is a `C`. ty reveals `int` (this is the mdtest's point: `__new__` is the union of callables returning int). mypy: errors on `__new__` assignment lines and reveals `Any`; pyright reveals `Left | Right`. The runtime probe says "C does not inhabit int", but the program has no assignment, so runtime says nothing about what the declaration means. This is a test whose runtime behaviour is unrelated to the static claim.
- `testNewReturnTypeCallableInference.py` L13-16: ty gives `int`/`Unknown`/`A`/`Unknown` where mypy gives `int/int/A/A`; the Unknowns are caused solely by the unbound `ta`.
- Version skew: `harvest_seeds.py` clones `--depth=1` HEAD of ruff and mypy with no pin, but the run uses ty 0.0.84 and mypy 2.4.0. Example `ty__bidirectional__41.py`: mdtest expects `int`; ty 0.0.84 reveals `Unknown` (pyright also `Unknown`, mypy `int`). Many of the 225 "ty-origin, ty differs from its own expectation" rows (e.g. `T@bounded`, `Never`, `Literal[1] | A`) look like this. I could not run a newer ty to confirm (no newer build in this environment).
- Gradual shape: 532 mypy `Any` vs non-Unknown ty type, 479 non-Any vs ty `Unknown`, 210 `Any` vs `Unknown`, 111 neither. `Any` vs `Unknown` is already handled by KB `BOTH-GRADUAL` when the position matches.

Accused tool's side: ty prints `Unknown` where it cannot infer. For ty it is a gradual type that is allowed to appear for unannotated or erroneous code, and the spec says nothing about what `reveal_type` prints. A reveal difference between Any and a concrete type is an inference-precision difference, not a soundness bug, and the spec does not define reveal output.

Systemic? Yes. Fixes:
1. New oracle in `rules.py`/`kb.py`: parse the line's own expectation comment (`# N: Revealed type is "..."` or `# revealed: ...`) and compare each tool's reveal after normalisation (strip `builtins.`, module prefix; mypy 2.4 prints `int`, old suites print `builtins.int`). Emit an "ORIGIN-ORACLE" evidence: "ty matches the test's expectation, mypy does not". Dismiss as DESIGN_DIVERGENCE only if the matching tool is not the one that came from the test source; otherwise keep for review. Use it to sort the review queue: findings where the origin tool does not match its own expectation (version skew or harvest breakage) are a separate bucket (e.g. 225 in this pattern).
2. Cascade rule: if a statement's argument name has a ty/mypy/pyright undefined-name diagnostic or a runtime NameError, set the case's reveal findings to `invalid_test` (mirrors `flagged_bindings`).
3. Pin the harvest (record commit SHAs of the ruff, mypy and typing clones in the harvest output header, and prefer the tags matching the installed tool versions).

## Pattern 3: reveal_mismatch, different (1012 findings, 107 "strong")

Verdict: DESIGN DIFFERENCE and KNOWN UPSTREAM (mypy#15182) for the constructor cluster; NEEDS MORE WORK for one sub-case. Confidence: medium.

Evidence:
- 95 of the 107 "strong" are "runtime value does NOT inhabit mypy's revealed type". `ty__call__constructor__35.py`: `__new__(cls) -> int` returning 42, plus `__init__(self, x: str)`.
  - mypy 2.4.0: error `Incompatible return type for "__new__" (returns "int", but must return a subtype of "ReturnsIntWithInit")  [misc]`, then reveals `ReturnsIntWithInit` plus `Missing positional argument "x"`.
  - ty: `int`, no `__init__` error. pyright: `int`. CPython: `42`.
  - So ty and pyright match runtime, mypy does not. The typing spec's constructor section says that when `__new__` returns something that is not an instance of the class, the checker should use that return type and skip `__init__` (I recalled this from the spec; I did not re-fetch it in this session).
  - Upstream: python/mypy#15182 "Honor return type of `__new__` even if not a subclass" is closed as completed (2026-05-27). mypy 2.4.0 still errors on the unrelated-type case, so either the fix covers only the subclass-returning case or it is not in 2.4.0. I did not verify which.
- Honest caveat: this is mypy being "wrong" by the spec's reading, but it is already tracked. It is not a ty finding, and it is a mypy deviation, not a ty bug.
- 10 + 10 of the "strong" have runtime value `None` (stub-bodied `def f(...): ...` in the fragment), which is blamed on both tools equally. Pure noise.
- `testMetaclassConflictingInstanceVars.py` L17 (`Foo.foo`), the example in the brief:
  - mypy: `int`; pyright: `int`; ty: `str`.
  - Runtime: `Foo.foo` raises AttributeError (declared-only). The "strong" evidence is that AttributeError, so it carries no signal for either tool.
  - Reduced sub-case (tested):
    ```python
    from typing import ClassVar
    class Meta(type):
        eggs: ClassVar[int] = 42
    class Foo(metaclass=Meta):
        eggs: str          # declared only; not in Foo.__dict__
    reveal_type(Foo.eggs)
    ```
    CPython: `Foo.eggs` is `42` (int), from the metaclass. mypy: `int`. ty: `str`. pyright: `str`. So ty and pyright both disagree with the runtime. No duplicate found in astral-sh/ty with body-text queries (hits were #384 "declared-only attributes are not accessible on instances", #2815, #1889; none match). The queries were not exhaustive.
  - Accused tool's side: a bare `eggs: str` in a class body is an instance-variable declaration and the spec does not say whether it shadows a metaclass attribute for class-object access. ty (and pyright) deliberately let declared instance variables be read from the class, because a decorator, `__init_subclass__` or a metaclass `__new__` could set them. Not a clear spec violation, so it is a design question worth asking, not filing as a bug.
- Origin check: 803 are ty-origin with ty matching its own expectation, 50 mypy-origin with mypy matching. Only 120 + 20 + 2 + 5 have the origin tool disagreeing with itself.

Proposals: add a KB entry `NEW-RETURNS-NON-SUBTYPE` (kind reveal_mismatch, mypy message `must return a subtype of`, `[misc]` on the `__new__` def, dismissal KNOWN_UPSTREAM, url mypy#15182, requires pyright agrees with ty). Add `known_upstream.json` `prior_stances` entry `MYPY-15182` (stance `open`/`duplicate-of`, kinds `["reveal_mismatch","only_mypy"]`, source regex `def __new__\(.*\) -> (?!Self|"?\w*"?:)`). Drop probe evidence whose runtime value is `None` when the callee body is only `pass`/`...`/docstring.

## Pattern 4: runtime_miss (55 findings, 55 "strong")

Verdict: HARNESS NOISE. A few KNOWN LIMITATIONS. No clean false negative found. Confidence: medium-high.

Census (/tmp/an4.py, innermost enclosing statement of the traceback line, plus where the tools reported):
- 13 enum classes (`ty__enums__20..24, 30, 31, 51..53, 74`): the traceback blames the `class` header line (EnumType runs member `__init__` at class creation), but the checkers reported on a member line inside the body. E.g. `ty__enums__20.py`: ty reports `L12 invalid-assignment: Enum member SATURN is incompatible with __init__`; pyright reports `L12 Arguments missing for parameters mass, radius`; mypy silent. CPython raises TypeError at L5. The report anchors at L5, so it shows "nobody flagged". It is an anchoring artifact: `discrepancy.py:120` compares by header-only statement anchor (see `anchors.py`, `end` is "last line of the header" for compound statements). In 17 of 55 the span of the blamed compound statement contains a ty/pyright/mypy diagnostic.
- Test scaffolding: 16 TypeError `... 'NoneType' object is not callable`, `iter() returned non-iterator of type NoneType`, `can't multiply sequence by non-int of type NoneType` come from fragments whose functions have `pass` bodies and return `None` (`testFunctionReturningGenericFunction`, `testNestedDecorators`, `testMultipleAssignmentFromAnyIterable`).
- 13 NameError: names declared-only or never defined in the fragment (`class B(Unknown):  # type: ignore` in `testCorrectConstructorTypeWithAnyFallback.py` is deliberately undefined; `g('x')` etc.).
- 5-6 lines carry `# type: ignore` (`x() # type: ignore`, `42 + "no" # type: ignore`, `Bad = A[int] # type: ignore`). The checkers correctly honour the suppression, so "nobody flagged" is expected.
- Cascades: `ty__call__functools_partial__23.py` has `partial(f, 1, 2, 3)` flagged by all three at L8 (too many arguments); the runtime error at the later `p()` is just that earlier error, which was reported.
- Known limitations: `ty__call__functools_partial__72/73/76.py` have `# TODO: should error ... once constructor signatures are merged` right in the source. ty and pyright are silent, mypy reports "Too many arguments for MyClass" on the `partial(...)` line. That one is a genuine ty and pyright false negative, documented upstream in the mdtest TODO (KNOWN LIMITATION). `ty__call__replace__9.py`: the mdtest expects `unresolved-attribute` for `Model.__replace__` on a `dataclass_transform` class; CPython raises AttributeError; ty 0.0.84, mypy and pyright are all silent. This looks like ty behind its own mdtest (version skew, fixed on main) or a real ty miss at 0.0.84. Not verified (no newer ty available here). Related search hits: ty#4095 (closed, `copy.replace` and missing `__replace__`) and ty#2666; neither matches.
- `conformance__constructors_call_new.py` L100 (`return super().__new__(cls, *args, **kwargs)`): `object.__new__` rejects extra arguments at runtime; the test forwards `*args`, which no checker can evaluate. The 16 TypeError rows with no diagnostic in span are mostly this kind.

Accused tool's side: for a runtime error to be a checker false negative it must come from a type error that the checker is able to know about. `*args` forwarding, `type: ignore`, `pass`-bodied stubs and unassigned declarations are all things where the checkers are right to stay silent.

Systemic? Yes. Fixes:
1. In `discrepancy.py` compare the runtime frame against the full compound-statement span (`ast.stmt.lineno..end_lineno`), or: if any checker has a diagnostic inside the blamed compound statement's span, do not create `RUNTIME_MISS`.
2. Skip `RUNTIME_MISS` when the line has `# type: ignore` / `# pyright: ignore`, or when the same statement text appears with `# E:`/`# error:` in the source (test-expected errors).
3. Cascade rule: skip when an earlier statement that the raising statement depends on already has a checker problem (reuse `flagged_bindings`).
4. KB rule `MDTEST-TODO`: if the source has a `# TODO:` line mentioning "should error" within 3 lines above, dismiss as KNOWN_LIMITATION.
5. Treat functions whose body is only `pass`/`...` and that have a non-None return annotation as "stub": do not count NoneType errors or probe values from calls to them.

## Pattern 5: reveal_mismatch, uncomparable (733 findings, 23 "strong")

Verdict: DESIGN DIFFERENCE (mypy joins, ty and pyright union) + HARNESS NOISE. Confidence: high.

Evidence (`testNewReturnTypeCallableJoins.py` L20-23, all tools run):
- mypy: `def () -> Foo`, `def () -> Base`. ty: `<class 'A'> | <class 'Foo'>`. pyright: `type[A] | type[Foo]`. All three agree there is no error to report beyond the stub body (`empty-body`).
- This is a join versus a union. The mypy test is about the `__new__`-returns-subclass callable join, which mypy implements and ty and pyright do not model. The reveal text differs in callable vs class syntax (`def () -> X` vs `<class 'X'>`), which is why relation is `uncomparable`.
- "Strong" evidence is `runtime value 'None' ... does NOT inhabit ty's revealed type type[A] | type[Foo]`. `join` is `def join(x: T, y: T) -> T: ...`, so it returns `None` at runtime. Pure noise. Across the 23 strong: 4 `None`-valued, 6 `_GenericAlias` vs `type[C[int]]` (runtime `typing._GenericAlias` of `C[int]` is a valid inhabitant of `type[C[int]]`; the probe is too literal), 6 on a function value vs `int` from an overload/exception test, 7 NameError.
- Origin check: 529 ty-origin where ty matches its own expectation, 79 mypy-origin where mypy matches; only 30 + 18 + 2 mixed.

Accused tool's side (ty): joins of unrelated callables are ill-defined in the spec. The spec only defines union and `type[A | B]` equivalence. ty returning the union is the more precise answer and is assignable to mypy's join (mypy's result is a supertype).

Fixes: 
1. Extend `kb.py::m_join_vs_union` (`is_join_vs_union` in typenorm.py currently rejects gradual or callable shapes) to callable joins: mypy `def () -> X` against ty/pyright union of `type[...]`/`<class>` where X is a common base. Requires pyright to agree with ty.
2. `inhabits()` in `rules.py`: treat `typing._GenericAlias` and `types.GenericAlias` as inhabiting `type[C[...]]`; skip stub-bodied results (same as pattern 4, item 5).

## Cross-cutting recommendations (priority order)

1. Stop blaming the silent tool when the runtime exception is the thing the reporting tool reported (patterns 1, 2, 4). This one change removes most of the 167 + 133 + 55 + 23 "strong bug evidence" flags.
2. Use the harvested expectation comments as an origin oracle (patterns 2, 3, 5) and put "origin tool disagrees with its own expectation" in a separate bucket (version skew). Pin harvest clones to the versions in use.
3. Handle stub-bodied functions and `None` probe values.
4. Anchor `runtime_miss` on compound statement spans; honour `type: ignore`.
5. Real, small leads worth a human look (none filed): (a) metaclass attribute vs declared-only attribute (`Foo.eggs`: ty and pyright say `str`, runtime and mypy say `int`); (b) `ty__call__replace__9.py` (`Model.__replace__` on a `dataclass_transform` class, runtime AttributeError, all tools silent, ty's own mdtest expects an error).

## How I triaged this (repeatable for patterns 6+)

```bash
cd /home/micropp/Documents/kiro_sa
# 1. patterns, members, evidence text, report path
.venv/bin/typediff triage runs/day1/harvest-out --top 30 --examples 3 --details > /tmp/t.txt
# 2. source of a member (file name is in the triage line; programs live under seeds/harvested/<area>/)
find seeds/harvested -name 'mypy__check_classes__testNewReturnTypeCallableJoins.py'
# 3. reproduce on a /tmp copy with all four tools (target 3.13)
mkdir -p /tmp/tri && cp <program> /tmp/tri/p.py && cd /tmp/tri
V=/home/micropp/Documents/kiro_sa/.venv/bin
$V/ty check --python-version 3.13 p.py --output-format concise
$V/mypy --python-version 3.13 --show-column-numbers p.py
$V/pyright --pythonversion 3.13 p.py
$V/python p.py            # NameError: reveal_type is expected; the harness injects it
# 4. whole-pattern census: load runs/day1/harvest-out/2*.json
#    keys: findings[].evidence[], discrepancies[] (kind, reveal_relation, anchor, statement, ty[], mypy[]),
#          diagnostics{mypy,ty,pyright}, runtime{exc_type,exc_message,exc_line,frames,probes}, source, notes (origin=)
#    my scripts: /tmp/analysis.py (patterns 1-5), /tmp/an2.py (cascades), /tmp/an3.py (origin oracle), /tmp/an4.py (pattern 4), /tmp/an5.py (inhabit evidence)
# 5. read the classification code
sed -n 24,45p typediff/typenorm.py; grep -n "blame" typediff/rules.py
# 6. duplicates (body text): web_fetch https://api.github.com/search/issues?q=repo:astral-sh/ty+<terms>
#    and repo:python/mypy; then read known_upstream.json
```

Note: in my session the shell tool did not echo output, so I redirected output to files in /tmp and read those. Not needed in a normal terminal.

## What I could not verify

- No newer ty than 0.0.84 was available, so version-skew claims (pattern 2 `ty__bidirectional__41`, pattern 4 `ty__call__replace__9`) are inferred from the mdtest expectation, not reproduced.
- mypy#15182: I did not check whether its closing fix is in mypy 2.4.0 or covers only the subclass case.
- The spec wording on `__new__` returning a non-instance was recalled, not re-fetched this session. Quote it before citing it in an issue.
- Duplicate searches were lexical GitHub API queries; one extra batch of searches was not run because a command was rejected. They are not exhaustive.
- Counts in the census are from my own AST heuristics (e.g. "annotation-only" vs "forward reference"), roughly accurate (+/- a few percent), not exact.
