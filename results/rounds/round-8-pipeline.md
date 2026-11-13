# Day 8, phase 1: pipeline improvements

> Paths written as `[campaign working file]`, `[run output]` or `[agent working file]` point to scratch files of the original campaign that are not part of this repository.

Branch [campaign working file] (from [campaign working file]), local only. Nothing was pushed; no issue, PR or comment was written on GitHub (only read-only `gh search issues`, `gh issue view`, `gh pr view`, `gh release list`). Pins unchanged: mypy 2.4.0, ty 0.0.97, pyright 1.1.414, CPython 3.13.16. ty 0.0.98 is the newest release (2026-11-05); it was not used in this phase because no new draft was verified.

Every number below was read from a file in [campaign working file] (`pytest.out`, `kb-selftest.out`, `check_hits.out`, `replay-*.out`, `replay-*-diff.txt`, `stats-*.txt`, [campaign working file], `results/`). Scripts and raw tool output are in the same directory (`scripts/`, `results/`, `repro/`, `search/`).

## 0. Result in numbers

| | Before | After |
|---|---|---|
| `pytest tests -q` | 498 passed | **580 passed** (498 + 82 in `tests/test_round8_pipeline.py`) |
| `typediff kb-selftest` | 20 PASS, 0 FAIL | 20 PASS, 0 FAIL |
| `check_hits.py 0.80` | | 42 files; 0 with problems (no parent changed) |
| Day-7 judge run (224 programs), live findings | 107 (88 without `only_pyright`; 68 programs with a live finding) | **75** (63 without `only_pyright`; 48 programs) |
| Day-7 run, dismissed | 75 | 107 |
| Day-6 run (250 programs, replay with `--pyright-only`), live | 231 (194 without `only_pyright`) | **199** (174 without) |
| ParamSpec `self_annotated_dunder_call` family, live | Day 7: 16; Day 6: 21 | 0; 0 |
| `only_pyright` with `runtime_supports` | Day 7: 0 of 19; Day 6: 0 of 37 | 1 of 19; 5 of 37 |

Replay method: `kbloop_replay.py` over the saved reports, `--verify-sample 30` re-runs 30 programs in full and compares tier, dismissal and `decided_by`: 30/30 identical in all four replays (Day 7 KB-only, Day 7 with `--rerun-runtime`, Day 6, Day 6 with `--rerun-runtime`). Day-7 KB-only replay changed 32 of 182 findings (DISPLAY-EQUIVALENT 16, CALLABLE-SELF-RECEIVER 12, CALLABLE-SELF-ATTR-STORE 2, PYRIGHT-11382 1, TY-2792-READONLY 1); the CPython re-run changed 0 more. Day-6 replay changed 31 of 358 findings (CALLABLE-SELF-RECEIVER 14, DISPLAY-EQUIVALENT 7, CALLABLE-SELF-ATTR-STORE 5, MYPY-2455 4, TY-3666 1) and removed one discrepancy (the `runtime_miss`, section 3.3). Every closed finding of Days 6 and 7 (63) and of the controls (Days 3 to 5: 12 closures) was read as a diff row with statement and origin (`replay-*-diff.txt`). For the display closures (all days) I also read the three reveal texts ([campaign working file], [campaign working file]); for the four Hashable closures and the Day-6 `reveal_type(g)` rows I read the program lines and pyright's message ([campaign working file]). The 9 Day-5 control closures are all mutants of the ParamSpec parent; I did not read those programs in full.

## 1. (a) The ParamSpec `self_annotated_dunder_call` family

Parent: [run output], the team-filed repro of ty#4899 (`__init__(self: Callable[P, T], *args: P.args, **kwargs: P.kwargs)` plus a `__call__` that also takes `Callable[P, T]` and an extra `x: int`; ty aborts or panics). The Day-7 mutants dropped `x: int`, which the issue says avoids the crash ("Without the extra `x: int` parameter ... ty finishes normally"), so they produce ordinary diagnostics instead. Day 7: 7 mutants, 5 with live findings (16 findings), the other 2 drifted into unrelated decorator programs. Day 6 (replay with `--pyright-only`): 21 live findings.

Experiments on the pinned tools ([campaign working file], output [campaign working file]):

