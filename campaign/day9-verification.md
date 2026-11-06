# Day 9 verification (Phase 6)

Date: 2026-11-06. Branch `campaign/day9-p2`, local only. Nothing was pushed. No issue, PR or comment was written on GitHub (`gh` calls were `search issues`, `search prs`, `issue view`, `release list`; web fetches of the Python data model, the ty rules page and the mypy test data). No pin was changed. Evidence: `campaign/day9/phase6/` (`repro/` programs, `results/` raw tool output, `search/` gh output, `scripts/`). Shell note: fish garbles stdout, every command ran as `bash script.sh > file 2>&1` and the file was read.

Input: the strong-evidence findings of `campaign/day9-triage.txt` (10 findings in 8 programs; `campaign/day9/phase5/strong_live.out`: 6 `reveal_mismatch` and 4 `runtime_miss`). Two further groups were verified because the Phase 5 log (item 7) marks them as unverified leads that decide whether the new operators found something: the 22 `only_pyright` rows with relation `runtime_supports` of `campaign/day9-only-pyright-relations.txt` (evidence strength weak in the triage), and one live mypy row that showed up in a strong candidate (`Need type annotation for "key"`).

## 1. Tools

| Tool | Version used | Note |
|---|---|---|
| CPython | 3.13.16 (`.venv`) | |
| ty | 0.0.97 (`.venv`, the pin), **0.0.99** (`/tmp/d9v/ty99`, verification only) | 0.0.99 is the newest release (GitHub and PyPI 2026-11-06 10:13 UTC). Installed beside the pin with `uv`; `.venv` still has 0.0.97. The ty 0.0.97 and 0.0.99 sections of all 30 runall result files are identical (`results/ty_diff.txt`) |
| mypy | 2.4.0 (`.venv`, the pin), 2.4.1 (`/tmp/d3v-latest`, PyPI latest, 2026-10-28), master 2.5.0+dev.879da562 (`/tmp/d3v-master`) | `gh release list` for python/mypy prints nothing, PyPI is the source for the latest release |
| pyright | 1.1.414 (`.venv`) | latest on PyPI (2026-09-10) and in GitHub releases |

`results/versions.txt`. Every checker ran through the memguard shim in `.venv/bin` or through `memguard.sh` directly, under a `timeout`, one program at a time (`scripts/runall.sh`: CPython, ty x2, mypy x3, pyright, exit codes printed; output in `results/<id>.txt`). Verbatim copies of the 8 programs are `repro/p_*.py`; reductions are `repro/c*.py` and `repro/d*.py`.

## 2. Candidates and verdicts

Strong-evidence candidates of the triage:

