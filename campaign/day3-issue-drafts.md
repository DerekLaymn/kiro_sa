# Issue drafts, Day 3 candidates (Day 4 consolidate, Day 6 re-verification)

Date: 2026-11-05. Tools: ty 0.0.84 and 0.0.97 (pinned since Day 5, also the latest release), mypy 2.4.0 / 2.4.1 / master 2.5.0+dev.879da562, pyright 1.1.414, CPython 3.13.16, Linux.

**Day 6 status (details and command output: `campaign/day6-verification.md`, raw output: `campaign/day6/evidence/`).**
Drafts 1 and 2 were verified on the ty playground by the user; Day 6 did not re-run them. Drafts 3 and 4 were re-run on ty 0.0.97, mypy 2.4.0, 2.4.1 and mypy master, with a fresh upstream search: both are still new. Draft 5 (mypy, ParamSpec default after a TypeVarTuple) was added on Day 6 from the `adbc14c6128a` "Callback" candidate. The ty half of that candidate is not a ty bug and has no draft (see "Not drafted"). The draft bodies were edited by hand on Day 6; `/tmp/cons/build.py` was not re-run.
**Day 7 status (details: `campaign/day7-verification.md`, raw output: `campaign/day7/partD/evidence/`).** Drafts 6 (ty) and 7 (pyright) were added from the Part C candidates. They were run on CPython 3.13.16, ty 0.0.97 and 0.0.98 (0.0.98 was released on 2026-11-05 and is the latest), mypy 2.4.0, 2.4.1 and master, pyright 1.1.414 (latest). The "Day 6 verdict" column of rows 6 and 7 holds the Day 7 verdict. Drafts 1 to 5 were not re-run.
**Day 8 status (details: `campaign/day8-verification.md`, raw output: `campaign/day8/phase6/`).** Draft 8 (mypy) was added from class F. Drafts 6 and 7 were re-run with four and one more Day-8 program (ty 0.0.97/0.0.98, pyright 1.1.414) and still reproduce; see the Day 8 status at the end of this file.
**Day 9 status (details: `campaign/day9-verification.md`, raw output: `campaign/day9/phase6/`).** Drafts 9 (mypy, comparison priority for operands of the same type) and 10 (mypy, `possibly-undefined` after a swallowing `with`) were added. Tools: CPython 3.13.16, ty 0.0.97 (the pin) and 0.0.99 (the newest release, 2026-11-06, beside the pin), mypy 2.4.0, 2.4.1 and master 2.5.0+dev.879da562, pyright 1.1.414. The author listing of the drafting account (`campaign/day9/phase6/search/author.out`, 2026-11-06) shows drafts 1 to 5 filed: ty#4933 (draft 1), ty#4934 (draft 2, closed), mypy#22377 (draft 3), ty#4941 (draft 4), mypy#22375 (draft 5). Drafts 6, 7, 8 are still not filed. The Day-9 program `d4v_metaclass_reflected_op__mut0_dcb547ed` is another instance of draft 3 (mypy#22377).
The drafts are concatenated without edits to the issue bodies from `campaign/day4/issue-drafts-v1.md` (draft 1), `-v2.md` (draft 2) and `-v3.md` (drafts 3 and 4). Each draft sits in a fenced block: copy the contents (without the fence lines) into the issue body, set the title from the "Title" line, and replace `<PLAYGROUND LINK>`. NOT FILED. Nothing here was posted anywhere, and no GitHub write call was made. (The format reference `temp/issue_drafts.md` does not exist in the repo; the format of the v1 to v3 drafts is kept.)