* e1 `__init__(self: Callable[[int], None], x)` with `self.x = x`: mypy reports the declaration (`The erased type of self "def (int)" is not a supertype of its class`), pyright reports the declaration and `Cannot assign to attribute "x" for class "FunctionType"`, ty reports `unresolved-attribute` on the store and the call `A(1)`.
* e2 same store in an ordinary method of a class that really has `__call__`: mypy silent, ty and pyright reject the store.
* e3 only `@classmethod def __call__(cls: Callable[P, T], *args: P.args, **kwargs: P.kwargs)`: ty and pyright both reject `User.__call__(1)` (ty "expected 1, got 2", pyright "Expected 0 positional arguments"), mypy accepts. So ty binds `cls` to the class's constructor signature. With the `__init__` of the parent that signature contains `P@__init__`, which is where `Expected P@__init__.args` comes from. It is not a scope leak of `__call__`'s own `P`.
* e4 `def run(self: Callable[[int], int], ...)` and `def run(self: int)`: mypy and pyright reject the declaration, **ty reports nothing**. Open ty#3666 "new rule - enforce that `self` parameter on methods is a supertype of its class" is this.

Classification of the 16 (Day 7) and 21 (Day 6) live findings:

| Class | Day 7 | Day 6 | Verdict | KB |
|---|---|---|---|---|
| `self.args = args` on a `Callable`-annotated `self`: ty `unresolved-attribute`, pyright `reportFunctionMemberAccess`, mypy silent | 2 | 5 | design difference (ty and pyright check the store against the declared function type; mypy defines the attribute from the store) | `CALLABLE-SELF-ATTR-STORE` (DESIGN_DIVERGENCE) |
| `def` line, instantiation, `User.__call__(..)`, `u(..)`, a parameter or variable of the class, reveals of results derived from them; all three checkers answer differently | 12 | 14 | not judgeable: the declaration is ill-formed (not a supertype of the class), each checker solves the ParamSpec against something else | `CALLABLE-SELF-RECEIVER` (SPEC_AMBIGUITY) |
| mypy and pyright reject the `self` annotation, ty accepts it | 0 | 1 | duplicate of ty#3666 (open) | `UPSTREAM-TY-3666` (DUPLICATE) |
| `reveal_type(user.args)`: mypy `P.args`, ty and pyright `P@__init__.args`; `Runner[[a: int], str]` vs `Runner[(a: int), str]` | 2 | 1 | display noise | `DISPLAY-EQUIVALENT` (NOISE) |
| ty crash on the parent and the `x: int` variants | 0 | 0 | already ty#4899 (entry `TY-4899`); the parent still panics, rc 101 ([campaign working file]) | existing crash entry |

No finding of the family is a new bug, so no draft was written. The one open question is whether ty should accept `User.__call__(1)` when the receiver's ParamSpec is the constructor's own; with an ill-formed declaration there is no reference answer, and ty#2926 (ParamSpec `*args`/`**kwargs` required) is a different case. Not verified: the family on a playground; the effect of ty 0.0.98.

## 2. (b) Known duplicates that stayed live

