# Day 8 verification (Phase 6)

Date: 2026-11-06. Branch `campaign/day8-p2`, local only. Nothing was pushed. No issue, PR or comment was written on GitHub (`gh` calls were `search issues`, `search prs`, `issue view`, `pr view`, `release list`; web fetch of the typing spec). No pin was changed. Evidence: `campaign/day8/phase6/` (`repro/` programs, `results/` raw tool output, `search/` gh output, `scripts/`). Shell note: fish garbles stdout, every command ran as `bash script.sh > file 2>&1` and the file was read.

Input: the strong-evidence findings of `campaign/day8-triage.txt` (13 findings in 11 programs, Phase 5 item 40), the ParamSpec `self_annotated_dunder_call` reductions e1 to e4 of Phase 1, class F ("mypy rejects an overloaded `__post_init__`", an unverified lead of Phases 2 and 5), the `only_pyright` `runtime_supports` row `seed-8af1b011a91f` (evidence text not read in Phase 4), and the live mypy `misc` row of `d3p_callables_self_call_attr__mut0_5445453a`.

## 1. Tools

| Tool | Version used | Note |
|---|---|---|
| CPython | 3.13.16 (`.venv`) | |
| ty | 0.0.97 (`.venv`, the pin), **0.0.98** (`/tmp/d7pd/ty98`, verification only) | 0.0.98 is the newest release (PyPI 2026-11-05 17:39 UTC; `gh release list`: Latest). `/tmp/d3v-latest/bin/ty` is 0.0.97, so it was not run again |
| mypy | 2.4.0 (`.venv`, the pin), 2.4.1 (`/tmp/d3v-latest`, PyPI latest, 2026-10-28), master 2.5.0+dev.879da562 (`/tmp/d3v-master`) | |
| pyright | 1.1.414 (`.venv`) | latest on PyPI (2026-09-10), npm and GitHub releases. Not tested: `main`, the branch of PR #11965 |

`results/versions.txt`, `results/latest-releases.txt`. Every program ran through `scripts/runall.sh` (CPython, ty x2, mypy x3, pyright; exit codes printed); output in `results/<id>.txt`. Verbatim copies of the 15 Day-8 programs are `repro/p_*.py`; reductions are `repro/c*.py`.

## 2. Candidates and verdicts

