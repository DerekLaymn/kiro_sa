# Day 6 verification: issue drafts 3 and 4, and the `adbc14c6128a` Callback candidate

Branch `campaign/day5-p2`, local only. Nothing was pushed, filed or commented on GitHub; only read-only `gh search`, `gh issue view`, `gh pr view`, `gh api` (GET) and web search were used.
Raw output of every run is in `campaign/day6/evidence/` and the reproducers are in `campaign/day6/repro/`, so this file can be read without re-running anything.

Numbering note: in `day3-issue-drafts.md` draft 3 is the **mypy** metaclass bug and draft 4 is the **ty** Hashable bug. The task text lists them the other way round. This file uses the file's numbering.
Drafts 1 (ty protocol flatten overflow) and 2 (ty alias narrowing over a loop back edge) were verified by the user on the ty playground and were skipped.

## 1. Verdicts

| Item | Tool | Verdict | One-line evidence |
|---|---|---|---|
| Draft 3: `A * B` with related metaclasses | mypy | **STILL-BUG-NEW** | mypy 2.4.0, 2.4.1 and master 2.5.0+dev.879da562 give the same 2 errors; CPython 3.13.16 prints `str`; cause confirmed (`covers_at_runtime(def () -> B, def () -> A)` is `False`); no upstream issue after 25+ phrases (issues and PRs) |
| Draft 4: `__eq__` without `__hash__` accepted as `Hashable` | ty | **STILL-BUG-NEW** | ty 0.0.97 (and 0.0.84): `All checks passed!`; CPython raises `TypeError: unhashable type`; pyright reports both calls; no ty/ruff issue or merged PR covers the implicit `__eq__` case |
| Callback `class Callback[*Ts, **P = [bool]]`, declaration | ty 0.0.97 | **NOT-A-BUG** | valid per typing spec and PEP 696; ty 0.0.84 to 0.0.93 rejected it, 0.0.94 stopped on purpose (ruff#29753). Not a regression |
| Callback, declaration | pyright 1.1.414, mypy | not wrong | both accept the declaration, as the spec says |
| Callback, runtime `TypeError` | CPython 3.13.16, 3.14.8, 3.15.0 | runtime bug, **DUPLICATE python/typing#2211** | all three versions raise on the spec's own example; Jelle Zijlstra on #2211: a bug in the runtime. No python/cpython issue found |
| Callback, subscript `Callback[int, str]` | mypy 2.4.0, 2.4.1, master | **STILL-BUG-NEW** (new draft 5) | `Can only replace ParamSpec ... got "str"` and the result is `Any`; pyright and ty 0.0.97 accept. Listed as failing in the public conformance results, no mypy issue found |

Answer to "which tool is wrong" for the Callback candidate: CPython's `typing` (rejects a valid class) and mypy (rejects the valid subscript). Not ty and not pyright. ty 0.0.97's silence on the declaration is correct.

## 2. Environment and commands

Tool versions (`evidence/00-versions.txt`, `01-latest-versions.txt`):

| Tool | Version | Source |
|---|---|---|
| ty | 0.0.97 | `.venv/bin/ty --version`; also the latest release (`gh release list -R astral-sh/ty`: 0.0.97, 2026-11-04T09:16:55Z) |
| ty (reference) | 0.0.84 to 0.0.97, one version at a time | `uvx --from ty==0.0.NN ty ...` |
| mypy pin | 2.4.0 (compiled: yes) | `.venv/bin/mypy --version` |
| mypy latest | 2.4.1 (compiled: yes) | `/tmp/d3v-latest`; `uv pip install --dry-run -U mypy` there: "Would make no changes"; newest tag `v2.4.1` |
| mypy master | 2.5.0+dev.879da562a4bba1ff8023799afad195bc364b730a (not compiled) | `/tmp/d3v-master`; GitHub API `repos/python/mypy/commits/master` returned sha `879da562a4bba1ff8023799afad195bc364b730a`, committed 2026-11-05T00:40:27Z, so the venv is at master HEAD |
| pyright | 1.1.414 | `.venv/bin/pyright --version`; PyPI latest is also 1.1.414 |
| CPython | 3.13.16 (`.venv/bin/python`), plus 3.14.8 and 3.15.0 for the runtime probe | `uv run --no-project --python 3.14|3.15` |

Runner: `campaign/day6/repro/run_all.sh FILE...` runs, in order, CPython 3.13.16, `ty check --python-version 3.13`, mypy 2.4.0 / 2.4.1 / master with `--python-version 3.13 --no-incremental --no-error-summary`, and `pyright --pythonversion 3.13`. It was run as `bash run_all.sh <files> > out.txt 2>&1`:

| Run | Files | Evidence |
|---|---|---|
| Hashable | `hash_bug.py`, `hash_ctrl.py`, `hash_extra.py` | `10-hashable-tools.txt` |
| Metaclass | `meta_bug.py`, `meta_ctrl.py` | `20-metaclass-tools.txt` |
| Callback, minimal variants | `c0_orig.py` to `c7_pack_default_after.py` | `30-callback-minimal-tools.txt` |
| Callback, spec example | `s1_spec_example.py`, `s2_nodefault_ts.py` | `31-callback-spec-example-and-runtimes.txt` |
| mypy use site | `m1_mypy_use_site.py`, `m2_mypy_legacy.py` | `32-mypy-use-site-assert-type.txt` |
| ty bisect | `uvx --from ty==0.0.$v ty check --python-version 3.13 c1b_decl_only.py` for v = 84..97 | `33-callback-ty-version-bisect.txt` |
| mypy source probe | `probe_covers.py` (wraps `mypy.checkexpr.covers_at_runtime` on master, prints non-tuple calls) | `21-...`, source of `check_op_reversible` in `22-...` |

## 3. Draft 4 (file numbering): ty accepts an `__eq__`-only class as `Hashable`

Reproducer `repro/hash_bug.py` (the draft's program). Results (`evidence/10-hashable-tools.txt`):

| Tool | Result |
|---|---|
| CPython 3.13.16 | `TypeError: unhashable type: 'Plain'`, exit 1 (raised at `need(Plain())`) |
| ty 0.0.97 | `All checks passed!`, exit 0 |
| ty 0.0.84 | `All checks passed!` (`evidence/01-latest-versions.txt`) |
| mypy 2.4.0, 2.4.1, master | no output, exit 0 |
| pyright 1.1.414 | 2 errors: `hash_bug.py:22:6` (`Plain`) and `hash_bug.py:23:6` (`Sub`), both "`__hash__` is an incompatible type", `Type "None" is not assignable to type "() -> int"` |

Controls (`repro/hash_ctrl.py`, ty 0.0.97): `reveal_type(Record.__hash__)` for a mutable `@dataclass` is `None`; `need(Record("a"))` (line 41) and `need(NoneHash())` with `__hash__ = None` (line 45) get `invalid-argument-type`; `OnlyNe()`, `OnlyLt()`, a subclass of `OnlyNe`, and an `__eq__` class with `__hash__ = object.__hash__` produce no error, which is correct. mypy 2.4.0, 2.4.1 and master: only line 45 is an error; they reveal `def (self: object) -> int` for `Record.__hash__`. pyright: only line 41 is an error (it did not report line 45; I did not investigate why).
`repro/hash_extra.py`: ty reveals `def __hash__(self) -> int` for `Plain.__hash__` and reports no error for `{Plain()}`, `{Plain(): 1}` or `hash(Plain())`; pyright reveals `None` and reports `reportUnhashable` for the set entry and the dict key.

Duplicate search (evidence `50-` to `57-`; `gh search issues|prs --repo ...`, then `gh issue view` / `gh pr view` / `gh pr diff` on the hits):
- astral-sh/ty issues and astral-sh/ruff PRs, 8 phrases each: `Hashable __eq__ __hash__`, `__hash__ None Hashable`, `unhashable Hashable protocol`, `implicit __hash__ None`, `class defines __eq__ without __hash__`, `unhashable type set dict key`, `Hashable protocol member __hash__`, `not hashable __eq__ override`. Two PR queries hit HTTP 403 (rate limit) in the first pass and were re-run with sleeps in `52-`.
- Round 2 (`52-`, `55-`): `hashability`, `hash in:title`, `unhashable`, `eq without hash`, `defines __eq__ unhashable`, `__hash__ implicitly None`, `implicit hash None dunder eq`, `TypeError unhashable type`, `Hashable`; `gh issue list --search` on titles with `__eq__`, `__hash__`, `hashable`; open ruff PRs with `ty Hashable`; recent PRs touching hash.
- Read in full: ty#4157 (closed), #4196 (closed), #3781 (open), #4748 (closed), #4754 (open); ruff PRs #27441 (merged 2026-08-05), #29471 (merged 2026-10-19), #26039 (merged 2026-06-17), #26040 (closed 2026-10-18, not merged), #26367 (closed).
- Findings: ty#4157 asked for non-hashable objects to be rejected for `Hashable`; ruff#27441 closed it. The PR text covers `__hash__` set to `None` (annotated or assigned `ClassVar`), built-in containers and mutable dataclasses; `gh pr diff 27441` has no occurrence of `__eq__`. ruff#29471 (restore hashability in subclasses) has none either. ruff#26040 does name the case ("implicitly disable hashing by defining `__eq__`" and an `__eq__` example) but only for union simplification, and it was closed on 2026-10-18 without a merge or a comment explaining why (timeline shows only bot comments and the close event), so it is not a recorded maintainer decision against the rule. ty#3781 (open) is about `{obj}` / `{obj: ...}` displays with a dataclass. No query, issue or PR covers `Hashable` and an `__eq__`-only class.
- Not found: any ty issue whose body or comments mention an `__eq__`-only class and `Hashable` (`gh search issues --match comments` with `__eq__ __hash__ unhashable` and with `defines __eq__ hash None` both returned nothing).
- Web search: ruff's own rule `eq-without-hash` (PLW1641) and CodeQL describe the runtime rule; pyright#5446 says pyright follows the `__hash__: None` convention. No ty issue.

**Verdict: STILL-BUG-NEW.** Caveats: ty `main` after 0.0.97 was not built or tested; the playground link is still open; the ty maintainers could regard it as part of ty#3781. ty already rejects the equivalent dataclass case, so I treat the `__eq__` case as the same rule applied inconsistently.

## 4. Draft 3 (file numbering): mypy reflected operator on class objects

Reproducer `repro/meta_bug.py`. Results (`evidence/20-metaclass-tools.txt`):

| Tool | Result |
|---|---|
| CPython 3.13.16 | prints `str`, exit 0 |
| ty 0.0.97 | `All checks passed!` |
| mypy 2.4.0, 2.4.1, master 2.5.0+dev.879da562 | identical: `meta_bug.py:18: error: Incompatible types in assignment (expression has type "int", variable has type "str")  [assignment]` and `meta_bug.py:19: error: Expression is of type "int", not "str"  [assert-type]`, exit 1 |
| pyright 1.1.414 | the same two errors (`reportAssignmentType`, `reportAssertTypeFailure`) |

Instance control `repro/meta_ctrl.py` (`L() * R()` where `R(L)` defines `__rmul__`): CPython prints `str`; mypy (all three) exit 0, no error; ty 0.0.97 gives `invalid-assignment` with `str | int` (imprecise, not a false negative); pyright reports `int` is not assignable to `str` (its maintainers treat that as by design, per the Day 4 note).

Cause (`evidence/21-`, `22-`): in `check_op_reversible` (mypy master, `checkexpr.py` around line 4329) the branch that tries the right operand's reflected method first requires `covers_at_runtime(right_type, left_type)`. With that function wrapped on master, the class-object program logs `covers_at_runtime(CallableType: def () -> meta_bug.B, CallableType: def () -> meta_bug.A) -> False` four times, and the instance control logs `covers_at_runtime(Instance: meta_ctrl.R, Instance: meta_ctrl.L) -> True` three times. The Day 4 "possible cause" is therefore confirmed on master. (Typeshed `TupleType` calls were filtered out of the probe output.)

Python rule: the data model says that when the right operand's type is a subclass of the left operand's type and provides the reflected method, it is called first (the note under `__radd__`, quoted in the bugs.python.org issue 41584 snippet from the web search). `type(B)` = `RightMeta` is a subclass of `type(A)` = `LeftMeta`, and CPython's output (`str`) confirms the order.

Duplicate search (evidence `50-`, `52-`, `55-`):
- python/mypy issues, 12 phrases in the first pass (`metaclass __rmul__`, `reflected operator metaclass`, `reverse operator class object metaclass`, `__ror__ metaclass`, `__radd__ metaclass subclass`, `binary operator classes metaclass subclass right operand`, `operators on class objects metaclass`, `reverse operand subclass priority`, `covers_at_runtime`, `metaclass __or__ __ror__ type union`, `Type[Foo] binary operator metaclass`, `check_op_reversible`) and the same number for PRs. The first two issue queries hit HTTP 403 and were re-run in `52-`, together with 8 more issue phrases and 3 PR phrases (`__ror__ metaclass`, `reverse operand metaclass subclass`, `binary operator type object metaclass`, `metaclass operator reversed`, `__rmul__ class object`, ...).
- Title searches in python/mypy (`gh issue list --search`): `metaclass in:title operator`, `reflected`, `__rmul__`, `__ror__`, `__radd__`, `reverse operator`, `right operand`, `binary operator ... metaclass`.
- Nearest hits: #4789 and #4929 (closed; the left operand's metaclass operators on `Type[Foo]` and TypeVar bounds, not the priority rule), #19006 (closed; tuple subclass priority, `covers_at_runtime` introduced by PR #19046), #5491 (closed 2025-06-09; cleanup of metaclass kludges in `check_op_reversible`, read in full: no mention of the right-metaclass-subclass priority), #18498 and #1486 (`__rmul__` overlap checks), #9388 (int/float duck typing), #7086 (unrelated).
- Web search: no issue; only the Python data-model sources.

**Verdict: STILL-BUG-NEW.** Caveat: I did not read the comments of #4789 and #4929 again beyond Day 4's notes; the title and first post show a different problem.

## 5. The Callback candidate (`adbc14c6128a`)

Program: `runs/day5/gen/typevartuple_unpack/d3p_typevartuple_unpack_paramspec_default_after_tvt__mut1_0ac168dd.py` (copy: `repro/c0_orig.py`, hypotheses comments dropped). The report `runs/day5/out97/seed-adbc14c6128a.md` has one finding, D1 `only_mypy`, verdict NEEDS_HUMAN.

### 5.1 Reduction and tool matrix (`evidence/30-`, `31-`)

| File | Content | CPython 3.13.16 | ty 0.0.97 | mypy 2.4.0 / 2.4.1 / master | pyright |
|---|---|---|---|---|---|
| `c0_orig.py` | original program in `try/except` | prints `TypeError: Type parameter with a default follows TypeVarTuple` (caught) | pass | 1 error, line 7: `Can only replace ParamSpec ... got "str"  [misc]` | 0 errors |
| `c1b_decl_only.py` | `class Callback[*Ts, **P = [bool]]: ...` only | `TypeError` (typing.py line 291) | pass | no output | 0 errors |
| `c1_min_ps.py` | the same plus `Callback[int, str]` | `TypeError` | pass | 1 error `[misc]` at the subscript | 0 errors |
| `c3_oldstyle_ps.py` | `Generic[Unpack[Ts], P]` with `ParamSpec("P", default=[bool])` | `TypeError` | pass | 1 error at the subscript | 0 errors |
| `c2b_typevar_decl.py` | `class Pack[*Ts, T = int]` (TypeVar default) | `TypeError` | `invalid-type-variable-default` | `A type variable with default cannot follow TypeVarTuple  [type-var]` | error (`reportGeneralTypeIssues`) |
| `c3b_oldstyle_tv.py` | legacy `Generic[Unpack[Ts], T]`, `T` defaulted | `TypeError` | `invalid-type-variable-default` | `[type-var]` | error |
| `c4_no_default_ps.py` | `class Callback[*Ts, **P]` | exit 0 | pass | pass | 0 errors |
| `c5_default_before_tvt.py` | `class Callback[**P = [bool], *Ts]` | `SyntaxError` (compile time) | `invalid-syntax` | error | error |
| `c7_pack_default_after.py` | `[**P = [bool], *Ts = *tuple[int]]` | exit 0 | pass | pass | 0 errors |

So the program is "only mypy complains, at the use site", as Day 5 said, and the declaration itself is accepted by every checker, while CPython rejects it. A defaulted `TypeVar` after the `TypeVarTuple` is rejected by all three checkers, which matches the spec's "error" example.

### 5.2 Is ty 0.0.97's silence a regression from 0.0.84?

`evidence/33-`: `c1b_decl_only.py` on ty 0.0.84, 0.0.85, ... 0.0.93 prints `error[invalid-type-variable-default]: Type parameters with defaults cannot follow a TypeVarTuple parameter` (10 versions); on 0.0.94, 0.0.95, 0.0.96 and 0.0.97 it prints `All checks passed!` (4 versions). The change landed in 0.0.94. The 0.0.94 release notes (`gh release view 0.0.94 -R astral-sh/ty`, 2026-10-28) list "Reject defaulted TypeVars after a TypeVarTuple in legacy generic classes (ruff#29753)". The PR (`evidence/34-`, merged 2026-10-28T01:45:39Z) says legacy bases and PEP 695 declarations now share one diagnostic that points to the pack and each later defaulted `TypeVar`, and that both allow a defaulted `ParamSpec`, "whose argument list is distinguishable from the types that fill the pack". Its conformance bot comment shows `generics_defaults.py:188` (the TypeVar case) became a true positive. The diagnostic text in 0.0.97 is now `TypeVars with defaults cannot follow a TypeVarTuple` (`evidence/30-`, `c2b`).
Conclusion: the change from 0.0.93 to 0.0.94 is deliberate. It removed a false positive on a spec-valid class. It is not a regression.

### 5.3 What the spec says

Fetched from https://typing.python.org/en/latest/spec/generics.html (section "Defaults following TypeVarTuple") and https://peps.python.org/pep-0696/ (same section): a `TypeVar` that immediately follows a `TypeVarTuple` must not have a default (ambiguous), and a `ParamSpec` with a default may follow a `TypeVarTuple` because a `ParamSpec` argument cannot be confused with a pack element. The spec example is `class Foo[*Ts = *tuple[int, str], **P = [float, bool]]: ...` with `Foo[int, str]` meaning `Ts = (int, str), P = [float, bool]` and `Foo[int, str, [bytes]]` meaning `P = [bytes]`. Nuance: the spec sentence and example put a default on the `TypeVarTuple` as well; the Callback class has none. The stated reason (no ambiguity) is the same, ty and pyright accept both forms, and mypy errors on both (`evidence/31-`, `s1` and `s2`).

### 5.4 Runtime

`repro/s3_runtime_probe.py` (`evidence/31-`) creates four classes with `exec`: PEP 695 `[*Ts, **P = [bool]]`, the spec example, `[*Ts, T = int]`, and a legacy `Generic[Unpack[Ts], P]`. On CPython 3.13.16, 3.14.8 and 3.15.0 all four fail with `TypeError: Type parameter with a default follows TypeVarTuple`. The `T = int` case should fail (spec says error), but the other three are spec-valid classes. The check is in `typing._collect_type_parameters` (traceback line 291 on 3.13.16) and does not distinguish `ParamSpec` from `TypeVar`.

### 5.5 mypy at the use site

`repro/m1_mypy_use_site.py` (class with methods returning `tuple[*Ts]` and `Callable[P, None]`) and `repro/m2_mypy_legacy.py` (`evidence/32-`): mypy 2.4.0, 2.4.1 and master report, for `Foo[int, str]()` and `Foo[int, str, [bytes]]()`, `Can only replace ParamSpec with a parameter types list or another ParamSpec, got "str"  [misc]` (lines 13 and 17) and then `assert-type` errors: `tuple[Any, ...]` instead of `tuple[int, str]`, `def (*Any, **Any) -> None` instead of `Callable[[float, bool], None]` / `Callable[[bytes], None]`. That is 6 errors per version for the PEP 695 form and 3 for the legacy form (one `[valid-type]` plus two `assert-type`). pyright: 0 errors on both files. ty 0.0.97: `All checks passed!` on both. For the spec example verbatim (`s1_spec_example.py`) mypy gives `Foo[*tuple[Any, ...], Any]` for `Foo[int, str]()` and `Foo[int, str, [bytes]]()`, `Foo[int, str, [float, bool]]` for `Foo()`; ty reveals `Foo[int, str, (float, bool, /)]`, `Foo[int, str, (bytes, /)]` and `Foo[int, str, (float, bool, /)]`; pyright reveals `Foo[int, str, (float, bool)]`, `Foo[int, str, (bytes)]` and `Foo[int, str, (float, bool)]`.

### 5.6 Duplicate search (evidence `40-`, `41-`, `42-`, `56-`)

- astral-sh/ty and astral-sh/ruff issues, 9 phrases each: `invalid-type-variable-default`, `TypeVarTuple default`, `TypeVarTuple ParamSpec default`, `TypeVarTuple follows default`, `type parameter default follows TypeVarTuple`, `cannot follow a TypeVarTuple`, `ParamSpec default TypeVarTuple`, `PEP 696 TypeVarTuple`, `typevartuple default regression`. Plus `gh issue list --search` on ty titles: `ParamSpec default`, `TypeVarTuple`, `default ... typevar`. Hits that mention TypeVarTuple defaults: ty#4047 (open, "TypeVarTuple defaults referencing other TypeVars"), #4045 (closed, hang), #2874 and #2429 (closed, other default checks), #1685 (closed). None reports ParamSpec-after-TypeVarTuple, and no issue reports the 0.0.94 change as a regression. The fix is PR ruff#29753 (merged), read in full above.
- python/mypy issues, 13 phrases (including `ParamSpec default TypeVarTuple`, `Can only replace ParamSpec with a parameter types list`, `defaults following TypeVarTuple`, `generics_defaults TypeVarTuple`, `PEP 696 ParamSpec default after TypeVarTuple`, `TypeVarTuple default`, `ParamSpec default`) and 2 PR phrases: nothing about this subscript. Related: mypy#14851 (closed 2026-06-02; comment by ilevkivskyi: "all the aspects of TypeVar defaults are supported in current master", which this result contradicts), #12981 and #20455 (closed), #20478 (closed), #17453 (open, unrelated inference), #15096 (closed).
- python/cpython issues, 9 phrases, and PRs, 2 phrases (`Type parameter with a default follows TypeVarTuple`, `ParamSpec default follows TypeVarTuple`, `TypeVarTuple default ParamSpec Generic`, `PEP 696 ParamSpec TypeVarTuple typing`, ...): no issue for this error message. Nearest: #158981 (open, "Subscripting a generic alias without an argument for a parameter with a default fails"; not the same), #124787, #91162.
- python/typing: **#2211 (open), "`generics_defaults.py` mandates that type checkers should allow a class that raises `TypeError` at runtime"**, created 2026-03-08. It shows `class A(Generic[*Ts, P])` with `P = ParamSpec("P", default=[int, str])` failing on Python 3.14.0 with the same message; Jelle Zijlstra replied "I think this is a bug in the runtime, yes" and linked the spec section. This is the duplicate for the runtime half.
- python/typing conformance results (`results/mypy|pyright|ty/generics_defaults.toml` on `main`, fetched 2026-11-05 through raw.githubusercontent.com): mypy "Partial", with the three errors on lines 203 to 205 that match what I reproduce; pyright "Pass"; the ty file in that repo is older than 0.0.97 (it still lists failures on 203 to 205 and the missing line-188 error, both different from what I measured on 0.0.97). I could not tell which tool versions those result files used.

### 5.7 Verdict

- ty: NOT-A-BUG. Valid class, no diagnostic is required. No draft.
- CPython `typing`: DUPLICATE (python/typing#2211, acknowledged). I found no python/cpython issue; whether to open one is the user's call. No draft written.
- mypy: STILL-BUG-NEW, drafted as draft 5 in `day3-issue-drafts.md`. Caveat: the failure is visible in the public conformance results, so the mypy team may already know; I found no issue for it.
- pyright: correct.

## 6. Changes made

- `campaign/day3-issue-drafts.md`: header status block and a "Day 6 verdict" column; user-verified notes on drafts 1 and 2; drafts 3 and 4 re-verified (version lines, confirmed cause for draft 3, search summary for both); new draft 5 (mypy); a "Not drafted" bullet for the ty part of the Callback candidate.
- `campaign/day6-verification.md` (this file), `campaign/day6-run-log.md`, `campaign/day6/repro/`, `campaign/day6/evidence/`.
- Day 5 files (`day5-ty97-bump.md`, `day5-report.md`) were not edited. Their "possible regression" wording for `adbc14c6128a` is superseded by section 5.2 of this file.
- Not changed: `known_upstream.json`. The pipeline still lists the Callback finding as live (NEEDS_HUMAN). Closing it with an entry (python/typing#2211 for the runtime part) is a KB change for the triage owner.

## 7. Not verified

- ty `main` (unreleased) and any ty nightly: not tested for drafts 3/4 or the Callback case.
- Playground reproductions (play.ty.dev, mypy-play): not made; the `<PLAYGROUND LINK>` placeholders are open (drafts 3, 4, 5).
- Issue comments: I read the bodies and comments of the issues named above through `gh issue view --json comments`, but GitHub search is fuzzy and returns few hits for exact phrases, so a duplicate under unusual wording cannot be ruled out. Run one last search on the exact title before filing.
- ruff#26040: why it was closed is unknown; I only know it was closed by its author without comment.
- The spec's example gives the TypeVarTuple a default; the Callback class has none (see 5.3).
- The conformance result files may have been produced with other tool versions than the ones I ran.
- pyright's tracker and the CPython `typing` fix status (3.16 / main branch) were not searched or tested; the runtime probe covers 3.13.16, 3.14.8 and 3.15.0 only.
- Why pyright did not report line 45 of `hash_ctrl.py` was not investigated.
