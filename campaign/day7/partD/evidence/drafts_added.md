
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
