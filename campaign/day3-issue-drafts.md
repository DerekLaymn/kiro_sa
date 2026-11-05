# Issue drafts, Day 3 candidates (Day 4 consolidate)

Date: 2026-11-05. Tools: ty 0.0.84 (pinned) and 0.0.97 (latest), mypy 2.4.0 / 2.4.1 / master 2.5.0+dev.879da562, pyright 1.1.414, CPython 3.13.16, Linux.
The drafts are concatenated without edits to the issue bodies from `campaign/day4/issue-drafts-v1.md` (draft 1), `-v2.md` (draft 2) and `-v3.md` (drafts 3 and 4). Each draft sits in a fenced block: copy the contents (without the fence lines) into the issue body, set the title from the "Title" line, and replace `<PLAYGROUND LINK>`. NOT FILED. Nothing here was posted anywhere, and no GitHub write call was made. (The format reference `temp/issue_drafts.md` does not exist in the repo; the format of the v1 to v3 drafts is kept.)

| # | Tool | Bug | Class | Conf | Duplicate check | Source |
|---|---|---|---|---|---|---|
| 1 | ty | stack overflow when a class is checked against a protocol whose method annotates `self` as `Stream[Stream[T]]` | CRASH | 0.80 | none found. Related: open #4746, open #4882, closed #4694, #4863 | v1 draft 1 |
| 2 | ty | alias narrowing (`is_none = x is None`) survives a reassignment that reaches the use over a loop back edge | INCORRECT_INFERENCE / FALSE_NEGATIVE | 0.9 | none found. Related: ty#4379, ty#719, ruff#24302, ty#2792 | v2 draft 1 |
| 3 | mypy | reflected operator of a subclass metaclass ignored for class-object operands (`A * B`) | FALSE_POSITIVE | 0.7 | none found (12 phrases). Related: mypy#19006, #4789 | v3 draft 1 |
| 4 | ty | class with `__eq__` and no `__hash__` accepted as `Hashable` | FALSE_NEGATIVE | 0.7 | none found. Related: ty#3781, ruff#27441; mypy#20230 is the mypy-side report | v3 draft 2 |

Not drafted, with reasons (all duplicates or fixed):

- Self-referential `__call__` attribute (`__call__: "C"`, `Self | None`, mutual pairs): open ty#4148 (ty) and python/mypy#22361 (mypy).
- `partial | None` in a loop: ty 0.0.84 panics, fixed in ty 0.0.85.
- Stale alias condition after a method call and read-only property `Never`: ty#2792. Tuple-subclass constant fold: ty#2171. Flag combination `Never`: ty#876. Metaclass `A | B` in ty: ty#4683. IntEnum alias: mypy#16830, mypy#21117, pyright#11100. Recursive alias reveal: mypy#2008. `__hash__` None reveal: mypy#20230.

Confidence for drafts 3 and 4 is 0.7: the construct in draft 3 is rare and the source location is a hypothesis; the ty maintainers may fold draft 4 into the hashability work in ty#3781.

Build: `/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.venv/bin/python /tmp/cons/build.py` (concatenation and renumbering only).

---

## 1. ty: nested protocol receiver

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

**Duplicate check:** Checked: `gh search issues` on python/mypy with 12 phrases, `gh search prs --repo astral-sh/ruff`, best three hits per tool read with `gh issue view`. Result: no duplicate. Related but different: mypy#4789 and #4929 (operators on `Type[Foo]`), mypy#19006 (reflected priority for tuple subclasses, fixed), pyright#4088, #3368, #10644 (instances, declined by maintainer). Source: `campaign/day4/verify-v3.md` 2.5.

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
c2_f.py:18: error: Incompatible types in assignment (expression has type "int", variable has type "str")  [assignment]
c2_f.py:19: error: Expression is of type "int", not "str"  [assert-type]
Found 2 errors in 1 file (checked 1 source file)
```

`python c2_f.py` prints `str`. Without the return-type difference, `reveal_type(A * B)` shows the left method's result (`Literal['left']` in the original report) where CPython returns the right one.

**Expected Behavior**

No errors; `A * B` is inferred from `RightMeta.__rmul__`, as for `L() * R()`. Unlike an instance annotated `L`, the expressions `A` and `B` name exactly one class each, so the metaclasses are known precisely and the call order is decidable. The same happens with `__or__`/`__ror__` on class objects.

Possible cause (from reading the source, not verified): in `check_op_reversible` the priority branch is guarded by `covers_at_runtime(right_type, left_type)`. For class objects both types are type-object callables (`def () -> B` and `def () -> A`), so the check is false and the metaclass relation is never looked at.

pyright reports the same two errors; its maintainers consider the instance version "as designed" (pyright#4088, #3368), so this report is only about mypy's inconsistency between instances and class objects. ty accepts the program.

**Your Environment**

- Mypy version used: 2.4.0, 2.4.1 and master 2.5.0+dev.879da56
- Mypy command-line flags: `--python-version 3.13 --no-incremental`
- Python version used: 3.13.16
- OS: Linux

mypy-play: <PLAYGROUND LINK>
````

---

## 4. ty: class with `__eq__` and no `__hash__` is accepted as `Hashable`

**Duplicate check:** Checked: ty tracker dump (regexes on `__eq__`, `__hash__`, `unhashable`, `hashab`), `gh search issues` on astral-sh/ty with 5 or more phrases, `gh search prs --repo astral-sh/ruff` with 5 phrases, best three hits read. Result: no duplicate. Related: ty#3781 (set/dict displays with mutable dataclasses), ruff#27441 (`Hashable` for ClassVar None, containers, mutable dataclasses), mypy#20230, #18622, #2455 (mypy side of the same rule). Source: `campaign/day4/verify-v3.md` 4.5.

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
