# Issue drafts v2 (Day 4 verification)

Date: 2026-11-05. Tools: ty 0.0.84 and 0.0.97, mypy 2.4.0 / 2.4.1 / master 2.5.0+dev.879da56, pyright 1.1.414, CPython 3.13.16, Linux.
Each draft sits in a fenced block: copy the contents (without the fence lines) into the issue body, set the title from the "Title" line, and replace `<PLAYGROUND LINK>`. NOT FILED. Nothing here was posted anywhere.

## Duplicate check summary

Searched for the draft below: ty tracker dump of 2026-11-05 (4060 issues, titles and bodies, 9 regexes), `gh search issues --repo astral-sh/ty` with 7 phrases, `gh search prs --repo astral-sh/ruff` with 3 phrases, python/mypy and microsoft/pyright with 2 phrases each. No match.
Related but different: ty#719 and ruff#24302 (the alias feature itself), ty#4379 (closed; same loop back-edge problem, but for direct narrowing), ty#2792 (open; attribute narrowing across method calls).
Not checked: comments of all ty issues, discuss.python.org, ty `main` (only release 0.0.97 was tested). Run one last search on the exact title before submitting.

| # | Tool | Bug | Duplicate check |
|---|---|---|---|
| 1 | ty | alias narrowing (`is_none = x is None`) survives a reassignment of `x` that reaches the use over a loop back edge | none found. Related: ty#4379 (direct narrowing, closed), ty#719 / ruff#24302 (feature), ty#2792 (calls) |

---

## 1. ty: aliased-condition narrowing ignores a reassignment on a loop back edge

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