| Id | Candidate | Verdict | Evidence in short |
|---|---|---|---|
| D9-1 | mypy reveals `Widget` for a class whose metaclass `__call__` returns `int` (`constructors_metaclasses/gen1_c86958a8`, 1 strong finding) | **DUPLICATE** of python/mypy#8595 (closed 2020-03-27) | CPython `int`; ty 0.0.97/0.0.99 `int`; pyright `int`; mypy 2.4.0, 2.4.1, master `Widget`. #8595: "unlikely this will be ever supported". Open #14122 ("Support `__call__` on metaclasses"), closed #15182 |
| D9-2 | mypy reveals `tuple[int, str]` for a 4-tuple (`typevartuple_unpack/gen1_4d7d067f`, 2 strong findings) | **NOT-A-BUG** | `tuple[*Ts, *Us]` is invalid. ty (`invalid-type-form`), mypy ("More than one variadic Unpack ... is not allowed"), pyright (`reportInvalidTypeForm`) all reject the signature. The odd reveal follows the error |
| D9-3 | mypy reveals the opposite literal for `c1 < c2` and `c1 > c2` (`inheritance_mro/..total_ordering_inherited_lt__mut0_73c4aa3f`, 2 strong findings) | **STILL-BUG-NEW** (mypy), **draft 9** | Reduced to 18 lines without `total_ordering`. mypy tries the reflected method first for two operands of the same type. CPython `'lt' 7`; ty and pyright agree; mypy `int`, `str` swapped on all three versions |
| D9-4 | mypy `int` for `A * B` where `RightMeta` subclasses `LeftMeta` (`constructors_metaclasses/d4v_metaclass_reflected_op__mut0_dcb547ed`, 1 strong finding) | **DUPLICATE** of python/mypy#22377 (open) | Draft 3, filed by the drafting account on 2026-11-05. CPython `str`; ty `str`; mypy `int` (3 versions); pyright `int`, as the draft says |
| D9-5 | `class Callback[*Ts, **P = [bool]]` raises `TypeError` and no checker says so (`..paramspec_default_after_tvt__mut0_49d4094b`, 1 strong finding) | **DUPLICATE** of python/typing#2211 (open) for the runtime error; the checkers are right | The spec requires accepting the class; the runtime is wrong (Jelle Zijlstra: "a bug in the runtime"). ty, mypy and pyright accept it |
| D9-6 | same class, `..mut0_df958820` (1 strong finding) | **DUPLICATE** of python/typing#2211 | Same `TypeError` at the class statement. mypy's `Callback[int, str]` error is draft 5 (filed as python/mypy#22375) |
| D9-7 | same shape with `Generic[*Ts, P]` and a `ParamSpec(default=...)`, `..mut0_9940d14a` (1 strong finding) | **DUPLICATE** of python/typing#2211 | CPython fails at the class statement (line 12); ty and pyright accept the class, mypy shows the draft-5 error |
| D9-8 | `n + 1` with a `str` passed through `Any` (`gradual_any/gen5_ade5dcc3`, 1 strong finding) | **NOT-A-BUG** | The program passes a `str` to an `Any` value on purpose; `Any` is consistent with `int`. No checker reports the call, as the gradual guarantee requires |

Counts: 8 candidates, **STILL-BUG-NEW 1, DUPLICATE 5, NOT-A-BUG 2, FIXED 0**. 10 findings: D9-1 1, D9-2 2, D9-3 2, D9-4 1, D9-5 to D9-8 4.

Additional leads verified in this phase:

| Id | Candidate | Verdict | Evidence in short |
|---|---|---|---|
| D9-9 | 20 `only_pyright` `runtime_supports` rows: `len(x)`, `list(x)`, `iter(x)` on a class whose `__len__`/`__iter__` is annotation-only (and some instance-assigned) | **NOT-A-BUG** (known trade-off) | In all 20 programs pyright's message is "Could not bind method ... missing a `self` or `cls` parameter" (19) or `No overloads for "iter"` (1). CPython raises `TypeError`, no checker rejects all five operations. ty#4570 comments state the trade-off; mypy#2113 for instance-assigned dunders |
| D9-10 | 2 `only_pyright` rows: a name assigned in a `with` block of a context manager whose `__exit__` returns `bool` is used after the block (`context_managers/gen0_b82d2e9e`, `gen21_6ee04c3a`) | **STILL-BUG-NEW** (mypy, confidence 0.4), **draft 10**; ty NOT-A-BUG | CPython `UnboundLocalError`; pyright reports it by default; ty reports it with the rule enabled (off by default); mypy `possibly-undefined` never reports it |
| D9-11 | mypy `Need type annotation for "key"` for `self.key = key` with a constrained type variable (live row in `..mut0_df958820`) | **DUPLICATE** of python/mypy#19618 (open) | Same on a constrained PEP 695 variable with and without a default, and on an old-style `TypeVar("K", int, str)`; ty and pyright infer `str` |

Totals over the 11 rows: STILL-BUG-NEW 2 (drafts 9 and 10), DUPLICATE 6, NOT-A-BUG 3.

Drafts appended to `campaign/day3-issue-drafts.md`: **2** (draft 9 and draft 10), numbered from 9. The header table, a "Day 9 status" paragraph in the header, and a "Day 9 status" note at the end list the rest. None is filed.