| Id | Entry | Kind | Shape | Seen on |
|---|---|---|---|---|
| D7-3 | `TY-2792-READONLY` and `TY-2792` (matcher extended) | only_mypy, reveal_mismatch | a store into a data-descriptor attribute of the program (`t.bumped = 3`) runs `__set__`, which assigns `obj.base`; it resets nothing, exactly like a mutating method call (ty#2792 body: any call that changes the attribute) | Day 7 `f26e2d99be2a`; fresh run of `c3.py`, `c3r.py` (via descriptor and via method both closed) |
| D7-4 | `PYRIGHT-11382` | only_pyright | `assert_type(Owner.name, D)` fails with `D \| int`: class-level `name = D()` with `D.__set__`, a method assigns `self.name` | Day 7 `265d08238d20`; fresh run of `p1.py` |
| H1 | `MYPY-2455` and `TY-4941` | only_pyright | a program class whose only reason for being unhashable is `__eq__` without `__hash__` (own or inherited, no decorators, no external bases) passed to a `Hashable` parameter; pyright rejects, mypy and ty accept | Day 6: 4 findings; fresh run of `h1.py` and `d4v_eq_no_hash_hashable.py` |
| (new) | `TY-3666` | only_mypy | mypy `The erased type of self "..." is not a supertype of its class`, ty silent | Day 6: 1; Day 5 control: 3 |

ty#4941 ("class that defines `__eq__` without `__hash__` is accepted where `Hashable` is required") was filed by us on 2026-11-05 (draft 4). So the `only_pyright` Hashable finding is a duplicate on both sides: mypy half python/mypy#2455 (open since 2016; #18622 open; PR #19168 open), ty half ty#4941. Both entries share one matcher and both appear in `kb_hits`.

Single-tool findings: before Day 8 an `only_mypy` or `only_ty` finding could be closed by `known_upstream.json` entries, an `only_pyright` finding could not (the entry matcher read mypy and ty diagnostics, and no entry listed the kind). Now an entry with `"kind": "only_pyright"` is matched against pyright's diagnostics; `docs/design.md` and the `_doc` field describe it. The two `silent_tool` conventions are unchanged.

Controls (all in `tests/test_round8_pipeline.py`, each must stay live): a descriptor whose `__set__` assigns nothing on the owner, a non-descriptor store, a non-data descriptor, a store before the narrowing, no read after the store, receiver rebound, store on another object, a direct store that resets the narrowing; Hashable: own `__hash__`, `__hash__` assigned in the body, external base, a union with a hashable member, a type that is no program class, another parameter type, another pyright rule, another kind, a dataclass; descriptor: never assigned on the instance, non-data descriptor, instance access, message without a union or without the descriptor class, other rule, other kind.

## 3. (c) Runtime-evidence weak spots

### 3.1 `only_pyright` never had `runtime_supports`

Cause: the harness reported only the uncaught exception (`exc_*`, `frames`). Generated programs follow the prompt rule "guard the `# expect-error` line so it does not abort the rest of the program (try/except TypeError)". The exception was raised and handled, so the harness said "success" and `pyright_runtime_relation` could only answer "contradicts". The 0.7 weighting itself was not the problem.

Fix: `runtime_harness.py` records every exception that passes through a frame of the program (`raised`: line, type, message; deduplicated by line and type, capped at 200). `RuntimeResult.raised` carries it (also through `replay.py` and `runtime_from_json`). `pyright_runtime_relation` returns `supports` when a type-related exception (`classify_exception` strong) was raised on a line of the statement and handled. The evidence text says "handled it (try/except)". Replay of the saved reports needs `kbloop_replay.py --rerun-runtime` (refreshes only the CPython result).

Result ([campaign working file]): Day 7 19 contradicts -> 18 contradicts + 1 supports (`desc.__delete__(obj, 1)  # expect-error`, decorated-descriptor family); Day 6 37 -> 32 + 5 (two are the Hashable rows now closed by `MYPY-2455`, three are unhashable set or dict displays, `{item}` and `{key: 1}` in a `d4p_inheritance_hash_none_from_eq` mutant and `len({p})` in a `d3p_inheritance_mro_hash_none_from_eq` mutant). Priority 0.7 ranks these above plain reveal differences (0.5 to 0.6) and below `runtime_miss` (0.8). I did not check the four that stay live against the trackers. Controls: exception raised on another line, `StopIteration`, `ZeroDivisionError`, no exception recorded.

### 3.2 `...` read as a variadic tuple

mypy prints `...` for the recursive occurrence inside a recursive alias (`tuple[str, ...]` for `tuple[str, Left]`). `rules.attach_runtime_evidence` compared the runtime value with that text and gave strong evidence against mypy. Now, when the program defines a recursive alias (`recursive_aliases`: PEP 695 `type`, `TypeAlias`, direct or through other aliases, names in string forward references count) and mypy's reveal contains `...`, the evidence is neutral with a note. Baseline code on [run output]: `RUNTIME/strong/bug` on D1; after: weak/neutral on all three rows ([campaign working file], [campaign working file]). Limit: a real `tuple[int, ...]` reveal in a program that also has a recursive alias loses its probe comparison.

### 3.3 `runtime_miss` on the wrong frame

`d3p_generics_callable_attr_contravariant__mut0_0bac40f6` (Day 6): all three checkers reject the marked line 34 `use(hf)  # expect-error`; the AttributeError comes from the lambda called by `hf.fire(1.5)` on line 35, a frame no checker flags. `find_discrepancies` now skips the `runtime_miss` when some line marked `# expect-error` is flagged by a checker, was executed, and comes before the outermost program frame of the traceback. Controls: marker not flagged, marker never executed, no marker, marker after the failing statement. Baseline code: `runtime_miss` live with strong evidence; after: no discrepancy ([campaign working file]). Limit: a real `runtime_miss` later in a program with a flagged, executed marker is also skipped.

## 4. (d) Display noise: `DISPLAY-EQUIVALENT`

`typediff/display.py` rewrites exactly the conventions that differ for the same type, then compares strings: scope tags (`P@__init__.args`, `T@f`), the module prefix, mypy `def (..)` callables (no `-> None`, hidden default values, `*P.args, **P.kwargs`), ty's `, /`, `[**P, R]` headers and parenthesised callable returns, ParamSpec arguments `[[a: int], str]` against `[(a: int), str]`, and TypedDict structure against the class name. After the rewrite mypy and ty must be equal, and pyright (if it revealed anything) must equal ty without the generic header. Day-7 closures (16): TypedDict 8, callables 4 (`def (float)`, `tuple[def (list[int]), ...]`, two ParamSpec-generic functions), `Child.__init__` with defaults 2, `P.args`/`P.kwargs` 2. Controls: different parameter name, type, default presence, return type, positional-only against named, different ParamSpec, TypedDict of another name, pyright disagreeing, a plain difference.

Day-7 no-hit-area items that are NOT display noise and stay live: recursive-alias reveals where mypy keeps the declared union (`int | list[...]` against ty's narrowed `list[int | list[Nested]]`, mypy#2008 is the binder issue, not a spelling), a class-level property reveal (mypy `Overload(def (self: Temp) -> float)`, ty and pyright `property`), star-pattern `rest` types, `__post_init__` overrides. The remaining 75 live findings are listed by `kbloop_stats.py`/`typediff triage` in the usual way.

## 5. Files

`typediff/display.py` (new); `typediff/kb.py` (descriptor stores in `_stale_attr_context`; matchers `eq_without_hash_argument`, `descriptor_set_on_instance`; entries `DISPLAY-EQUIVALENT`, `CALLABLE-SELF-ATTR-STORE`, `CALLABLE-SELF-RECEIVER`; `only_pyright` in the upstream-entry matcher); `typediff/data/known_upstream.json` (`MYPY-2455`, `TY-4941`, `PYRIGHT-11382`, `TY-3666`, note on `TY-2792-READONLY`); `typediff/{runtime_harness,models,parsers,replay,discrepancy,rules}.py`; `tests/test_round8_pipeline.py` (new), `tests/test_upstream_round3.py` (allowed kinds); `docs/design.md`.

## 6. Not verified, open points

* No playground (ty, mypy, pyright) was used; ty 0.0.98 was not run on the new shapes.
* `CALLABLE-SELF-RECEIVER` is broad on purpose (the statement touches a class with a `Callable`-annotated receiver). A ty bug inside such a class, for example a crash, is not hidden (crash findings are separate and `TY-4899` is untouched), but a wrong ty answer at a call site would be. A CPython type error at the statement keeps the finding in review (`runtime_override=True`, tested).
* The mypy/ty/pyright disagreement about unhashable set and dict displays (`{item}`, `{key: 1}`) is not in the KB; I did not search the trackers for it in this phase (the Day-4 log names ty#3781).
* Parents: `d3p_paramspec_self_annotated_dunder_call` now yields only dismissed findings except for the ty#4899 crash; the three hash parents (`d4v_eq_no_hash_hashable`, `d4p_inheritance_hash_none_from_eq`, `d3p_inheritance_mro_hash_none_from_eq`) are partly closed. Retiring them is a phase-2 decision (Day 7 retired parents whose mutants gave no live finding); [run output] was not touched.
* `results/rounds/round-7-report.md` has an uncommitted edit that is not mine (`se=0-9rches` inside the word "searches" in section 7). I left it and did not commit it.
