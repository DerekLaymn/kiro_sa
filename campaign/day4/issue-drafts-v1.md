# Issue drafts, Day 4 worker v1

Date: 2026-11-05. Tools: ty 0.0.84 and 0.0.97, mypy 2.4.0 / 2.4.1 / master 2.5.0+dev.879da562, pyright 1.1.414, CPython 3.13.16, Linux.
Each draft sits in a fenced block: copy the contents of the block (without the fence lines) into the issue body, set the title from the "Title" line, and replace the `<PLAYGROUND LINK>` placeholder (UNVERIFIED-PLAYGROUND: it could not be tried from the shell). Nothing has been filed.

## Duplicate check summary

Evidence is in `campaign/day4/verify-v1.md`, section C2. Checked: ty tracker snapshot of 4060 issues (title and body regexes), `gh search issues` on astral-sh/ty with 12 phrases, `gh search prs` on astral-sh/ruff, and full reads of ty#4746, #4882, #4694, #4863. Not checked: issue comments beyond those reads, discuss.python.org, play.ty.dev, ty `main` (only release 0.0.97). Run one last search on the exact title before submitting.

| # | Tool | Bug | Duplicate check |
|---|---|---|---|
| 1 | ty | stack overflow when a class is checked against a protocol whose method annotates `self` with a nested specialization of the protocol | none found. Related: open #4746 (false positive for `self: "HasMeth"`, same query), open #4882 (stack overflow, different program), closed #4694 and #4863 (stack overflow with `self: Stream[Stream[U]]` plus other members, fixed) |

Not drafted, with reasons:

- Self-referential `__call__` attribute (`__call__: "C"`, `Self | None`, mutual pairs): already open as ty#4148 (ty) and python/mypy#22361 (mypy).
- `partial | None` in a loop: ty 0.0.84 panics, fixed in ty 0.0.85.

---

## 1. ty: nested protocol receiver

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