The author listing of the drafting account (`search/author.out`, 2026-11-06) shows drafts 1 to 5 already filed: ty#4933 (1), ty#4934 (2, closed), mypy#22377 (3), ty#4941 (4), mypy#22375 (5). Drafts 6, 7 and 8 are not filed.

## 3. Details

### D9-1 metaclass `__call__` return type (mypy)

`repro/c1.py`: `class Meta(type): def __call__(cls, *args: str) -> int`, `class Widget(metaclass=Meta)`, `reveal_type(Widget("abc"))`. CPython `int`, ty 0.0.97/0.0.99 `int`, pyright `int`, mypy 2.4.0/2.4.1/master `c1.Widget`. The verbatim program `p_meta_c86958a8` is the same, with `Ticket` and `Pair` as controls that every tool gets right. Searches: python/mypy `metaclass __call__`, `metaclass call`, `__call__ return`, PR `metaclass __call__`; ty `metaclass __call__`, `metaclass call`. Read python/mypy#8595 (Phase 5 had read it; read again, state unchanged), #14122 (open, priority-2-low, "currently we don't handle `__call__()` on metaclasses correctly") and #15182 (closed 2026-05-27, `__new__` return types; its comments name the metaclass `__call__` case).

### D9-2 two unpacked `TypeVarTuple`s

`repro/c2.py` and the verbatim `p_tvt_4d7d067f`: `def concat(a: tuple[*Ts], b: tuple[*Us]) -> tuple[*Ts, *Us]`. ty 0.0.97/0.0.99: `invalid-type-form` "Multiple unpacked variadic tuples are not allowed", mypy `More than one variadic Unpack in a type is not allowed [misc]` plus a `return-value` error, pyright `reportInvalidTypeForm` "at most one unpacked TypeVarTuple or tuple". The control `repro/c2ctl.py` (`tuple[int, *Ts]`) has no error on any tool. The mypy reveal `tuple[Literal[1]?, Literal['x']?]` for the 4-tuple call (reduction) and `tuple[int, str]` (verbatim) follow the reported error. mypy#20386 (closed): "`args + args` cannot be represented", needs two unpacks. ty#4054 (open): the missing diagnostic for classes and aliases, not for `tuple`.

### D9-3 comparison priority for operands of the same type (mypy)

`repro/c3g.py`:

```py
class Base:
    def __lt__(self, other: "Base") -> str: return "lt"
class Child(Base):
    def __gt__(self, other: "Child") -> int: return 7
a = Child(); b = Child()
s: str = a < b
assert_type(a < b, str); assert_type(a > b, int)
```

| Tool | Result |
|---|---|
| CPython 3.13.16 | `'lt' 7` |
| ty 0.0.97, 0.0.99 | no diagnostic |
| mypy 2.4.0, 2.4.1, master | `assignment` error (`int` for `str`), `assert-type` `int` not `str`, `assert-type` `str` not `int` |
| pyright 1.1.414 | no diagnostic |

Variants (`results/c3.txt` to `c3g.txt`): `c3` both methods in one class with `Literal` returns: mypy right. `c3b` same without literals: right. `c3c` the two-class program: swapped (reveals `int` and `str`). `c3f`: `__le__`/`__ge__` swapped the same way; the control `a <= c` with `class Sub(Child)` as right operand is `int` in mypy and `7` in CPython (reflected first for a proper subclass: right). `c3e`: `__add__` in `Base`, `__radd__` in `Child`: mypy `str`, right (mypy only adds the unsafe-overlap message). `c3d`: with `@total_ordering` and no local method mypy reveals `Any` (plugin, unrelated). The data model (fetched 2026-11-06, "Basic customization", rich comparisons): the reflected method of the right operand has priority only if the operands are of different types and the right type is a subclass of the left type. Cause read in mypy master `checkexpr.py` `check_op_reversible` (`results/grep_mypy.txt`): the same-type branch is guarded by `op_name in operators.op_methods_that_shortcut`, a set of 14 arithmetic and bitwise methods without comparisons; the next branch puts the reflected method first when `lookup_definer(left_type, op_name) != lookup_definer(right_type, rev_op_name)` and `covers_at_runtime(right_type, left_type)` holds. Not debugged by instrumentation.

