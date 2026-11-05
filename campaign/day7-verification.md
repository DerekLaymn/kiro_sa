# Day 7 verification (Part D)

Date: 2026-11-06. Branch `campaign/day7-p2`, local only. Nothing was pushed, no issue, PR or comment was written on GitHub (`gh` calls were `search`, `issue view`, `pr view`, `pr diff`, `release list`; web search twice). Evidence: `campaign/day7/partD/evidence/` (`repro/` programs, `results/` raw tool output, `search/` gh output, `scripts/`).

Input: the live patterns of Part C (`campaign/day7-triage.txt`, 107 live findings in 24 patterns, `campaign/day7-run-log.md` items 26 to 39) and the open Day-6 candidate "mypy accepts a class with `__eq__` and no `__hash__` as `Hashable`" (`campaign/day6/partB/evidence/hash_h1.py`, `campaign/day6-report.md` section 6 item 1).

## 1. Tools

| Tool | Versions used | Note |
|---|---|---|
| CPython | 3.13.16 (`.venv`) | |
| ty | 0.0.97 (`.venv`, the pin), 0.0.97 (`/tmp/d3v-latest`), **0.0.98** (new, installed in `/tmp/d7pd/ty98` with `uv`, the pin is unchanged) | PyPI and `gh release list`: 0.0.98 was released 2026-11-05 17:39 UTC, after `/tmp/d3v-latest` was built. `results/latest-releases.txt` |
| mypy | 2.4.0 (`.venv`), 2.4.1 (`/tmp/d3v-latest`, PyPI latest), master 2.5.0+dev.879da562 (`/tmp/d3v-master`) | |
| pyright | 1.1.414 (`.venv` and `/tmp/d3v-latest`) | 1.1.414 is also the latest on npm, PyPI and GitHub releases (2026-09-09). Not tested: pyright `main`, the open PR branches |

Every program was run by `scripts/runall.sh` (CPython, ty x3, mypy x3, pyright x2); the output is in `results/<id>.txt`. `results/c2.txt`, `c3.txt`, `c1.txt` ran before the ty 0.0.98 block was added to the script; the later reductions include it.

## 2. Candidates and verdicts

| Id | Candidate | Verdict | Evidence in short |
|---|---|---|---|
| D7-1 | ty and pyright reveal the old value in an `except` clause after a nested unpacking assignment failed half-way (`partial_unpack_exception`, 3 programs) | **STILL-BUG-NEW** (ty; draft 6) | CPython `'bad'`, ty 0.0.97/0.0.98 `Literal[1]`, mypy `int \| str`. No matching issue. Related: ty#225 (closed), ruff#27471 (merged) |
| D7-2 | pyright `RangeError: Maximum call stack size exceeded` on a decorated descriptor `__get__` (`d3p_descriptors_decorated_get__mut1_040cc0db`) | **STILL-BUG-NEW** (pyright; draft 7) | crashes on 1.1.414 (latest), exit 2; ty and mypy do not crash. Not pyright#11961 (constructor path, open PR #11965 does not touch it) |
| D7-3 | ty skips the read-only property assignment after a descriptor `__set__` changed the narrowed attribute (`d4p_descriptors_readonly_prop_never__mut1_328a328e`) | **DUPLICATE** of astral-sh/ty#2792 | identical result when the mutation is an ordinary method call, which is the KB entry TY-2792-READONLY. Related: ty#4880, ty#4345 |
| D7-4 | pyright: `Gauge.level` is `Clamped \| int`, `assert_type(Gauge.level, Clamped)` fails (`only_pyright`, `gen3_908b3252`) | **DUPLICATE** of microsoft/pyright#11382 (open) | same cause: `self.level = start` in `__init__` of a data descriptor |
| D7-5 | ty `unsupported-operator` for `a + b` after `case (a, b)` when the subject union contains a non-final class (`class_sequence_patterns__mut0_713c86e5`) | **NOT-A-BUG** | ty intersects the non-final class with `Sequence[object]` on purpose (multiple inheritance); ty#1578 closed not planned, better diagnostics tracked in ty#2215 |
| H1 | mypy accepts a class with `__eq__` and no `__hash__` as `Hashable` (Day 6 open candidate) | **DUPLICATE** of python/mypy#2455 (and #18622) | open PR python/mypy#19168 implements the missing rule. mypy 2.4.0, 2.4.1 and master all accept |

STILL-BUG-NEW drafts appended to `campaign/day3-issue-drafts.md`: **2** (draft 6: ty, draft 7: pyright). None is filed.

## 3. Details per candidate

### D7-1 partial unpack in `try`

Reduced repro (`repro/c1.py`, from `campaign/day7/partC/evidence/reduce/v1.py`):

