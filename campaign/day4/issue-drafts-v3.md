# Issue drafts v3 (Day 4 verification)

Date: 2026-11-05. Tools: ty 0.0.84 and 0.0.97, mypy 2.4.0 / 2.4.1 / master 2.5.0+dev.879da56, pyright 1.1.414, CPython 3.13.16, Linux.
Each draft sits in a fenced block: copy the contents (without the fence lines) into the issue body, set the title from the "Title" line, and replace `<PLAYGROUND LINK>`. NOT FILED. Nothing here was posted anywhere.

## Duplicate check summary

Searched for the two drafts below: ty tracker dump of 2026-11-05 (4060 issues, titles and bodies, regexes on `__eq__`/`__hash__`/`unhashable`/`hashab` and on metaclass operators), `gh search issues` on astral-sh/ty, python/mypy and microsoft/pyright with 5 to 12 phrases per candidate, `gh search prs --repo astral-sh/ruff` with 5 phrases, and the best three hits per tool read with `gh issue view`. Details in `campaign/day4/verify-v3.md` §2.5 and §4.5.
Related but different: mypy#4789 / #4929 (operators on `Type[Foo]`), mypy#19006 (reflected priority for `tuple` subclasses, fixed), pyright#4088 / #3368 / #10644 (reflected priority for instances, declined by the maintainer), ty#3781 (set/dict display, mutable dataclass), ruff#27441 (`Hashable` for `ClassVar[None]`, containers and mutable dataclasses), mypy#20230 / #18622 / #2455 (the same missing hashability rule on the mypy side).
Not checked: comments of all ty issues, discuss.python.org, ty `main` (only release 0.0.97 was tested). Run one last search on the exact title before submitting.

| # | Tool | Bug | Duplicate check |
|---|---|---|---|
| 1 | mypy | reflected operator of a subclass metaclass is ignored for class-object operands (`A * B`) | none found (12 phrases). Related: mypy#19006, mypy#4789 |
| 2 | ty | a class that defines `__eq__` without `__hash__` is accepted as `Hashable` | none found. Related: ty#3781, ruff#27441; mypy#20230 is the mypy-side report |

Confidence: draft 1 is 0.7 (rare construct, source location is a hypothesis); draft 2 is 0.7 (the maintainers may fold it into the hashability work in ty#3781).

---

## 1. mypy: reflected operator on class objects whose metaclasses are related

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

## 2. ty: class with `__eq__` and no `__hash__` is accepted as `Hashable`

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