Duplicate search: python/mypy issues `reflected comparison`, `reverse comparison`, `__gt__ __lt__`, `comparison operator`, `reverse operator`, `check_op_reversible`, `rich comparison`, `__lt__ __gt__`, `same type reflected`, `operator subclass`, `__le__ __ge__`, `total_ordering`, `reflected method` (13), PRs `reflected comparison`, `reverse operator`, `comparison operator`, `check_op_reversible`, `__lt__ __gt__`, `op_methods_that_shortcut` (6); ty and pyright 2 issue queries each, ruff 1 PR query. Hits that matter: mypy#22377 (draft 3, a different branch of the same function), #22316 (open) and PR #22380 (open, error message names the flipped operator), #19006 and PR #19046 (closed and merged, tuple subclass priority), #1987 (closed 2018, "Can't overload `__add__` for subclass"). Nothing describes this case. The total_ordering parent has been a live reveal mismatch since Day 2 (`day3-morning.md`: "mypy reveals the opposite literals"), never verified before.

The other half of the program, `len(p)` on an annotation-only `__len__`, is part of D9-9.

### D9-4 reflected operator on class objects (mypy)

Verbatim `p_reflmeta_dcb547ed`: CPython prints `s`, ty `str`, mypy 2.4.0/2.4.1/master `int` with `assert-type` and `return-value` errors, pyright `int` with the same two errors. This is draft 3 (`LeftMeta`/`RightMeta`, `A * B`). `gh issue view python/mypy#22377`: open, label `bug`, author `DerekLaymn`, created 2026-11-05T21:50:48Z, no comments, the body is draft 3 as written. The `len(s)` half of the program is D9-9.

### D9-5 to D9-7 TypeVarTuple followed by a defaulted ParamSpec