```py
def f(pair: tuple[int, ...]) -> None:
    value: int | str = 1
    try:
        value, (a, b) = "bad", pair
    except ValueError:
        reveal_type(value)
f((1,))
```

| Tool | `reveal_type(value)` in the `except` |
|---|---|
| CPython 3.13.16 | `'bad'` (`value` is bound before the nested `(a, b)` unpack of a 1-tuple raises `ValueError`) |
| ty 0.0.97, 0.0.98 | `Literal[1]` |
| mypy 2.4.0, 2.4.1, master | `int \| str` |
| pyright 1.1.414 | `Literal[1]` |

Variants (`repro/c1b.py`, `c1c.py`, `c1g.py`): `value, items[5] = "bad", 2` gives ty `Literal[1, "bad"]` (correct); `value = items[5] = "bad"` gives ty `Literal["bad"]` (correct); the flat `first, second = values` followed by `state = 1` gives `Literal[0]` (correct, and the case that ruff#27471 documents). Only a nested unpacking target after an earlier bound target is wrong: ty places one exception checkpoint before the whole target list. pyright shows `Literal[1]` for every variant including `value = "bad"` followed by `items[5]` (a complete statement), so for pyright the snippet is part of a wider limitation (my reading: it links `except` only after call nodes; I did not read the pyright source) and is not drafted.

Duplicate search (all read-only):
- `gh search issues/prs` in astral-sh/ty, astral-sh/ruff, microsoft/pyright, python/mypy with 8 term sets (round 1: tuple unpacking except narrowing, partial assignment except, assignment raises exception except clause, try except declared type narrowing assignment, chained assignment exception, nested unpacking exception, except clause reachability assignment, multi-target assignment) and 10 more on ty, ruff and pyright (round 2: try except assignment, except narrowing assignment, exception handler flow, unpack ValueError, binding try block, try block reachability, raise during assignment, definition in try block, except clause, try statement). `search/c1-*.txt`. A first round with whole phrases quoted and no pause hit the search rate limit and was discarded and redone.
- Read: ty#225 (closed; flow of `try`/`else`; fixed by ruff#27471), ty#762 (closed, unrelated), ruff#27471 (merged 2026-08-12, "Model try exception flow with operation checkpoints"; its mdtest has "Unpacking can raise" for the flat case only), mypy#13123 (open, the opposite direction: mypy keeps too many states), plus the PR titles ruff#27703, #27817, #29750 (checkpoint follow-ups, no nested-unpack case).
- Result: no issue or PR describes a partial binding by a nested unpacking target. Not a duplicate. The maintainers have an active feature here, so the report will likely be handled as an edge case of ruff#27471.

Verdict: STILL-BUG-NEW for ty, confidence 0.5 (narrow, but the runtime evidence is exact and the feature is new). Draft 6.

### D7-2 pyright `RangeError`

Program from Part C: `runs/day7/gen/descriptors_properties/d3p_descriptors_decorated_get__mut1_040cc0db.py` (`repro/c2.py`). Reduced (`repro/r6.py`):

```py
class Desc:
    def deco(fn):
        return fn

    @deco
    def __get__(self, obj, owner=None):
        return 42


class Host:
    attr = Desc()


h = Host()
print(h.attr)
```

| Tool | Result |
|---|---|
| CPython | `42` |
| pyright 1.1.414 (both installs) | `An internal error occurred ... RangeError: Maximum call stack size exceeded`, exit status 2 (`results/pyright-exit-codes.txt`); frames `typeUtils.ts` and `typeEvaluator.ts` `retainTypeAlias` repeating |
| ty 0.0.97, 0.0.98 | no crash, `invalid-argument-type` on `@deco` (the first parameter of a class-body function is taken as `self`) |
| mypy 2.4.0, 2.4.1, master | no crash, `arg-type` on `@deco` for the same reason |

Cause: pyright infers the unannotated parameter of `deco` as `Self@Desc`, so the decorated `__get__` has the type of `Desc` itself, and applying the descriptor protocol to it never ends. The three-line `class Desc: __get__: "Desc"` followed by `Host().attr` crashes the same way (`repro/r8.py`; CPython does not care, there is no real `__get__`). Controls that do not crash on pyright (`results/pyright-reduce-r1-r7.txt`, `-r8-r11.txt`): no access to the attribute (`r5`), decorated `__set__` with an assignment (`r2`), decorated ordinary method called (`r3`), decorated `__call__` called (`r10`), the decorator at module level (`r11`). Direct call `Desc.__get__(Desc(), None, Host)` crashes (`r4`), so the instance access is not needed.

The program is not clean for any checker (ty and mypy report the decorator line, pyright reports `reportSelfClsParameterName`). The crash is the finding, not the missing diagnostic.

Duplicate search: `gh search issues/prs` microsoft/pyright with 9 term sets (Maximum call stack size exceeded, RangeError, descriptor decorated `__get__`, decorator `__get__` descriptor, retainTypeAlias, stack overflow descriptor, infinite recursion descriptor, crash decorated method self, decorator without self class body), `search/c2-pyright-rangeerror.txt`; web search on the same terms. Read: #9283, #9740, #6178, #6783, #5139, #4798, #5090 (Part C, `campaign/day7/partC/evidence/gh3.out`: old telemetry issues, none involves a descriptor), and today **#11961** (open, 2026-11-02) with its fix **PR #11965** (open): that crash is `validateConstructorArgs` recursion for `__init__`/`__new__`/metaclass `__call__` annotated with their own class; the PR diff only adds a `constructorCallStack` guard in `validateCallForInstantiableClass`, and the stack here goes through `typeUtils.ts` and `retainTypeAlias`, so the PR does not touch this path. Same family ("dunder typed as its own class"), different code path. Related for the ty/mypy side only: ty#4148 and python/mypy#22361 (self-referential `__call__`), not pyright.

Verdict: STILL-BUG-NEW (pyright), confidence 0.8. Draft 7. Not tested: pyright with the PR #11965 applied.

### D7-3 read-only property after a descriptor store (ty)

`repro/c3.py` is the Part C mutant (`t.bumped = 3` runs `Bumper.__set__`, which changes `t.base`; then `assert t.base == 7` is unreachable for ty, so ty does not report `t.readonly = 5`). `repro/c3r.py` puts the descriptor store and a plain method call `t.bump(3)` side by side: ty 0.0.97 and 0.0.98 reveal `Literal[4]` for `t.base` after both, and CPython raises the `AttributeError` for both; mypy and pyright report the read-only property in both. The mechanism is the one of ty#2792 (narrowing of an attribute is kept after a call that changes it; carljm: every checker does this, a direct method call on `self` could be special-cased). A descriptor store is an implicit call to `__set__`. Read ty#2792, found ty#4880 (closed, "unreachable code seems to assume immutability"), ty#4345 (open, Mock `call_count`), ty#628 (open, assignment narrowing with a descriptor). Verdict: DUPLICATE ty#2792. No KB entry added: the closing matcher `readonly_prop_after_stale_narrowing` needs a program method call and the descriptor store would need a new matcher. Nothing is gained for the dismissal rate beyond this one parent mutant family.

### D7-4 pyright class access to a data descriptor assigned in `__init__`

`repro/p1.py`: `assert_type(Gauge.level, Clamped)` fails on pyright with `Clamped | int`, CPython `type(Gauge.level)` is `Clamped`, ty and mypy (all versions) accept. Cause and reporter's analysis are in microsoft/pyright#11382 (open, 2026-04-13; a comment confirms 1.1.411 and that any instance method assignment is enough). Verdict: DUPLICATE pyright#11382. Of the other 18 `only_pyright` findings of Part C (12 programs, all `RUNTIME/weak ... neutral`): 10 findings in 6 programs are mutants of the decorated-descriptor parents (`h.slot = 5` on a descriptor whose `__set__` is decorated by a class-body `keep(fn)`; pyright types the decorated dunder as the descriptor class and rejects the use, ty and mypy report the decorator line instead). I checked `seed-3c7159d68626` only; the cause is the self-parameter inference of D7-2, not a separate bug. 6 findings in 3 programs come from the ParamSpec self-annotated `__call__` family (not analysed, see section 4). 2 fresh programs (`4a2a192556ca`; `81f56b3b025b`, an abstract property implemented by a class attribute, which pyright rejects with `reportAssignmentType`) were not analysed.

### D7-5 `object` captures in a sequence pattern (ty)

`repro/p2.py`: `Wrap | tuple[int, int]` matched with `case (a, b)`: ty reports `a + b` as `object + object`, mypy and pyright accept, CPython runs. ty narrows `Wrap` by `Sequence[object]` because a subclass of the non-final `Wrap` could be a sequence (ty#1578, closed not planned, carljm's explanation; ruff#26807 merged, `search/ty-1578-ruff-26807-read.txt`). Same on ty 0.0.98. Verdict: NOT-A-BUG (design difference). The false positive can be removed by making `Wrap` `@final`.

### H1 mypy and `Hashable` (Day 6 candidate)

`repro/h1.py` (Day-6 evidence file) and `repro/h1b.py` (the draft 4 program plus a dataclass):

| Tool | `need(Plain())`, `need(Sub())` | `need(Record("a"))` (dataclass, eq, not frozen) |
|---|---|---|
| CPython 3.13.16 | `TypeError: unhashable type` | `TypeError: unhashable type: 'Record'` |
| mypy 2.4.0, 2.4.1, master | accepted | accepted |
| ty 0.0.97, 0.0.98 | accepted (draft 4) | rejected |
| pyright 1.1.414 | rejected | rejected |

Duplicate search: `gh search issues` python/mypy with 18 terms (Hashable, `__eq__`, `__hash__`, unhashable, `__hash__ = None`, implicit `__hash__`, `__eq__` without `__hash__`, hashable protocol, dataclass, and others) and `gh search prs` with 5, `search/mypy-hashable-searches.txt`. Read: 
- **python/mypy#2455** "MyPy does not enforce Hashability" (open since 2016): its example is exactly a class that defines `__eq__` and so loses `__hash__`, and a comment notes pyright added it after typeshed changes. 
- **python/mypy#18622** "Incorrect inference for types with `__eq__` and no `__hash__`" (open): `reveal_type(A().__hash__)` is `def () -> int`, proposal: infer `ClassVar[None]`. 
- **PR python/mypy#19168** (open): "Classes defining `__eq__` without `__hash__` get their `__hash__` assigned to `None` to match runtime semantics", "Fixes #18622 ... first step towards checking hashability of dict keys (and `Hashable` compatibility in general)". 
- Related, different: #20230 (open, `hash()`, `in set()`, `{obj}` false negatives), #11465, #11463 (dataclass not `Hashable`), #19232 (tuple of unhashable), #4266, #16550 (closed, attrs).

Verdict: DUPLICATE python/mypy#2455 (the issue that asks for exactly this, `Hashable` and the `{obj}` display follow from the same missing rule); the open PR #19168 is the pending fix. This corrects the Day-6 wording "UNVERIFIED, no duplicate found" (three phrases only). Draft 4 (ty) is unaffected: ty has its own `Hashable` implementation and does not share the mypy cause.

## 4. Other live patterns, looked at and not candidates

Reasons were checked in the programs (reports `runs/day7/out/seed-*.md`), no new search was needed:

| Pattern (Part C triage) | Disposition |
|---|---|
| `reveal_mismatch uncomparable` (18): TypedDict vs class name, `def (float)` vs `(float, /) -> None` | display forms of the same type, NOT-A-BUG |
| `reveal_mismatch different` (10): recursive alias `int \| list[...]` vs ty expansion | mypy#2008 (already in the Day-3 not-drafted list) |
| `only_mypy override` / `arg-type` / `operator` on `overloaded_post_init` mutants (7 + 6 + 1) | mypy checks the user `__post_init__` and the `InitVar` parameter against the synthesized signature; the mutants use mismatching types, mypy is right. `InitVar[int]` in a function annotation is invalid and ty reports it |
| `concern_mismatch arg-type` on `assert_never(v)` (6) | all three checkers reject; the program's `list[int]` arm is not exhaustive by type (list patterns are not exhaustive) |
| `mypy_more_precise` star-pattern `rest` (5): ty `list[int] \| list[str]` | the same non-final intersection design as D7-5, not contradicted by the runtime |
| `only_ty invalid-argument-type` `Strict.label(3)` (`s: Base = Strict()`) | ty narrows the declared type on assignment (Day-5 design note) |
| `only_mypy arg-type` `load(Fixed())` after `Source.register(Fixed)` | ty accepts only because of the earlier `assert issubclass(Fixed, Source)`; without it ty rejects like mypy (`repro/a1.py`), NOT-A-BUG |
| `only_ty unresolved-attribute` `x.hex()` for `Callable[[float], ...]` | `float` means `float \| int`, `int.hex` does not exist, ty is right |
| `only_ty` / `only_mypy` on `d3p_paramspec_self_annotated_dunder_call` mutants (16 live) | the Day-6 unverified neighbourhood of TY-4899; unchanged, not analysed |
| `only_mypy has-type`, `overload-overlap` (3 + 3) | already carry KB hints (GRADUAL-OPERAND, ERROR-CASCADE, TY-CHECK-MISSING-JUDGE-MYPY); not runtime-contradicted |

## 5. Limits

- Playgrounds (play.ty.dev, mypy-play, pyright playground) were not used: the `<PLAYGROUND LINK>` placeholders in drafts 6 and 7 are open (UNVERIFIED-PLAYGROUND).
- ty `main`, pyright `main` and the open PR branches were not built. ty 0.0.98 and pyright 1.1.414 are the latest releases.
- GitHub search matches words in titles and bodies, not semantics; issue comments were read only for the issues listed above.
- No KB entry was added or changed; the pytest, kb-selftest and `check_hits` results of Part C are unchanged (no code change).