| # | Tool | Bug | Class | Conf | Duplicate check | Day 6 verdict | Source |
|---|---|---|---|---|---|---|---|
| 1 | ty | stack overflow when a class is checked against a protocol whose method annotates `self` as `Stream[Stream[T]]` | CRASH | 0.80 | none found. Related: open #4746, open #4882, closed #4694, #4863 | verified by the user on the playground, not re-run | v1 draft 1 |
| 2 | ty | alias narrowing (`is_none = x is None`) survives a reassignment that reaches the use over a loop back edge | INCORRECT_INFERENCE / FALSE_NEGATIVE | 0.9 | none found. Related: ty#4379, ty#719, ruff#24302, ty#2792 | verified by the user on the playground, not re-run | v2 draft 1 |
| 3 | mypy | reflected operator of a subclass metaclass ignored for class-object operands (`A * B`) | FALSE_POSITIVE | 0.7 | none found (Day 4: 12 phrases; Day 6: 20+ more, issues and PRs). Related: mypy#19006, #4789, #5491 | STILL-BUG-NEW, cause now confirmed by instrumenting mypy master | v3 draft 1 |
| 4 | ty | class with `__eq__` and no `__hash__` accepted as `Hashable` | FALSE_NEGATIVE | 0.7 | none found (Day 6: 40+ queries on ty and ruff, issues and PRs). Related: ty#3781, ty#4157 (fixed by ruff#27441), ruff#26040 (closed, unmerged); mypy#20230 is the mypy-side report | STILL-BUG-NEW | v3 draft 2 |
| 5 | mypy | `Foo[int, str]` on a class with a `TypeVarTuple` followed by a defaulted `ParamSpec` is rejected and inferred as `Any` | FALSE_POSITIVE / INCORRECT_INFERENCE | 0.7 | none found in python/mypy (13 issue phrases, 2 PR phrases). Known in the public conformance results (`generics_defaults.py` L203 to L205); runtime half is python/typing#2211 | STILL-BUG-NEW (mypy only) | Day 6, program `adbc14c6128a` |
| 6 | ty | `except` clause sees the old value after a nested unpacking target failed half-way through an assignment | INCORRECT_INFERENCE | 0.5 | none found (18 term sets on ty, ruff, pyright, mypy). Related: ty#225 (closed), ruff#27471 (merged, flat unpacking only) | STILL-BUG-NEW (Day 7, ty 0.0.97 and 0.0.98) | Day 7, `partial_unpack_exception` |
| 7 | pyright | `RangeError: Maximum call stack size exceeded` when a descriptor `__get__` is decorated by a class-body function without `self` and the attribute is accessed | CRASH | 0.8 | none found. Related: open #11961 and PR #11965 (constructor path, different frames), closed #9283, #9740, #6178, #6783, #5139, #4798, #5090 | STILL-BUG-NEW (Day 7, pyright 1.1.414 = latest) | Day 7, `d3p_descriptors_decorated_get__mut1_040cc0db` |
| 8 | mypy | overloaded `__post_init__` of a dataclass: every overload item is checked against the InitVar signature, so an item without the `InitVar` type gets `[override]` although another item takes it | FALSE_POSITIVE | 0.6 | none found (16 term sets on python/mypy, 5 on ty and pyright; read #15498, #15503, #9254, #16293, #15515, #12379) | STILL-BUG-NEW (Day 8, mypy 2.4.0, 2.4.1, master) | Day 8, class F, `rsv_dataclasses_223fff8f__mut0_3b9111ba` |
| 9 | mypy | `a < b` for two operands of the same type tries `b.__gt__` first when `__lt__` and `__gt__` are defined in different classes of the MRO; the inferred type is that of the wrong method | FALSE_POSITIVE / INCORRECT_INFERENCE | 0.6 | none found (13 issue and 6 PR queries on python/mypy, 2+2 issue queries on ty and pyright, 1 ruff PR query). Same function, different bugs: mypy#22377 (draft 3), #19006 (fixed), #22316 and PR #22380 (message text) | STILL-BUG-NEW (Day 9, mypy 2.4.0, 2.4.1, master) | Day 9, `d3p_inheritance_mro_total_ordering_inherited_lt__mut0_73c4aa3f` |
| 10 | mypy | `possibly-undefined` does not report a name assigned in a `with` block whose `__exit__` returns `bool` (`contextlib.suppress`, user classes), although the name is unbound after a swallowed exception | FALSE_NEGATIVE (opt-in check) | 0.4 | none found (8 issue and 3 PR queries on python/mypy, 5 on ty, 3 on pyright, 2 ruff PR queries). Related: closed mypy#7577, #10896, #7726, #15715 (`Missing return statement` after such blocks, handled by the type checker) | STILL-BUG-NEW (Day 9, mypy 2.4.0, 2.4.1, master; ty and pyright report it) | Day 9, `context_managers/gen0_b82d2e9e`, `gen21_6ee04c3a` |

Not drafted, with reasons (all duplicates, fixed, or not bugs):

- **Day 6, `adbc14c6128a` "Callback" candidate, ty part: NOT-A-BUG.** `class Callback[*Ts, **P = [bool]]` is valid under the typing spec ("Defaults following TypeVarTuple": a defaulted `ParamSpec` may follow a `TypeVarTuple`). ty 0.0.84 to 0.0.93 rejected it (over-strict), and ty 0.0.94 stopped on purpose (ruff#29753: "Both allow a defaulted `ParamSpec`"). Pyright 1.1.414 also accepts it. The CPython 3.13.16, 3.14.8 and 3.15.0 `TypeError` is a runtime bug that is already reported as python/typing#2211 (acknowledged by Jelle Zijlstra as a runtime bug). I found no python/cpython issue for it.
- Self-referential `__call__` attribute (`__call__: "C"`, `Self | None`, mutual pairs): open ty#4148 (ty) and python/mypy#22361 (mypy).
- `partial | None` in a loop: ty 0.0.84 panics, fixed in ty 0.0.85.
- Stale alias condition after a method call and read-only property `Never`: ty#2792. Tuple-subclass constant fold: ty#2171. Flag combination `Never`: ty#876. Metaclass `A | B` in ty: ty#4683. IntEnum alias: mypy#16830, mypy#21117, pyright#11100. Recursive alias reveal: mypy#2008. `__hash__` None reveal: mypy#20230.

- **Day 7 (details: `campaign/day7-verification.md`).** mypy accepts `__eq__` without `__hash__` as `Hashable`: DUPLICATE of python/mypy#2455 and #18622, fix pending in open PR #19168 (no draft; draft 4 is the ty counterpart and stays). ty skips the read-only property assignment after a descriptor `__set__` changed a narrowed attribute: ty#2792. pyright `Gauge.level` is `Clamped | int` for a data descriptor assigned in `__init__`: pyright#11382. ty `object + object` after `case (a, b)` on a union with a non-final class: design, ty#1578.

- **Day 8 (details: `campaign/day8-verification.md`).** ty `Never` for a read-only property after contradicting asserts and a mutating call: ty#2792 (also ty#4345, ty#4880). ty accepts `x.add(Node())` for `add(self, c: 'Self')` on a subclass: ty#4656 (closed, intended). ty/pyright `norm(v)` for a union argument with a catch-all `T` overload (spec step 2 picks it, mypy does union math first): design. mypy reveals `str` for `k: str = 'int'` (mypy erases the literal on assignment, ty and pyright keep it): design. ty accepts `Desc.__delete__(Desc(), h, 1)` behind an untyped decorator: return type inference is off by default (ty#4739, ty#1971), it reports the call with `analysis.return-type-inference = "always"`. ParamSpec self-annotation family (e1 to e4): ty#3666 and design, no new bug.

Confidence for drafts 3 and 4 is 0.7: the construct in draft 3 is rare and the source location is a hypothesis; the ty maintainers may fold draft 4 into the hashability work in ty#3781.

Build: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.venv/bin/python /tmp/cons/build.py` (concatenation and renumbering only).

---

## 1. ty: nested protocol receiver

**Day 6 verdict: verified by the user on the ty playground; not re-run in Day 6.** (Day 5 note: the overflow still reproduces on ty 0.0.97, `day5-ty97-bump.md`.)

**Duplicate check:** Checked: ty tracker snapshot of 4060 issues (title and body regexes), `gh search issues` on astral-sh/ty with 12 phrases, `gh search prs` on astral-sh/ruff, full reads of ty#4746, #4882, #4694, #4863. Result: no duplicate. Nearest: open #4746 (false positive, non-growing receiver), open #4882 (different program), closed #4694 and #4863 (need extra members and a factory call). Source: `campaign/day4/verify-v1.md` C2 (5).

**Not checked:** issue comments beyond the issues read in full; PRs that the search phrases did not surface; discuss.python.org; playgrounds (play.ty.dev, mypy-play; the `<PLAYGROUND LINK>` placeholder is still open, UNVERIFIED-PLAYGROUND); ty `main` (only release 0.0.97 was tested). Run one last search on the exact title before submitting.

Title: `Stack overflow when a class is assigned to a protocol whose method annotates self as a nested specialization of the protocol`

````markdown
### Summary

ty aborts with a stack overflow when a class is checked against a protocol that has a method whose `self` is annotated as the protocol specialized with itself (`Stream[Stream[T]]`). The protocol definition alone and the method call alone do not crash. The assignment is enough.

```py
from typing import Protocol


class Stream[T](Protocol):
    def flatten(self: "Stream[Stream[T]]") -> None: ...


class Impl:
    def flatten(self) -> None: ...


x: Stream[int] = Impl()
```

```console
$ ty check --python-version 3.13 test_bug.py

thread '<unknown>' has overflowed its stack
fatal runtime error: stack overflow, aborting
```

Checking `Impl` against `Stream[int]` binds `flatten` with the receiver `Stream[Stream[int]]`. That needs `Impl` to match `Stream[Stream[int]]`, which needs the receiver `Stream[Stream[Stream[int]]]`, and so on. The type grows on every round, so the "assume the relation holds when the decision depends on itself" step never sees a repeated relation.

What I tried (all on 0.0.84 and 0.0.97, same result):

- Crashes too: `self: "Stream[list[T]]"`, `"Stream[tuple[T]]"`, `"Stream[dict[str, T]]"`; old-style `TypeVar("T", covariant=True)` with `Protocol[T]`; a generic `Impl[T]`; a method that returns `T`; passing `Impl()` as an argument to `def use(v: Stream[int])`, returning it from a function annotated `-> Stream[int]`, or putting it in a `list[Stream[int]]`.
- Does not crash: the protocol definition alone, `def use(value: Stream[int]) -> None: ...` without a call, a program that only calls `value.flatten()` on a `Stream[int]` parameter.
- Does not crash but rejects `Impl` (mypy and pyright accept it): `self: "Stream[T | None]"` and a method-level type variable, `def flatten[U](self: "Stream[Stream[U]]") -> None`. That looks like the problem in #4746, which has the same shape with a non-growing receiver.

mypy 2.4.0, 2.4.1 and master accept the program; pyright 1.1.414 accepts it. CPython runs it without error.

The related reports #4694 and #4863 (closed) also use `self: Stream[Stream[U]]` but need extra members and a factory call; this program has neither and still overflows on 0.0.97. #4882 (open) is a different program, also a stack overflow in protocols.

**Expected:** no crash. Accepting the assignment (as mypy and pyright do) or reporting a diagnostic would both be fine.

Playground: <PLAYGROUND LINK>

### Version

ty 0.0.84 and ty 0.0.97
````

---

## 2. ty: aliased-condition narrowing ignores a reassignment on a loop back edge

**Day 6 verdict: verified by the user on the ty playground; not re-run in Day 6.**

**Duplicate check:** Checked: ty tracker dump of 4060 issues (9 regexes on titles and bodies), `gh search issues --repo astral-sh/ty` with 7 phrases, `gh search prs --repo astral-sh/ruff` with 3 phrases, python/mypy and microsoft/pyright with 2 phrases each. Result: no match. Related but different: ty#4379 (closed, direct narrowing in loops), ty#719 and ruff#24302 (the alias feature), ty#2792 (open, attribute narrowing across calls). Source: `campaign/day4/verify-v2.md` 1b.5.

**Not checked:** issue comments beyond the issues read in full; PRs that the search phrases did not surface; discuss.python.org; playgrounds (play.ty.dev, mypy-play; the `<PLAYGROUND LINK>` placeholder is still open, UNVERIFIED-PLAYGROUND); ty `main` (only release 0.0.97 was tested). Run one last search on the exact title before submitting.

Title: `Aliased conditional narrowing is not invalidated when the target is reassigned later in the same loop body`

````markdown
### Summary

When a narrowing check is stored in a variable (an "aliased conditional expression", added in astral-sh/ruff#24302) and the narrowed variable is reassigned at the end of a loop body, ty keeps the narrowing on the next iteration. The reassignment reaches the use through the loop back edge, so `x` can be `None` there. ty reports no error, and CPython raises `TypeError`.

```py
def f(x: int | None) -> int:
    is_none = x is None
    total = 0
    for _ in range(2):
        if not is_none:
            total += x + 1
        x = None
    return total


print(f(3))
```

```console
$ ty check --python-version 3.13 test.py
All checks passed!

$ python test.py
TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'
```

With `reveal_type(x)` instead of the addition, ty reveals `int`; the second iteration sees `None`.

mypy and pyright both report the `None` operand (mypy: `Unsupported operand types for + ("None" and "int")`, pyright: `reportOptionalOperand`). They do not implement aliased conditions for this case at all, so I do not take that as evidence for how ty should behave. The evidence is the runtime error and ty's own contract: the `narrow/aliased_conditions.md` mdtest section "Narrowing is invalidated when target is reassigned" says that narrowing does not take place if the target is reassigned between the definition of the alias and its use. That holds for straight-line code and for an `if` branch, but not when the reassignment arrives over a loop back edge.

Same behaviour with:

- a `while` loop instead of `for`
- an attribute target: `is_none = a.x is None`, then `a.x = None` at the end of the loop body
- an `isinstance` alias: `is_int = isinstance(a.x, int)`, then `a.x = "s"` at the end of the loop body

Cases that are handled correctly, for comparison:

- direct narrowing (`if x is not None:` before the loop, `x = None` at the end of the body): `int | None`
- the reassignment placed before the use inside the body: `None`
- the loop variable itself as the target (`for x in xs:`): `int | None`
- reassignment inside an `if` branch before the use: `int | None`

The existing direct-narrowing fix for loops (#4379) does not seem to cover the alias path.

Playground: <PLAYGROUND LINK>

### Version

ty 0.0.84 and ty 0.0.97
````

---

## 3. mypy: reflected operator on class objects whose metaclasses are related

**Day 6 verdict: STILL-BUG-NEW.** Re-run on mypy 2.4.0, 2.4.1 and master 2.5.0+dev.879da562 (GitHub master HEAD on 2026-11-05): same two errors on all three. CPython 3.13.16 prints `str`. The suspected cause is now confirmed: with `covers_at_runtime` instrumented on master, the class-object case calls `covers_at_runtime(def () -> B, def () -> A)` and gets `False`; the instance control gets `True`. Day 6 search: python/mypy issues and PRs with 25+ phrases (metaclass, `__rmul__`, `__ror__`, reflected, reverse operator, `covers_at_runtime`, `check_op_reversible`), nothing about the subclass-metaclass priority rule. Nearest: #4789 and #4929 (closed, metaclass operators on `Type[Foo]`), #19006 (closed, tuple subclass priority, fixed by PR #19046), #5491 (closed, cleanup of metaclass kludges in `check_op_reversible`). Evidence: `campaign/day6-verification.md`.

**Duplicate check (Day 4):** Checked: `gh search issues` on python/mypy with 12 phrases, `gh search prs --repo astral-sh/ruff`, best three hits per tool read with `gh issue view`. Result: no duplicate. Related but different: mypy#4789 and #4929 (operators on `Type[Foo]`), mypy#19006 (reflected priority for tuple subclasses, fixed), pyright#4088, #3368, #10644 (instances, declined by maintainer). Source: `campaign/day4/verify-v3.md` 2.5.

**Not checked:** issue comments beyond the issues read in full; PRs that the search phrases did not surface; discuss.python.org; playgrounds (mypy-play; the `<PLAYGROUND LINK>` placeholder is still open, UNVERIFIED-PLAYGROUND). mypy master 2.5.0+dev.879da562 was tested with the same result. Run one last search on the exact title before submitting.

Title: `Binary operator on class objects ignores the right operand's reflected method when its metaclass subclasses the left operand's metaclass`

````markdown
**Bug Report**

When both operands of a binary operator are classes (not instances) and the metaclass of the right operand is a subclass of the metaclass of the left operand that overrides the reflected method, CPython calls the reflected method first (Python data model, note under `object.__radd__`: a right operand whose type is a subclass of the left operand's type and that provides a different reflected method gets called before the left operand's method). mypy applies this rule to instances but not to class objects, so the inferred type is the result of the left operand's method.

**To Reproduce**

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

For comparison, the same hierarchy with instances is handled correctly:

```python
class L:
    def __mul__(self, other: object) -> int: ...
class R(L):
    def __rmul__(self, other: object) -> str: ...

s: str = L() * R()   # no error, as it should be
```

**Actual Behavior**

```
meta_bug.py:18: error: Incompatible types in assignment (expression has type "int", variable has type "str")  [assignment]
meta_bug.py:19: error: Expression is of type "int", not "str"  [assert-type]
Found 2 errors in 1 file (checked 1 source file)
```

`python meta_bug.py` prints `str`.

**Expected Behavior**

No errors; `A * B` is inferred from `RightMeta.__rmul__`, as for `L() * R()`. Unlike an instance annotated `L`, the expressions `A` and `B` name exactly one class each, so the metaclasses are known precisely and the call order is decidable. The same happens with `__or__`/`__ror__` on class objects.

Cause: in `check_op_reversible` the priority branch is guarded by `covers_at_runtime(right_type, left_type)`. For class objects both operand types are type-object callables, and logging the call on master shows `covers_at_runtime(def () -> B, def () -> A)` returns `False`, so the metaclass relation is never looked at. For the `L() * R()` version the same call returns `True`.

pyright reports the same two errors; its maintainers consider the instance version "as designed" (pyright#4088, #3368), so this report is only about mypy's inconsistency between instances and class objects. ty accepts the program.

**Your Environment**

- Mypy version used: 2.4.0, 2.4.1 and master 2.5.0+dev.879da562
- Mypy command-line flags: `--python-version 3.13 --no-incremental`
- Python version used: 3.13.16
- OS: Linux

mypy-play: <PLAYGROUND LINK>
````

---

## 4. ty: class with `__eq__` and no `__hash__` is accepted as `Hashable`

**Day 6 verdict: STILL-BUG-NEW.** Re-run on ty 0.0.97 (latest release) and 0.0.84: `All checks passed!` for `need(Plain())` and `need(Sub())`; CPython 3.13.16 raises `TypeError: unhashable type: 'Plain'`; pyright 1.1.414 reports both calls; mypy 2.4.0, 2.4.1 and master accept them. The dataclass control and an explicit `__hash__ = None` class are rejected by ty 0.0.97, a class with only `__ne__` or `__lt__` is accepted (correct). Day 6 search: astral-sh/ty issues and astral-sh/ruff PRs with 40+ queries (Hashable, `__hash__`, `__eq__`, unhashable, hashability, implicit `__hash__`, eq without hash), issues #4157, #4196, #3781, #4748, #4754 and PRs ruff#27441, #29471, #26039, #26040, #26367 read. None covers a class that gets `__hash__ = None` implicitly from `__eq__`. Nearest: ty#4157 (closed, fixed by ruff#27441, which handles explicit `ClassVar[None]`, built-in containers and mutable dataclasses; its diff has no `__eq__` case), and ruff#26040 (closed without merge or comment on 2026-10-18; its text names the `__eq__` case, for union simplification only). The `__eq__` case is not fixed on a merged PR as of 2026-11-05. Not tested: ty `main` (unreleased). Evidence: `campaign/day6-verification.md`.

**Duplicate check (Day 4):** Checked: ty tracker dump (regexes on `__eq__`, `__hash__`, `unhashable`, `hashab`), `gh search issues` on astral-sh/ty with 5 or more phrases, `gh search prs --repo astral-sh/ruff` with 5 phrases, best three hits read. Result: no duplicate. Related: ty#3781 (set/dict displays with mutable dataclasses), ruff#27441 (`Hashable` for ClassVar None, containers, mutable dataclasses), mypy#20230, #18622, #2455 (mypy side of the same rule). Source: `campaign/day4/verify-v3.md` 4.5.

**Not checked:** issue comments beyond the issues read in full; PRs that the search phrases did not surface; discuss.python.org; playgrounds (play.ty.dev, mypy-play; the `<PLAYGROUND LINK>` placeholder is still open, UNVERIFIED-PLAYGROUND); ty `main` (only release 0.0.97 was tested). Run one last search on the exact title before submitting.

Title: `Class that defines __eq__ without __hash__ is accepted where Hashable is required`

````markdown
### Summary

A class that defines `__eq__` and does not define `__hash__` gets `__hash__ = None` from Python, so its instances are unhashable. ty accepts such an instance (and an instance of a subclass that does not restore `__hash__`) for a `Hashable` parameter. ty already rejects the same call for a mutable dataclass (astral-sh/ruff#27441), which gets the same implicit `__hash__ = None`.

```py
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


need(Keyed())  # fine
need(Plain())  # runtime: TypeError: unhashable type: 'Plain'
need(Sub())    # runtime: TypeError: unhashable type: 'Sub'
```

```console
$ ty check --python-version 3.13 test_bug.py
All checks passed!

$ python test_bug.py
TypeError: unhashable type: 'Plain'
```

`reveal_type(Plain.__hash__)` gives `def __hash__(self) -> int`; for `@dataclass class Record` ty reveals `None`. With the same file but `need(Record("a"))`, ty reports `invalid-argument-type`.

pyright reports an error for `need(Plain())` and `need(Sub())`. mypy accepts them (python/mypy#20230, #18622, #2455).

This is separate from astral-sh/ty#3781, which is about `{obj}` and `{obj: ...}` displays; the same missing rule also lets `{Plain()}` pass, but the minimal case here is the `Hashable` protocol check that ty already implements.

**Expected:** `invalid-argument-type` for `need(Plain())` and `need(Sub())`, not for `need(Keyed())`. A class that defines only `__ne__` or `__lt__` stays hashable and must not be flagged.

Playground: <PLAYGROUND LINK>

### Version

ty 0.0.84 and ty 0.0.97
````

---

## 5. mypy: `Foo[int, str]` fails when a TypeVarTuple is followed by a ParamSpec with a default

**Day 6 verdict: STILL-BUG-NEW (mypy only).** Source: seed `adbc14c6128a` (`class Callback[*Ts, **P = [bool]]`), reduced on Day 6. Re-run on mypy 2.4.0, 2.4.1 and master 2.5.0+dev.879da562: the same three errors on all of them (`campaign/day6/evidence/32-mypy-use-site-assert-type.txt`). Pyright 1.1.414 and ty 0.0.97 accept the program and infer `Foo[int, str, (float, bool)]`. The typing spec ("Defaults following TypeVarTuple") and PEP 696 both say this class is valid and give `Foo[int, str]` as `Ts = (int, str), P = [float, bool]`.

**Duplicate check:** Checked: python/mypy issues with 13 phrases (ParamSpec default, TypeVarTuple default, PEP 696, "Can only replace ParamSpec", conformance, class specialization and variants), python/mypy PRs with 2 phrases, the closing comments of mypy#14851 read. Result: no issue about this subscript. Related: mypy#14851 (closed 2026-06-02; the last comment says all aspects of TypeVar defaults are supported on master, which does not match this result), mypy#12981 and #20455 (closed, TypeVarTuple defaults), mypy#20478 (closed, ParamSpec default value). The python/typing conformance results for mypy (`results/mypy/generics_defaults.toml`, fetched 2026-11-05) list the same three errors on the spec test's lines 203 to 205 and say "Does not fully support defaults on `TypeVarTuple` and `ParamSpec`", so the maintainers may already treat it as a known gap. Related, not the same: python/typing#2211 (open): CPython rejects this class at runtime, which Jelle Zijlstra called a runtime bug.

**Not checked:** issue comments beyond the issues read in full; PRs that the search phrases did not surface; discuss.python.org; mypy-play (the `<PLAYGROUND LINK>` placeholder is still open, UNVERIFIED-PLAYGROUND). Run one last search on the exact title before submitting.

Title: `Subscripting a class with a TypeVarTuple followed by a defaulted ParamSpec reports "Can only replace ParamSpec" and infers Any`

````markdown
**Bug Report**

PEP 696 and the typing spec (section "Defaults following TypeVarTuple") allow a `ParamSpec` with a default after a `TypeVarTuple`. The spec's example also gives the `TypeVarTuple` a default; the result below is the same with and without it. mypy accepts the class definition, but subscripting it gives an error: the last type argument is taken as the argument for the `ParamSpec`, and the result is `Foo[*tuple[Any, ...], Any]`.

**To Reproduce**

```python
from collections.abc import Callable
from typing import assert_type


class Foo[*Ts, **P = [float, bool]]:
    def args(self) -> tuple[*Ts]:
        raise NotImplementedError

    def fn(self) -> Callable[P, None]:
        raise NotImplementedError


foo = Foo[int, str]()
assert_type(foo.args(), tuple[int, str])
assert_type(foo.fn(), Callable[[float, bool], None])

bar = Foo[int, str, [bytes]]()
assert_type(bar.args(), tuple[int, str])
assert_type(bar.fn(), Callable[[bytes], None])
```

The old-style spelling (`Ts = TypeVarTuple("Ts")`, `P = ParamSpec("P", default=[float, bool])`, `class Foo(Generic[Unpack[Ts], P])`, a parameter annotated `Foo[int, str]`) gives the same message on the subscript.

**Actual Behavior**

```
t.py:13: error: Can only replace ParamSpec with a parameter types list or another ParamSpec, got "str"  [misc]
t.py:14: error: Expression is of type "tuple[Any, ...]", not "tuple[int, str]"  [assert-type]
t.py:15: error: Expression is of type "def (*Any, **Any) -> None", not "Callable[[float, bool], None]"  [assert-type]
t.py:17: error: Can only replace ParamSpec with a parameter types list or another ParamSpec, got "str"  [misc]
t.py:18: error: Expression is of type "tuple[Any, ...]", not "tuple[int, str]"  [assert-type]
t.py:19: error: Expression is of type "def (*Any, **Any) -> None", not "Callable[[bytes], None]"  [assert-type]
```

With a default on the `TypeVarTuple` too (`class Foo[*Ts = *tuple[int, str], **P = [float, bool]]`, the example from the spec) the result is the same. This is also what the typing conformance suite shows for mypy on `generics_defaults.py`, lines 203 to 205.

**Expected Behavior**

No errors. `Foo[int, str]` is `Ts = (int, str), P = [float, bool]` and `Foo[int, str, [bytes]]` is `Ts = (int, str), P = [bytes]`, as in the spec. A `ParamSpec` argument has to be a list, `...` or another `ParamSpec`, so `str` cannot be one and there is no ambiguity with the `TypeVarTuple`. pyright 1.1.414 and ty 0.0.97 accept the program.

Note: CPython 3.13.16, 3.14.8 and 3.15.0 raise `TypeError: Type parameter with a default follows TypeVarTuple` when this class is created (python/typing#2211, a runtime bug), so the snippet is for type checking only.

**Your Environment**

- Mypy version used: 2.4.0, 2.4.1 and master 2.5.0+dev.879da562
- Mypy command-line flags: `--python-version 3.13 --no-incremental`
- Python version used: 3.13.16
- OS: Linux

mypy-play: <PLAYGROUND LINK>
````

---

## 6. ty: `except` clause ignores bindings made before a nested unpacking target fails

**Day 7 verdict: STILL-BUG-NEW.** Source: Part C program `tuples_unpacking__partial_unpack_exception__mut0_1a265ba6` (3 mutants, same finding), reduced by hand. ty 0.0.97 and 0.0.98 (latest) reveal `Literal[1]`; CPython has `'bad'`; mypy 2.4.0, 2.4.1 and master reveal `int | str`; pyright 1.1.414 reveals `Literal[1]`. Evidence: `campaign/day7-verification.md` (D7-1), `campaign/day7/partD/evidence/results/c1.txt`, `c1b.txt`, `c1g.txt`.

**Duplicate check:** Checked: `gh search issues` and `gh search prs` on astral-sh/ty, astral-sh/ruff, microsoft/pyright and python/mypy with 18 term sets (tuple unpacking except, partial assignment, assignment raises in try, chained assignment, nested unpacking, exception handler flow, unpack ValueError, binding in try block, ...), web search once. Read ty#225 (closed, fixed by ruff#27471), ty#762, ruff#27471 (merged 2026-08-12, "Model try exception flow with operation checkpoints", its mdtest "Unpacking can raise" covers only the flat `first, second = values`), mypy#13123. Result: no issue or PR for the nested case. This is an edge of the ruff#27471 work and may be handled there.

**Not checked:** issue comments beyond the issues read in full; PRs that the search phrases did not surface; discuss.python.org; playgrounds (play.ty.dev; the `<PLAYGROUND LINK>` placeholder is still open, UNVERIFIED-PLAYGROUND); ty `main` (only releases 0.0.97 and 0.0.98 were tested). Run one last search on the exact title before submitting.

Title: `except clause does not see the earlier targets of a tuple assignment whose nested unpacking raises`

````markdown
### Summary

In a tuple assignment with a nested unpacking target, the targets are bound from left to right, so an earlier target is already assigned when the nested unpacking raises. ty treats the whole assignment as one step for the `except` clause and reports the type from before the statement.

```py
from typing import reveal_type


def f(pair: tuple[int, ...]) -> None:
    value: int | str = 1
    try:
        value, (a, b) = "bad", pair
    except ValueError:
        reveal_type(value)
        print(repr(value))


f((1,))
```

```console
$ ty check --python-version 3.13 test_bug.py
info[revealed-type]: Revealed type
 --> test_bug.py:9:21
  |
9 |         reveal_type(value)
  |                     ^^^^^ `Literal[1]`

Found 1 diagnostic

$ python test_bug.py
Runtime type is 'str'
'bad'
```

`pair` has one element, so `(a, b)` raises `ValueError` after `value` was bound to `"bad"`.

The neighbouring cases are right, so only the nested target is missing a checkpoint:

- `value, items[5] = "bad", 2` with an `IndexError` handler: `Literal[1, "bad"]`
- `value = items[5] = "bad"`: `Literal["bad"]`
- the flat `first, second = values` followed by `state = 1` (the example in the "Unpacking can raise" section of the mdtest added with astral-sh/ruff#27471): `Literal[0]`

mypy reveals `int | str`. pyright also reveals `Literal[1]`, but it does the same after a complete earlier statement (`value = "bad"` followed by `items[5]`), so I assume it only links the `except` clause at calls and I am not reporting that part.

**Expected:** `Literal[1, "bad"]` (the handler can run before or after `value` is bound).

Playground: <PLAYGROUND LINK>

### Version

ty 0.0.97 and ty 0.0.98
````

---

## 7. pyright: RangeError when a descriptor `__get__` is decorated by a function defined in the class body

**Day 7 verdict: STILL-BUG-NEW.** Source: Part C program `d3p_descriptors_decorated_get__mut1_040cc0db` (mutant of the Day-4 parent `d5p_descriptors_decorated_get_pyright_rangeerror`), reduced by hand. pyright 1.1.414 (latest on npm, PyPI and GitHub releases) crashes with exit status 2; CPython prints `42`; ty 0.0.97/0.0.98 and mypy 2.4.0/2.4.1/master do not crash. Evidence: `campaign/day7-verification.md` (D7-2), `campaign/day7/partD/evidence/results/c2min.txt`, `pyright-reduce-r1-r7.txt`, `pyright-reduce-r8-r11.txt`, `pyright-exit-codes.txt`.

**Duplicate check:** Checked: `gh search issues` and `gh search prs` on microsoft/pyright with 9 term sets (Maximum call stack size exceeded, RangeError, descriptor decorated `__get__`, retainTypeAlias, stack overflow descriptor, infinite recursion descriptor, ...), web search once. Read #9283, #9740, #6178, #6783, #5139, #4798, #5090 (closed, old telemetry crashes, none involves a descriptor), #11961 (open, 2026-11-02) and PR #11965 (open). Result: no duplicate. #11961 has the same message, but the recursion there is `validateConstructorArgs` for `__init__`/`__new__`/metaclass `__call__` annotated with their own class, and the PR only adds a guard in `validateCallForInstantiableClass`. The stack here goes through `typeUtils.ts` and `retainTypeAlias`, so the PR does not look like it covers this program.

**Not checked:** issue comments beyond the issues read in full; PRs that the search phrases did not surface; discuss.python.org; the pyright playground (the `<PLAYGROUND LINK>` placeholder is still open, UNVERIFIED-PLAYGROUND); pyright `main` and the branch of PR #11965 (only release 1.1.414 was tested). Run one last search on the exact title before submitting.

Title: `RangeError: Maximum call stack size exceeded when accessing a descriptor whose __get__ is decorated by a function defined in the class body`

````markdown
### Describe the bug

Pyright aborts with `RangeError: Maximum call stack size exceeded` when a descriptor's `__get__` is decorated by a function defined in the same class body (the usual `def deco(fn)` without `self`) and the descriptor is accessed.

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

```console
$ pyright --pythonversion 3.13 test_bug.py
An internal error occurred while type checking file "test_bug.py": RangeError: Maximum call stack size exceeded
    at z (.../pyright-internal/src/analyzer/typeUtils.ts:1985:18)
    at M (.../pyright-internal/src/analyzer/typeUtils.ts:1830:26)
    at M.next (<anonymous>)
    ...
$ echo $?
2

$ python test_bug.py
42
```

With annotations (`def __get__(self, obj: object, owner: type | None = None) -> int`) the result is the same. The stack is mostly `typeEvaluator.ts` `retainTypeAlias` and `typeUtils.ts` repeating.

Pyright treats the unannotated parameter `fn` as `self` (it reports `reportSelfClsParameterName`), so the decorated `__get__` ends up with the type of `Desc`, and applying the descriptor protocol to a `__get__` that is itself a `Desc` never ends. This smaller program crashes in the same way, the annotation is enough:

```py
class Desc:
    __get__: "Desc"


class Host:
    attr = Desc()


h = Host()
h.attr
```

What I tried (pyright 1.1.414):

- Crashes too: `Desc.__get__(Desc(), None, Host)` instead of the instance access.
- Does not crash: the same class without any access to `attr`; only `__set__` decorated, with an assignment `h.attr = 5`; a decorated ordinary method that is called; a decorated `__call__` that is called; the same decorator defined at module level.

mypy 2.4.0, 2.4.1 and master and ty 0.0.97 and 0.0.98 do not crash. They report an error on the `@deco` line (the first parameter of a function in a class body is taken as `self`), so the program is not clean for them either, but it runs under CPython and a crash is not the expected result.

This looks related to #11961 (same message, a method typed as its own class) but it is a different path: the constructor code is not involved here, and the open PR #11965 only guards `validateCallForInstantiableClass`.

**Expected:** no crash. A diagnostic about the decorator is fine.

Playground: <PLAYGROUND LINK>

**VS Code extension or command-line**

Command line. pyright 1.1.414 (PyPI `pyright==1.1.414`, also `pyright@latest` on npm), Python 3.13.16, Linux.
````

---

## 8. mypy: overloaded `__post_init__` of a dataclass is checked item by item against the InitVar signature

**Day 8 verdict: STILL-BUG-NEW.** Source: Day 8 class F, programs `rsv_dataclasses_223fff8f__mut0_3b9111ba` and `dataclasses__overloaded_post_init__mut0_46f20490` (two of the programs behind the 6 live `only_mypy override` findings of `campaign/day8-triage.txt`), reduced by hand. mypy 2.4.0, 2.4.1 and master 2.5.0+dev.879da562 report `[override]` on the overload item that does not take the `InitVar` type; ty 0.0.97/0.0.98 and pyright 1.1.414 accept; CPython runs. Control: an ordinary override of a non-overloaded method by an overloaded one with one compatible item is accepted by the same mypy versions. Evidence: `campaign/day8-verification.md` (D8-7), `campaign/day8/phase6/results/draft-outputs.txt`, `c7.txt`, `c7b.txt`, `c7d.txt`.

**Duplicate check:** Checked: `gh search issues` and `gh search prs` on python/mypy with 16 term sets (`__post_init__`, post_init overload, post_init signature, dataclass post_init, InitVar, InitVar overload, overload dataclass, dataclass override, dataclass overloaded, supertype dataclass, `Argument 2 of __post_init__`, overloaded override, ...) plus 5 on ty and pyright; read python/mypy#15498 and PR #15503 (the feature that added the check; no mention of overloads), #9254, #16293 (closed, `explicit-override`), #15515 (open, plugin API for implicit definitions, mentions the direct call from `checker.py`), #12379 (closed 2026-09-20, overloaded override of a non-overloaded method; it is the generic case that mypy accepts now). Result: no issue or PR for the overloaded `__post_init__`.

**Not checked:** issue comments beyond the issues read; PRs that the search phrases did not surface; discuss.python.org; mypy-play (the `<PLAYGROUND LINK>` placeholder is still open, UNVERIFIED-PLAYGROUND). The typing spec has no text on `__post_init__`. Cause below is read from mypy master, not debugged. Run one last search on the exact title before submitting.

Title: `Overloaded __post_init__ in a dataclass: [override] error for an overload item that does not take the InitVar type`

````markdown
**Bug Report**

For a dataclass with an `InitVar`, mypy checks the user's `__post_init__` against the signature built from the `InitVar` fields (added in #15503). When `__post_init__` is overloaded, every overload item is checked on its own, so an item that does not take the `InitVar` type is reported as an incompatible override even though another item does. The overloaded method as a whole accepts what the dataclass passes, and CPython runs the program.

**To Reproduce**

```python
from dataclasses import InitVar, dataclass
from typing import overload


@dataclass
class Record:
    value: InitVar[int]

    @overload
    def __post_init__(self, value: int) -> None: ...
    @overload
    def __post_init__(self, value: str) -> None: ...
    def __post_init__(self, value: int | str) -> None:
        print(type(value))


Record(1)
```

**Actual Behavior**

```
$ mypy --python-version 3.13 test_bug.py
test_bug.py:12: error: Argument 2 of "__post_init__" is incompatible with supertype "dataclass"; supertype defines the argument type as "int"  [override]
Found 1 error in 1 file (checked 1 source file)

$ python test_bug.py
<class 'int'>
```

The error is on the `str` item (line 12). The `int` item and the implementation (`int | str`) are not reported.

**Expected Behavior**

No error. The generated call is `__post_init__(value)` with an `int`, which the first overload accepts. For an ordinary method, mypy already accepts an overloaded override of a non-overloaded method when one item is compatible:

```python
from typing import overload


class Base:
    def post(self, value: int) -> None: ...


class Child(Base):
    @overload
    def post(self, value: int) -> None: ...
    @overload
    def post(self, value: str) -> None: ...
    def post(self, value: int | str) -> None:
        print(type(value))
```

`mypy test_control.py` prints `Success: no issues found`. If no item takes the `InitVar` type (for example overloads for `str` and `bytes` with `InitVar[int]`), an error is right, and mypy reports both items.

I read `checker.py` on master: `check_func_def` calls `dataclasses_plugin.check_post_init(self, defn, defn.info)` for a function named `__post_init__`, and `check_post_init` passes `defn.type` to `check_override`. For an overloaded method `defn` is a single item (the line of the error above) and not the `Overloaded` type, which would explain the difference to the ordinary override. I did not debug it further.

ty 0.0.97 and 0.0.98 accept the program above and reject overloads that take neither `int` nor a supertype of it. pyright 1.1.414 accepts both.

Playground: <PLAYGROUND LINK>

**Your Environment**

- Mypy version used: 2.4.0, 2.4.1 and master 2.5.0+dev.879da562
- Mypy command-line flags: `--python-version 3.13`
- Mypy configuration options from `mypy.ini` (and other config files): none
- Python version used: 3.13.16
- Operating system: Linux
````

---

## 9. mypy: comparison of two operands of the same type tries the reflected method first when `__lt__` and `__gt__` come from different classes

**Day 9 verdict: STILL-BUG-NEW.** Source: Day 9 program `d3p_inheritance_mro_total_ordering_inherited_lt__mut0_73c4aa3f` (2 strong findings; its parent has shown the same reveal mismatch since Day 2), reduced by hand; `functools.total_ordering` is not needed. mypy 2.4.0, 2.4.1 and master 2.5.0+dev.879da562 infer `int` for `a < b` and `str` for `a > b`; CPython 3.13.16 returns `'lt'` and `7`; ty 0.0.97/0.0.99 and pyright 1.1.414 agree with CPython. Evidence: `campaign/day9-verification.md` (D9-3), `campaign/day9/phase6/results/c3g.txt`, `c3c.txt`, `c3f.txt`, `c3e.txt`, `c3.txt`.

**Duplicate check:** Checked: `gh search issues` (13 queries) and `gh search prs` (6 queries) on python/mypy, 2 issue queries each on ty and pyright, 1 PR query on ruff (reflected comparison, reverse comparison, `__lt__ __gt__`, `__le__ __ge__`, comparison operator, reverse operator, `check_op_reversible`, rich comparison, same type reflected, total_ordering, `op_methods_that_shortcut`, ...). Result: no issue or PR for this. Same function, different bugs: mypy#22377 (open, class objects and `covers_at_runtime`), #19006 (closed, tuple subclass priority, fixed by PR #19046), #22316 (open) and PR #22380 (open, the operator shown in the error message is flipped).

**Not checked:** issue comments beyond the issues read; PRs that the search phrases did not surface; discuss.python.org; mypy-play (the `<PLAYGROUND LINK>` placeholder is still open, UNVERIFIED-PLAYGROUND). The cause below is read from mypy master, not debugged. Run one last search on the exact title before submitting.

Title: `Comparison of two operands of the same type calls the reflected method first when __lt__ and __gt__ are defined in different classes`

````markdown
**Bug Report**

For `a < b` where `a` and `b` have exactly the same type, CPython calls `a.__lt__(b)`. The reflected method `b.__gt__(a)` goes first only if the type of `b` is a proper subclass of the type of `a` (data model, `object.__lt__`: "If the operands are of different types, and the right operand's type is a direct or indirect subclass of the left operand's type, the reflected method of the right operand has priority"). mypy tries `b.__gt__(a)` first for operands of the same type when `__lt__` and `__gt__` are defined in different classes of the MRO, so it infers the result type of the wrong method.

**To Reproduce**

```python
from typing import assert_type


class Base:
    def __lt__(self, other: "Base") -> str:
        return "lt"


class Child(Base):
    def __gt__(self, other: "Child") -> int:
        return 7


a = Child()
b = Child()
s: str = a < b
assert_type(a < b, str)
assert_type(a > b, int)
print(repr(a < b), repr(a > b))
```

**Actual Behavior**

```
$ mypy --python-version 3.13 --no-incremental test_bug.py
test_bug.py:16: error: Incompatible types in assignment (expression has type "int", variable has type "str")  [assignment]
test_bug.py:17: error: Expression is of type "int", not "str"  [assert-type]
test_bug.py:18: error: Expression is of type "str", not "int"  [assert-type]
Found 3 errors in 1 file (checked 1 source file)

$ python test_bug.py
'lt' 7
```

**Expected Behavior**

No errors: `a < b` is `str` and `a > b` is `int`. pyright 1.1.414 and ty 0.0.97 report nothing for this file.

What I tried:

- `<=` in `Base` and `>=` in `Child`: same swap.
- Both methods in one class: correct. The swap needs the two methods to come from different classes.
- `__add__` in `Base` and `__radd__` in `Child` with two `Child` operands: correct, `a + b` is `str` (mypy reports the unsafe overlap of the two methods on the class, which is a separate message).
- The right operand of a proper subclass of `Child` (`a <= c` with `class Sub(Child)`): mypy infers `int`, which is also what CPython returns, because `Sub` is a proper subclass.

Cause, as far as I can tell from `check_op_reversible` in `checkexpr.py` on master: the branch for two operands of the same type is guarded by `op_name in operators.op_methods_that_shortcut`, and that set holds the arithmetic and bitwise methods (`__add__` to `__rshift__`) but no comparison. For `<` mypy therefore goes to the next branch, which puts the reflected method first when `lookup_definer(left_type, "__lt__") != lookup_definer(right_type, "__gt__")` and `covers_at_runtime(right_type, left_type)` holds. It does not check that the two types differ.

**Your Environment**

- Mypy version used: 2.4.0, 2.4.1 and master 2.5.0+dev.879da562
- Mypy command-line flags: `--python-version 3.13 --no-incremental`
- Python version used: 3.13.16
- OS: Linux

mypy-play: <PLAYGROUND LINK>
````

---

## 10. mypy: `possibly-undefined` does not report a name assigned in a `with` block whose context manager can swallow the exception

**Day 9 verdict: STILL-BUG-NEW (low confidence, 0.4).** Source: two Day 9 `only_pyright` rows with a `runtime_supports` relation (`context_managers/gen0_b82d2e9e`, `gen21_6ee04c3a`; weak evidence in the triage), reduced by hand to `c10.py` and `c10b.py`. CPython 3.13.16 raises `UnboundLocalError`; pyright 1.1.414 reports `reportPossiblyUnboundVariable` in its default configuration; ty 0.0.97 and 0.0.99 report `possibly-unresolved-reference` when the rule is enabled (it is off by default, so ty is not a bug here); mypy 2.4.0, 2.4.1 and master 2.5.0+dev.879da562 report nothing, also with `--enable-error-code possibly-undefined`. Evidence: `campaign/day9-verification.md` (D9-10), `campaign/day9/phase6/results/c10.txt`, `c10b.txt`, `c10d.txt`, `c10e.txt` (mypy 2.4.0, 2.4.1 and master: `Missing return statement` for a function that ends in `with suppress(...): return ...`), `c10_extra.txt`, `c10d_extra.txt`.

**Duplicate check:** Checked: `gh search issues` (8 queries) and `gh search prs` (3) on python/mypy, 5 queries on ty, 3 on pyright, 2 PR queries on ruff (possibly-undefined with, possibly-undefined suppress, possibly-undefined context manager, suppress possibly, swallow exceptions, context manager swallow, partially_defined, ...). Result: nothing about `possibly-undefined` and `with`. The mypy results are about "Missing return statement" after `ExitStack` or `suppress` (mypy#7577, #10896, #7726, #15715, closed), which the type checker handles. mypy's own test `testWithStmt` in `check-possibly-undefined.test` covers only names bound by the `with` targets.

**Not checked:** issue comments beyond the issues read; PRs that the search phrases did not surface; discuss.python.org; mypy-play (the `<PLAYGROUND LINK>` placeholder is still open, UNVERIFIED-PLAYGROUND). The maintainers may call this a known limit of an opt-in check that runs without type information. Run one last search on the exact title before submitting.

Title: `possibly-undefined: name assigned in a with block that can swallow exceptions is not reported after the block`

````markdown
**Bug Report**

mypy knows that a `with` block can swallow an exception when `__exit__` returns `bool`: a function that ends in `with suppress(KeyError): return d["a"]` gets `Missing return statement`, because the code after the block is reachable. The `possibly-undefined` check does not use this. A name that is assigned inside the block is unbound after it if the exception was swallowed before the assignment, and mypy does not report the later use.

**To Reproduce**

```python
from contextlib import suppress


def get(d: dict[str, int]) -> int:
    with suppress(KeyError):
        value = d["a"]
    return value


print(get({"a": 1}))
print(get({}))
```

```
$ mypy --python-version 3.13 --enable-error-code possibly-undefined test_bug.py
Success: no issues found in 1 source file

$ python test_bug.py
1
UnboundLocalError: cannot access local variable 'value' where it is not associated with a value
```

**Expected Behavior**

`test_bug.py:7: error: Name "value" may be undefined  [possibly-undefined]`

pyright reports this by default (`"value" is possibly unbound`), and ty reports it with `--warn possibly-unresolved-reference`. A user-defined context manager gives the same result:

```python
class Swallow:
    def __enter__(self) -> None:
        return None

    def __exit__(self, *args: object) -> bool:
        return True


def f(fail: bool) -> str:
    with Swallow():
        if fail:
            raise TypeError("boom")
        result = "ok"
    return result
```

Controls: with `__exit__(...) -> None` nobody reports the name (the exception propagates), and `-> bool | None` is not reported by any of the three (typeshed's convention for "does not swallow"). With `-> Literal[True]` pyright and ty report it and mypy does not.

Cause, read from master and not debugged: `PossiblyUndefinedVariableVisitor.visit_with_stmt` in `partially_defined.py` visits `o.body` as straight-line code. That pass works on the AST before type checking, so it does not know the return type of `__exit__`, which `TypeChecker.visit_with_stmt` uses to decide whether exceptions may be suppressed. A fix probably needs the type information, so this may be a known limitation.

**Your Environment**

- Mypy version used: 2.4.0, 2.4.1 and master 2.5.0+dev.879da562
- Mypy command-line flags: `--python-version 3.13 --enable-error-code possibly-undefined`
- Python version used: 3.13.16
- OS: Linux

mypy-play: <PLAYGROUND LINK>
````

---

**Day 8 status (details: `campaign/day8-verification.md`, raw output: `campaign/day8/phase6/`).** Draft 8 (mypy, overloaded `__post_init__`) was added. Draft 6 and draft 7 cover more programs now, without a new draft: the four Day-8 mutants of the partial-unpack parent (`(a, *b, c)` star target, `(first, *rest)` with an empty tuple, an attribute-chain source, a `match` in the handler) show the same `Literal[1]` / `Literal[0]` on ty 0.0.97 and 0.0.98 as draft 6; the annotated variant `d3p_descriptors_decorated_get__mut0_655e135a` with `reveal_type(C.__get__)` and a direct `C.__get__(C(), None, C)` call crashes pyright 1.1.414 like draft 7 (draft 7 already lists the direct call). Neither draft was found filed under the account that filed ty#4933, #4934, #4941 and mypy#22375, #22377 (author listing, `campaign/day8/phase6/search/out_author.txt`).

**Day 9 status (details: `campaign/day9-verification.md`, raw output: `campaign/day9/phase6/`).** Drafts 9 and 10 were added. Not drafted, with reasons:

- **Metaclass `__call__` return type ignored by mypy** (`constructors_metaclasses/gen1_c86958a8`): DUPLICATE of python/mypy#8595 (closed 2020-03-27, "unlikely this will be ever supported"); related open #14122 and closed #15182. ty 0.0.97/0.0.99 and pyright infer `int`.
- **`tuple[*Ts, *Us]`** (`typevartuple_unpack/gen1_4d7d067f`): NOT-A-BUG. The signature is invalid and all three checkers say so; the odd reveal in mypy comes after the error (mypy#20386: the maintainer calls such a type unrepresentable).
- **Reflected operator on class objects** (`d4v_metaclass_reflected_op__mut0_dcb547ed`): another instance of draft 3, filed as python/mypy#22377 (open).
- **`class Callback[*Ts, **P = [bool]]` raises `TypeError` in CPython** (three mutants of `d3p_typevartuple_unpack_paramspec_default_after_tvt`): the runtime bug is python/typing#2211 (open, "a bug in the runtime"); the typing spec requires the checkers to accept the class, ty and pyright do (ruff#29753 and #29755 on the ty side), and mypy's subscript error is draft 5 (mypy#22375).
- **`Any` argument reaches `n + 1` on a `str`** (`gradual_any/gen5_ade5dcc3`): NOT-A-BUG, the gradual guarantee.
- **Annotation-only or instance-assigned special methods** (20 `only_pyright` `runtime_supports` rows, the Day-8 lead of section 4 of `day8-verification.md`): NOT-A-BUG, a known trade-off. CPython raises `TypeError` for `len(x)`, `x()`, `list(x)`, `x[0]` and `1 in x` in both forms (`d1.py`, `d2.py`). For the annotation-only form no checker rejects all five (ty rejects 2, mypy 3, pyright 2); for the instance-assigned form ty rejects all five, pyright 3 and mypy none. The ty maintainers state the trade-off in ty#4570 (instance attributes implement protocol methods, "false negatives in some cases that will raise at runtime", dunders named explicitly); for instance-assigned dunders mypy#2113 (open since 2016) is the same report. Nothing is drafted: confidence that ty or mypy would take it as a bug is below 0.3.
- **`Need type annotation for "key"` on `self.key = key` with a constrained PEP 695 or old-style type variable** (seen in `d3p_typevartuple_unpack_paramspec_default_after_tvt__mut0_df958820`): DUPLICATE of python/mypy#19618 (open, known problem, subset of #5416).