All three verbatim programs fail in CPython 3.13.16 at the class statement with `TypeError: Type parameter with a default follows TypeVarTuple` (`typing.py` `_collect_type_parameters`). `49d4094b`: ty and pyright reveal `Callback[int, str, (x: int, y: str)]`, mypy `Callback[int, str, [x: int, y: str]]`, no errors. `df958820`: ty reveals `(bool, /) -> tuple[int, str]` and pyright `(bool) -> tuple[int, str]` for `Callback[int, str](pair)`, mypy reports `Can only replace ParamSpec with a parameter types list or another ParamSpec, got "str"` and `def (*Any, **Any) -> tuple[Any, ...]` (draft 5, python/mypy#22375). `9940d14a`: same mypy error for `Callback[int, str]()`; ty reports `invalid-type-form` only for `Callback[int, 3]` and pyright nothing. python/typing#2211 (open, filed 2026-03-08 by Alex Waygood, label "topic: conformance tests"): the conformance test `generics_defaults.py` requires accepting a class that raises at runtime; Jelle Zijlstra: "I think this is a bug in the runtime, yes." and links the spec section. The ty side was changed on purpose (ruff#29755, merged 2026-10-28, "Use a trailing ParamSpec default after a TypeVarTuple"; the Day 6 note in the drafts file cites ruff#29753). python/cpython: searches `TypeVarTuple default`, `ParamSpec default`, `TypeVarTuple ParamSpec` (issues), `TypeVarTuple default` (PR) find only other topics (#158981, #132100, #138859, PRs #158991, #155646); no cpython issue for this `TypeError`. The Phase 5 note ("three rediscoveries of the parent") holds.

### D9-8 gradual guarantee

`p_any_ade5dcc3`: `a: Any = 'hello'`, `takes_int(a)` runs `n + 1` on the `str`. ty, mypy and pyright accept the call (`c` is `int` on all three). Not a bug by design of `Any`. The other differences in the file are known: ty `Unknown` where mypy has `Any` for an unannotated return; pyright infers `Literal[3]` for `untyped(3)` by call-site return type inference and fails `assert_type(d, Any)`.

### D9-9 annotation-only and instance-assigned special methods

This is the lead of `day8-verification.md` section 4 (annotation-only `__call__`), widened by the operator `dunder_instance_shadow`. `repro/d1.py` (annotation-only `Callable` for `__len__`, `__call__`, `__iter__`, `__getitem__`, `__contains__`), `d2.py` (instance-assigned lambdas), `d3.py` (annotation-only with the instance as first parameter). CPython raises `TypeError` for `len(a)`, `a()`, `list(a)`, `a[0]` and `1 in a` in `d1` and `d2`.

| Operation | d1 ty | d1 mypy | d1 pyright | d2 ty | d2 mypy | d2 pyright |
|---|---|---|---|---|---|---|
| `len(a)` | accepts | accepts | rejects (cannot bind, no `self`) | rejects | accepts | accepts |
| `a()` | accepts | rejects (`misc`) | accepts | rejects | accepts | rejects |
| `list(a)` | accepts | accepts | rejects (cannot bind) | rejects | accepts | accepts |
| `a[0]` | rejects | rejects | accepts | rejects | accepts | rejects |
| `1 in a` | rejects | rejects | accepts | rejects | accepts | rejects |

(ty 0.0.97 and 0.0.99 identical, mypy 2.4.0, 2.4.1 and master identical.) With `Callable[["Ann"], int]` (`d3.py`) ty accepts all five, mypy rejects `len` and `list`, pyright rejects `a()`, `a[0]` and `1 in a`. All 20 `only_pyright` `runtime_supports` programs (not the two `with` programs) declare a dunder as annotation-only; pyright's message names the failed bind in 19 of them (`scripts/pyright_rows.sh`, `results/pyright_rows.txt`) and `No overloads for "iter"` in the other. ty treats an annotation-only `Callable` as a callable instance attribute that satisfies a protocol method. ty#4570 (open, `needs-decision`): Alex Waygood notes that dunders "cannot be soundly implemented by instance attributes", and carljm states that all other checkers allow it and have false negatives in some cases that raise at runtime. ty#491 (open): the Callable-as-method-descriptor discussion, the maintainers lean towards matching mypy and pyright. mypy#2113 (open since 2016, bug, Guido: "dunder methods must be defined on the class"): the same report for `self.__call__ = ...`. Not drafted: no tool is consistent, each tool's behaviour is a documented trade-off in an open issue, and a single tool-specific root cause is not visible. Confidence that ty or mypy would take it as a bug: below 0.3.

### D9-10 `with` blocks that swallow the exception (mypy)

`repro/c10.py` (user class, `__exit__(...) -> bool`), `c10b.py` (`contextlib.suppress`), `c10ctl.py` (`-> None`), `c10d.py` (`bool | None`, `Literal[True]`, `ExitStack`), `c10e.py`.

| Program | CPython | pyright | ty 0.0.97/0.0.99 default | ty with `--warn possibly-unresolved-reference` | mypy 2.4.0, master default and with `--enable-error-code possibly-undefined` |
|---|---|---|---|---|---|
| `c10` bool | `UnboundLocalError` | `reportPossiblyUnboundVariable` | silent | warning | silent |
| `c10b` suppress | `UnboundLocalError` | `reportPossiblyUnboundVariable` | silent | warning | silent |
| `c10ctl` None | `TypeError` propagates | silent | silent | silent | silent |
| `c10d` `bool \| None` | `UnboundLocalError` (the exit returns `True`) | silent | silent | silent | silent |
| `c10d` `Literal[True]` | `UnboundLocalError` | reports | silent | warning | silent |
| `c10d` `ExitStack` | `ValueError` propagates | silent | silent | silent | silent |

`c10e.py` (`with suppress(KeyError): return d["a"]`, no `return` after the block): mypy 2.4.0, 2.4.1 and master report `Missing return statement`, ty `invalid-return-type`, pyright `reportReturnType`. So mypy's type checker models the swallowing `with`; its `possibly-undefined` pass does not. In mypy master `partially_defined.py`, `visit_with_stmt` processes the targets and visits `o.body` as straight-line code (`results/grep_pd.txt`); the pass runs on the AST before type checking. ty documents `possibly-unresolved-reference` as "Default level: ignore" (rules page, fetched 2026-11-06), so the default `All checks passed!` is not a bug; with the rule on, ty is right in all four cases. Types `bool | None` are not treated as swallowing by any tool, which matches the typeshed convention. Duplicate search: python/mypy 8 issue and 3 PR queries (`possibly-undefined with`, `possibly-undefined suppress`, `possibly-undefined context manager`, `suppress possibly`, `swallow exceptions`, `partially_defined`, ...), ty 5, pyright 3, ruff 2 PR queries. Nothing about `possibly-undefined` and `with`. Closed mypy#7577, #10896, #7726, #15715 are the "Missing return statement" reports that the type checker fixed; pyright#5914, #8530 and #9279 are the same topic for pyright. The mypy test `testWithStmt` covers only names bound by `with` targets. Confidence 0.4: an opt-in check without type information may be a known limit.

### D9-11 `Need type annotation` with constrained type variables (mypy)

`repro/c9.py`, `c9ctl.py`, `c9b.py`: `class Tag[K: (int, str) = int]` with `self.key = key` gives `Need type annotation for "key" [var-annotated]` on mypy 2.4.0, 2.4.1 and master; also without the default and with `K = TypeVar("K", int, str)`; an explicit `key: K` or a bound (`B: float`) is accepted; ty and pyright infer `str`. python/mypy#19618 (open, 2025-08-08): the same message for `class C[T: (int, str)]`; a comment says mypy checks the body once per constraint and cannot merge the attribute types, a subset of #5416.

## 4. Searches and limits

- Tracker searches (`gh search issues|prs`, read-only), 1 to 3 words each: **133 queries** (`search/spec_a.txt` to `spec_d.txt`, output `out_a.txt` to `out_d.txt`; issues: mypy 57, ty 24, pyright 17, cpython 3, typing 2, ruff 1; PRs: mypy 19, ruff 8, pyright 1, cpython 1), plus an author listing of issues and PRs (`author.out`). 12 `gh issue view` calls (`views1.out` to `views3.out`) and 3 `gh release list` calls. A first run of `gh_view.sh` failed because `--comments` and `--json` cannot be combined; it was redone without `--comments` (the JSON holds the comments) and the output replaced.
- GitHub search matches words in titles, bodies and comments, not meaning; comments were read only for the issues listed above.
- No playground was used; drafts 9 and 10 have the `<PLAYGROUND LINK>` placeholder (UNVERIFIED-PLAYGROUND).
- Not tested: ty `main`, pyright `main`, mypy PR branches (for example PR #22380).
- The mypy cause in D9-3 and D9-10 is read from mypy master source, not shown by instrumentation.
- Of the 22 `runtime_supports` rows, the 2 `with` rows were reduced and run, the 20 dunder rows were grouped by mechanism from the pyright message and the source (all 20 programs checked with `scripts/pyright_rows.sh`), not each reduced.

## 5. Final checks

`.venv/bin/python -m pytest tests -q` -> **655 passed** in 84.91 s, rc 0 (`results/pytest.out`). `.venv/bin/typediff --python-version 3.13 kb-selftest` -> **20 PASS lines, no FAIL line**, rc 0 (`results/kb-selftest.out`). `campaign/day4m/check_hits.py 0.80` -> **40 files; 0 with problems**, no near-duplicate pair (`results/check_hits.out`). No code or KB change in this phase; `runs/hits` unchanged (40 files).