| Id | Candidate | Verdict | Evidence in short |
|---|---|---|---|
| D8-1 | ty reveals the old value in `except` after a nested unpacking target failed half-way (`partial_unpack_except_ty` mutants, 4 programs, 4 strong findings) | **STILL-BUG-NEW**, same root cause as unfiled draft 6, no new draft | CPython `'bad'`; ty 0.0.97/0.0.98 `Literal[1]` / `Literal[0]`; mypy `int \| str`; pyright `Literal[1]`. New shapes: star target, attribute chain, `match` in the handler |
| D8-2 | ty reveals `Never` for a read-only property and then skips the assignment error (`d4p_descriptors_readonly_prop_never` mutants, 2 programs, 3 strong findings) | **DUPLICATE** of astral-sh/ty#2792 (open) | `assert c.base == 4; c.bump(); assert c.base == 5` is `Never` for ty, `int` for mypy and pyright. Related: ty#4345 (open), ty#4880 (closed as duplicate of #4345) |
| D8-3 | ty `invalid-return-type` for `return norm(v)` (`rsv_overloads_d41747bd` mutants, 2 programs, 2 strong findings) | **NOT-A-BUG** | The `T -> T` overload is the only one that accepts the whole union, so spec step 2 picks it and expansion (step 3) does not run. ty and pyright follow the spec; mypy does union math first on purpose. The overload set is unsound by itself |
| D8-4 | mypy reveals `str`, ty and pyright `int`, for `parse(k, '9')` after `k: str = 'int'` (`overloads/gen12_a368580c`, 1 strong finding against mypy) | **NOT-A-BUG** | mypy's binder erases the literal when it narrows on assignment (comment in `binder.py`); ty and pyright keep `Literal['int']`. The overloads overlap with incompatible returns, mypy and pyright say so |
| D8-5 | ty accepts `x.add(Node())` for `def add(self, c: 'Self')` on a subclass (`self_param_inherited__mut0_3a63c673`, 2 strong findings) | **DUPLICATE** of astral-sh/ty#4656 (closed, intended) | The Day-4 report, written as `'Self'`. Also ty#4849 (closed, same answer), ty#4673 (display, closed) |
| D8-6 | pyright `RangeError` on a decorated descriptor `__get__` (`d3p_descriptors_decorated_get__mut0_655e135a`, 1 strong crash) | **STILL-BUG-NEW**, same root cause as unfiled draft 7, no new draft | pyright 1.1.414 exit 2 on the program and on the draft-7 program; ty and mypy report the `@deco` call and do not crash |
| D8-7 | mypy `[override]` on an overload item of `__post_init__` (class F, 6 findings in the triage, 0 strong) | **STILL-BUG-NEW** (mypy; draft 8) | Reduced to 14 lines. Error on the `str` item although the `int` item takes the `InitVar` type. An ordinary override with one compatible item is accepted by the same mypy |
| D8-8 | only pyright rejects `Desc.__delete__(Desc(), h, 1)` behind an untyped class-body decorator (`runtime_supports` row, CPython raises `TypeError`) | **NOT-A-BUG** (ty and mypy) | ty does not infer return types by default (ty#4739). With `analysis.return-type-inference = "always"` ty reports `too-many-positional-arguments`. mypy gives an unannotated decorator the type `Any` |
| D8-9 | ParamSpec `self_annotated_dunder_call` family, reductions e1 to e4 (Phase 1) | **no new bug**; e4 **DUPLICATE** of ty#3666 (open) | e1 all three reject, e2 and e3 design differences, e4 mypy and pyright reject `self: int`, ty accepts |

STILL-BUG-NEW drafts appended to `campaign/day3-issue-drafts.md`: **1** (draft 8, mypy). D8-1 and D8-6 are listed in a "Day 8 status" note at the end of that file instead of getting their own drafts, because each is a second set of programs for an existing unfiled draft (one issue per root cause). None is filed.

## 3. Details

### D8-1 partial unpack in `try` (ty)

`repro/c1.py` (star target) and `repro/c1d6.py` (draft 6 shape):

```py
def f(pair: tuple[int, ...]) -> None:
    value: int | str = 1
    try:
        value, (a, *b, c) = "bad", pair
    except ValueError:
        reveal_type(value)
        print(repr(value))
f((1,))
```

| Tool | `reveal_type(value)` |
|---|---|
| CPython 3.13.16 | `'bad'` |
| ty 0.0.97, 0.0.98 | `Literal[1]` |
| mypy 2.4.0, 2.4.1, master | `int \| str` |
| pyright 1.1.414 | `Literal[1]` |

The four verbatim programs (`p_tuples_*`) give the same on every version: `cfdf17ba` `Literal[0]`, `d873ebcb`, `cdecbcd7`, `aa1f1387` `Literal[1]`; mypy `int | str`. Duplicate search: ty/ruff/pyright/mypy term sets (`unpacking except`, `except narrowing`, `nested unpacking`, `partial assignment`, `try except`, `except clause`, `try block`, `exception handler`, `checkpoint`, `starred`, `unpacking`; ruff PRs `exception flow`, `checkpoints`, `try block`, `assignment target`). Nothing describes a partially bound nested target. Related, as on Day 7: ruff#27471 (merged), #27703, #27817, #29750 (merged 2026-10-27, "Reuse exception checkpoints when a new place is read"), ty#225, ty#233 (open, `finally`), ty#4293 (closed). The author listing of the account that filed ty#4933, #4934, #4941 shows no unpacking issue, so draft 6 is still unfiled. ty 0.0.98 (2026-11-05) still has the result, so the checkpoint work in #29750 did not cover it.

### D8-2 `Never` after contradicting asserts (ty)

`repro/c2.py`: `assert c.base == 4`, `c.bump()`, `assert c.base == 5`, `reveal_type(c.readonly)` gives `Never` on ty 0.0.97/0.0.98, `int` on mypy (3 versions) and pyright. In `p_readonly_f116e46b` and `p_readonly_17c399aa` mypy and pyright report the write to the read-only property; ty reports nothing because the code after the contradiction is `Never`. Same mechanism as the retained parent `d4v_ty_attr_eq_narrow_unreachable` and as Day-7 D7-3. ty#2792 (open): carljm, every checker narrows attributes unsoundly after a mutating call; ty may drop the narrowing for direct method calls on `self`. In the second program the mutation is a call to a function (`poke(c, 10)`), not a direct method call, so it would not be covered even by that fix. Searches: `stale narrowing`, `attribute narrowing`, `narrowing invalidate`, `mutating method`, `read-only property`, `unreachable assert`, `narrowing __dict__`, `Never reveal`, ruff PRs `attribute narrowing`, `method call narrowing`.

### D8-3 overload with a catch-all `T` and a union argument

`repro/c3.py`: overloads `Literal['a','b'] -> Literal['A','B']`, `str -> str`, `T -> T`, call with `Literal['a','b'] | int`.

| Tool | `reveal_type(norm(v))` |
|---|---|
| ty 0.0.97, 0.0.98 | `Literal["a", "b"] \| int` |
| pyright | `int \| str` |
| mypy 2.4.0, 2.4.1, master | `Literal['A'] \| Literal['B'] \| int` |

Control `repro/c3ctl.py` (the `T` overload replaced by `int -> int`): ty `Literal["A", "B"] | int`, pyright `int | Literal['A', 'B']`, mypy as before, so ty expands unions when no overload takes the whole union. The typing spec (overload call evaluation, fetched 2026-11-06): step 2 evaluates each overload without expansion, "if only one overload evaluates without error, it is the winning match"; step 3 expands unions only if all overloads fail. ty and pyright follow that. mypy master `checkexpr.py` `check_overload_call` runs union math first whenever an argument is a real union and then keeps the more precise of the two results, citing mypy#4063. Both programs also make pyright report the `return r`, and the `T -> T` overload is unsound (`str.upper()` gives `'A'` for `'a'`, which is outside `T = Literal['a','b'] | int`). mypy#18321 (closed) shows mypy conforming in a case where both orders agree. Searches: `overload union`, `union expansion`, `overload typevar`, `union math`, `overload expansion`, `overload spec` on ty, mypy, pyright, python/typing. I did not look for or file a conformance issue for mypy's order; it is deliberate and commented in the source.

### D8-4 mypy keeps `str` after `k: str = 'int'`

`repro/c4.py`: `reveal_type(k)` is `Literal["int"]` (ty, pyright) and `str` (mypy); `parse(k)` is `int` (ty, pyright, CPython `<class 'int'>`) and `str` (mypy). `mypy/binder.py` `assign_type` starts with `remove_instance_last_known_values(type)` and a comment that a non-final target cannot hold a literal. All three checkers except ty report the overlapping overloads (`overload-overlap`, `reportOverlappingOverload`); ty has no such check (KB `TY-CHECK-MISSING-JUDGE-MYPY`). Searches on python/mypy (`narrowing assignment declared`, `declared type narrowing`, `initial assignment narrowing`, `overload Literal variable`, `narrow on assignment`) found nothing specific. Design difference.

### D8-5 `'Self'` on an inherited method (ty)

`repro/c5.py` and the verbatim program: ty reveals `bound method Leaf.add(c: Leaf) -> Leaf` and accepts `x.add(Node())`, `x.add(c=Node())`, `Leaf.add(Leaf(), Node())`; mypy (3 versions) and pyright reject all three. The quoted form is the same program as ty#4656 (filed by the account that files our drafts, closed 2026-10-05): carljm, intended, `Self` is a typevar bounded by the defining class. ty#4849 (closed 2026-10-28) got the same answer.

### D8-6 pyright `RangeError`

`repro/c6.py` is the draft-7 program, `repro/c6b.py` and the verbatim `p_pyright_655e135a` use annotated `__get__` and the direct call `C.__get__(C(), None, C)`. pyright 1.1.414: `RangeError: Maximum call stack size exceeded`, exit 2, frames `typeEvaluator.ts` `retainTypeAlias` / `typeUtils.ts` repeating, in all three. CPython prints `42`. ty and mypy (3 versions) report the `@deco` argument and do not crash. Draft 7 already lists the annotated variant and the direct call. State of the neighbours on 2026-11-06: issue #11961 and PR #11965 are still open (the PR only guards constructor validation; a comment of 2026-11-04 reports a non-terminating constructor case), no pyright release after 1.1.414. Searches: `RangeError`, `Maximum call stack`, `retainTypeAlias`, `descriptor crash`, `__get__ decorator`, `descriptor recursion`, `stack overflow`, PRs `RangeError`, `call stack`, `descriptor recursion`, `infinite recursion`, `decorated descriptor`, `descriptor __get__`, `reportSelfClsParameterName`. No issue about a descriptor. Draft 7 is not filed (author listing).

### D8-7 mypy `__post_init__` overloads

`repro/c7.py` (the draft program): mypy 2.4.0, 2.4.1 and master `test_bug.py:12: error: Argument 2 of "__post_init__" is incompatible with supertype "dataclass"; supertype defines the argument type as "int"  [override]` (line 12 is the `str` item); ty 0.0.97/0.0.98 and pyright accept; CPython `<class 'int'>`. Controls: `c7plain.py` (one method, `value: int | str`) accepted by all; `c7ctl.py` (`value: str`) rejected by all (ty `invalid-dataclass`, pyright `reportGeneralTypeIssues`); `c7d.py` (overloaded override of an ordinary method, one item compatible) accepted by mypy 2.4.0 and master; `c7b.py` (items `str` and `bytes`, no `int`): mypy reports both items, ty reports `invalid-dataclass` at the implementation, pyright is silent. Cause read in mypy master: `checker.py` calls `dataclasses_plugin.check_post_init(self, defn, defn.info)` from `check_func_def`, and the plugin passes `defn.type` of that single item to `check_override`. Not debugged. Duplicate search: python/mypy 12 issue and 4 PR term sets, ty 2, pyright 3; read mypy#15498, PR #15503 (added the check, no overload case), #9254, #16293, #15515, #12379. No match. Draft 8; confidence 0.6 (the maintainers may call the per-item check intended, though the generic override rule says otherwise).

### D8-8 pyright-only `Desc.__delete__` over-arity

Evidence text of `seed-8af1b011a91f` (Phase 4 item 35): pyright `reportCallIssue Expected 2 positional arguments`, CPython raised the type error and the program handled it. Reduction `repro/c8ctl.py` (module-level untyped `wrap`) and `repro/c9.py`: ty reveals `def wrap(fn) -> Unknown` and `Desc.run` as `Unknown`, mypy `Any`, pyright `(self: Desc, obj: object) -> None`. With `ty check --config 'analysis.return-type-inference = "always"'` (0.0.97 and 0.0.98) ty reveals `(self, obj: object) -> None` and reports `too-many-positional-arguments` on `c9.py`, `c8ctl.py` and the verbatim program (`results/ty_rti.txt`). ty#4739 (the feedback issue) states RTI is off by default; ty#1971 (open) tracks pass-through for untyped decorators; carljm there: mypy neither infers nor assumes, ty matches mypy. Pyright is right at runtime, ty and mypy are silent by design.

### D8-9 ParamSpec family

`repro/e1.py` to `e4.py`, all tools:

| Program | ty | mypy | pyright | Read |
|---|---|---|---|---|
| e1 `__init__(self: Callable[[int], None], ..)` with `self.x = x` | `unresolved-attribute`, `invalid-argument-type` | `[misc]` erased type of self not a supertype | supertype error plus attribute error | all reject |
| e2 `setup(self: Callable[[int], None])` with `self.y = 1` | rejects | accepts | rejects | mypy's `self.y = ..` in a method defines an attribute; `repro/c11.py` shows mypy rejects the same store and the reads on a `Callable` parameter. Design |
| e3 `cls: Callable[P, T]` classmethod `__call__` | binds `cls` to the constructor: `() -> User` | `def [P, T] (*P.args, **P.kwargs) -> T` | `() -> User` | CPython rc 0 (the `NotImplementedError` is caught), runtime does not decide. Design |
| e4 `self: int` / `self: Callable[[int], int]` | accepts | rejects both | rejects both | ty#3666 (open) |

The 21 (Day 6) and 16 (Day 7) live findings of the family are dismissed by the Phase-1 entries; nothing in them is a new bug.

## 4. Additional lead, not drafted

`d3p_callables_self_call_attr__mut0_5445453a` (live `only_mypy misc`, not strong). `repro/c12.py`: `class C: __call__: Callable[[], int]` (annotation only) and `C()()`. CPython raises `TypeError` (special-method lookup finds no `__call__` on the class). ty 0.0.97/0.0.98 and pyright accept `C()()`; mypy reports `Attribute function "__call__" with type "Callable[[], int]" does not accept self argument [misc]` (a different cause, right outcome). The variant that assigns `self.__call__ = lambda: 1` in `__init__` is rejected by ty and pyright (`call-non-callable`, "not callable"). So ty and pyright treat an annotation-only declaration as a class-level `__call__` but an instance assignment as not callable. Searches (10 term sets on ty, pyright, mypy; mypy#2113 read, open, the mypy-side version of the same unsoundness): no ty or pyright issue. Not drafted because I could not tell whether ty and pyright intend annotation-only members to count (the same declaration form is what a callback-style protocol or dataclass field uses) and the finding was not strong. Candidate for a Day-9 look at ty's treatment of annotation-only dunder attributes; confidence 0.4.

## 5. Searches and limits

- Tracker searches (`gh search issues|prs`, read-only): a first batch of 62 queries with 4 to 8 words returned almost nothing, because GitHub ANDs all words; it was discarded (`search/out1.txt`, `out2.txt`) and redone with 1 to 3 words: **113 queries** (`search/spec3.txt` to `spec6.txt`, output `out3.txt` to `out6.txt`; ty 44, mypy 28, pyright 20, ruff 2 issue and 8 PR, mypy 5 PR, pyright 5 PR, python/typing 1), plus an author listing of 4 repositories (`out_author.txt`). 21 `gh issue view` / `pr view` calls (`views.txt`, `views2.txt`, `views3.txt`; python/mypy#4380 in `views3.txt` was a wrong number I typed and is irrelevant) and 3 `gh release list` calls.
- GitHub search matches words in titles, bodies and comments, not meaning; comments were read only for the issues listed above.
- No playground was used; draft 8 has the `<PLAYGROUND LINK>` placeholder (UNVERIFIED-PLAYGROUND).
- ty `main`, pyright `main`, mypy PR branches and the branch of pyright PR #11965 were not built.
- The pyright `str` result for `norm(Any)` in `p_overloads_1de657a6` (ty `Unknown`, mypy `Any`) was seen once; the minimal `repro/c10.py` gives `Unknown` on pyright, so it was not pursued.
- Typing spec pages fetched: overloads (quoted above, paraphrased in the text) and dataclasses (no text on `__post_init__`).

## 6. Final checks

`.venv/bin/python -m pytest tests -q` -> **604 passed** in 77.06 s (`results/pytest.out`). `.venv/bin/typediff --python-version 3.13 kb-selftest` -> **20 PASS, 0 FAIL** (`results/kb-selftest.out`). `campaign/day4m/check_hits.py 0.80` -> **40 files; 0 with problems**, no near-duplicate pair (`results/check_hits.out`). No code or KB change in this phase; `runs/hits` unchanged.
