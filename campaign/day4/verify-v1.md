# Day 4 verification, worker v1 (Plan §6 checklist)

Date: 2026-11-05. Candidates: the three checker-crash families of `campaign/day3-report.md` §4.1 (6 generated programs).
Nothing was filed, pushed or written to GitHub; all `gh` calls were read-only (`gh search`, `gh issue view`, `gh pr view`, `gh release view`).

Tools (pinned = the kiro_sa venv; latest = `/tmp/d3v-latest`; master = `/tmp/d3v-master`):

| set | mypy | ty | pyright | CPython |
|---|---|---|---|---|
| pinned | 2.4.0 (compiled) | 0.0.84 | 1.1.414 | 3.13.16 |
| latest | 2.4.1 (compiled) | 0.0.97 | 1.1.414 (same) | 3.13.16 |
| master | 2.5.0+dev.879da562 (uncompiled) | n/a | n/a | n/a |

Every checker call went through `/home/derek/.config/kiro-hooks/memguard.sh` (4 GB cap, no swap), pinned ones included. Command template, with `K=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.venv/bin`, `L=/tmp/d3v-latest/bin`, `M=/tmp/d3v-master/bin`, `MG=/home/derek/.config/kiro-hooks/memguard.sh` (flags are the pipeline's own, `typediff/runners.py`):

```
$K/python FILE
$MG timeout 120 $K/mypy --python-version 3.13 --check-untyped-defs --no-incremental --no-error-summary --no-color-output --show-error-codes FILE
$MG timeout 120 $K/ty check --python-version 3.13 --output-format concise --no-progress --color never FILE
$MG timeout 120 $K/pyright --pythonversion 3.13 FILE
# latest: same with $L/mypy, $L/ty, $L/pyright;  master: $M/mypy
```

Summary:

| id | tool | verdict | class / dismissal | conf | faulty_tool | new? |
|---|---|---|---|---|---|---|
| C1 self-referential `__call__` (A1/A5 family, 4 programs) | ty | BUG | CRASH, DUPLICATE of ty#4148 | 0.90 | ty | no |
| | mypy | BUG | CRASH, DUPLICATE of mypy#22361 (team-filed) | 0.95 | mypy | no |
| | pyright | NOT_BUG | SPEC_AMBIGUITY | 0.50 | none | n/a |
| C2 protocol `flatten` (`self: Stream[Stream[T]]`) | ty | BUG | CRASH, no duplicate found | 0.80 | ty | **yes** (draft written) |
| | mypy | NOT_BUG | NOISE (accepts, terminates) | 0.80 | none | n/a |
| | pyright | NOT_BUG | NOISE (accepts, terminates) | 0.80 | none | n/a |
| C3 `partial \| None` in a loop | ty 0.0.84 | BUG | CRASH, already fixed in ty 0.0.85 | 0.97 | ty (pinned only) | no (not reportable) |
| | ty 0.0.97, mypy, pyright | NOT_BUG | NOISE (all report `unsupported-operator`) | 0.95 | none | n/a |

---

## C1. Self-referential `__call__` attribute (ty stack overflow; day-3 seeds 0032056ba741, 6cb04c1e6fbc, 3e7d6fb5688c, 887c42f07fb0)

`[Plan §6 / verify C1]`

### (1) REPRODUCE

The four generated programs (`runs/day3/gen/callables/d3p_callables_self_call_attr__mut0_{2e173b54,eae572b3}.py`, `runs/day3/gen/self_classmethods/d3p_self_classmethods_self_call_union__mut0_{99c51718,a5207109}.py`) all still crash ty on pinned and latest. Matrix from `matrix.py` (pinned / latest / master):

| program | CPython | mypy 2.4.0 | ty 0.0.84 | pyright | mypy 2.4.1 | ty 0.0.97 | mypy master |
|---|---|---|---|---|---|---|---|
| call_attr 2e173b54 | ok | SIGSEGV | stack overflow | 0 errors | SIGSEGV | stack overflow | INTERNAL ERROR |
| call_attr eae572b3 | ok | SIGSEGV | stack overflow | 0 errors | SIGSEGV | stack overflow | INTERNAL ERROR |
| call_union 99c51718 | ok | SIGSEGV | stack overflow | 1 error | SIGSEGV | stack overflow | INTERNAL ERROR |
| call_union a5207109 | ok | SIGSEGV | stack overflow | 1 error | SIGSEGV | stack overflow | INTERNAL ERROR |

Hand-minimized reproducer A (5 lines; file `/tmp/d4v1/final/c1_call_attr.py`, copy of the parent `runs/hits/d3p_callables_self_call_attr.py` without header):

```python
class C:
    __call__: "C"


C()()
```

Outputs:

```
$ $K/python m1a.py
TypeError: 'C' object is not callable                                  exit=1
$ mypy (pinned) m1a.py
timeout: the monitored command dumped core / Segmentation fault        exit=139
$ ty (pinned) m1a.py
thread '<unknown>' (468994) has overflowed its stack
fatal runtime error: stack overflow, aborting                          exit=134
$ pyright (pinned) m1a.py
0 errors, 0 warnings, 0 informations                                   exit=0
$ mypy 2.4.1 -> Segmentation fault (139);  ty 0.0.97 -> stack overflow (134);  pyright -> 0 errors
$ mypy master m1a.py
m1a.py:5: error: INTERNAL ERROR -- Please try using mypy master on GitHub:   exit=2
```

Reproducer B (`Self | None`, 9 lines, the A5 shape):

```python
from typing import Self


class C:
    __call__: Self | None = None


x: C = C()
x()
```

CPython: `TypeError: 'NoneType' object is not callable`. mypy 2.4.0/2.4.1: SIGSEGV (139). ty 0.0.84/0.0.97: stack overflow (134). pyright: `m1b.py:9:1 - error: Object of type "None" cannot be called (reportOptionalCall)`. mypy master: INTERNAL ERROR (exit 2).

### (2) SPEC

The typing spec says nothing about a class that declares `__call__` as an annotated attribute. Searched `~/.cache/typediff/docs/spec/*.txt` for `__call__` (callables.txt, constructors.txt only mention method-style `__call__` and metaclass `__call__`) and fetched https://typing.python.org/en/latest/spec/callables.html. The only related sentence is in "Callback protocols": protocols "can be defined ... with a `__call__` member". Spec: silent for annotation-only and self-referential `__call__`.

Documentation of intent: DESIGN.md §2 classifies any `CRASH` as "Always a bug, even on invalid input". ty's own tracker treats it as a bug: ty#4148 (labels `fatal`, `attributes`, `callables`, `cycles`, milestone Stable) says "A non-callable endpoint such as `__call__: int` correctly emits `call-non-callable`; the recursive cycle should terminate the same way." mypy prints "INTERNAL ERROR" for the same input; mypy#22361 carries the `crash` label.

### (2b) The accused tool's side

If a self-referential `__call__` attribute were legitimately callable, `C()()` would have to evaluate `C().__call__` (type `C`), then call that, forever. No finite result type exists, so the only coherent outcomes are "not callable" (error) or `Unknown`. ty already decides "not callable" on another path:

```
y: Callable[[], object] = x     # x: C
ty 0.0.84 and 0.0.97:  error[invalid-assignment]: Object of type `C` is not assignable to `() -> object`
pyright:               error: Type "C" is not assignable to declared type "() -> object"
mypy:                  Segmentation fault
```

Probes (`/tmp/d4v1/probe/p*.py`): `reveal_type(C().__call__)` works in all three (`C`); `x.__call__()`, `g = x; g()` and `type(x).__call__(x)` crash ty the same way; `callable(x)` narrows to `C & ((...) -> object)` in ty without crashing.

What pyright does: it accepts `C()()` silently while rejecting `C` -> `Callable[[], object]`. Runtime says TypeError, so pyright is probably too lenient, but the spec is silent and this is not a crash, so it stays NOT_BUG / SPEC_AMBIGUITY (0.5). Side note for a later day, not verified further: pyright's call path and its assignability path disagree about whether `C` is callable.

### (3) STRONGEST ORACLE

Runtime crash of the checker on a program CPython runs without error unless called, plus ty contradicting itself (the `Callable[[], object]` assignment above says "not callable", the call overflows). Not a spec quote.

### (4) GENERALISE (`/tmp/d4v1/c1`, `/tmp/d4v1/hv`; ty pinned and latest give the same result in every row)

| variant | CPython | mypy | ty | pyright |
|---|---|---|---|---|
| `__call__: "C"`, `C()()` | TypeError | SIGSEGV | overflow | 0 err |
| declaration only (`x = C()`) | ok | clean | clean | 0 err |
| `__call__: "C \| None"`, call in function | ok | SIGSEGV | overflow | 1 err |
| `__call__: Self` | ok | SIGSEGV | overflow | 0 err |
| `__call__: Self \| None = None` | ok | SIGSEGV | overflow | 1 err |
| subclass instance `D(B)()` | TypeError | SIGSEGV | overflow | 0 err |
| two classes `A.__call__: "B"`, `B.__call__: "A"` | TypeError | SIGSEGV | overflow | 0 err |
| three-class chain A -> B -> C -> A | ok | SIGSEGV | overflow | 0 err |
| mutual `"B \| None"` / `"A \| None"` | ok | SIGSEGV | overflow | 1 err |
| `ClassVar["C"]` | TypeError | SIGSEGV | overflow | 0 err |
| `ClassVar` mutual pair | ok | SIGSEGV | overflow | 0 err |
| control `__call__: int` | TypeError | 1 err | 1 diag | 1 err |
| control `__call__: D` (unrelated class) | TypeError | 1 err | 1 diag | 1 err |
| control `__call__: list[C]` | TypeError | 1 err | 1 diag | 1 err |
| control `__call__: Callable[[], "C"]` | ok | 1 err | clean | 0 err |
| control method `def __call__(self) -> Self` | ok | clean | clean | 0 err |

Every variant whose `__call__` type leads back to the class crashes both mypy and ty; unrelated or terminating types do not. The mutual-recursion and chain forms are new compared with the parents in `runs/hits`.

### (5) DUPLICATES

ty (tracker snapshot `/tmp/d3v-trk/ty.json`, 4060 issues, plus live `gh`):

- Regexes over title + body: `__call__: *"?C"?` -> ty#4148 (OPEN, "Stack overflow on self-referential `__call__` attribute"), #3981, #3957, #491 (unrelated); `overflowed its stack.{0,2000}__call__` and the reverse -> only #4148; `self.referential.{0,50}__call__` -> only #4148; `Self \| None` -> #4387, #4101, #3731, #2593, #2042, #1827, #1124 (none about `__call__`); `callable attribute.{0,100}(overflow|crash)` -> none.
- `gh search issues "self-referential __call__" --repo astral-sh/ty` -> #4148. Other phrases (`__call__ stack overflow`, `__call__ attribute overflow`) -> no results. `gh search issues "overflowed its stack"` lists #4898, #4691, #4882, #4900, #4148, #4104, #4099, #4694, none about `__call__` except #4148.
- `gh issue view 4148 --repo astral-sh/ty`: body is exactly reproducer A (`class C: __call__: "C"` then `C()()`), reported on ty 0.0.65, still OPEN, assignee charliermarsh, milestone Stable. Our programs on 0.0.97 still crash, so it is not fixed.
- `gh search prs "self-referential __call__" --repo astral-sh/ruff` -> ruff#28691 "[ty] Detect cycles in instance __call__ expansion" (CLOSED 2026-10-07, not merged, "Closes ty#4148"; says the result becomes `call-non-callable`). No merged fix exists.

mypy: `gh search issues` phrases tried: `__call__ attribute own type segfault`, `__call__ attribute segfault`, `expand_self_type`, `__call__ Self crash`, `__call__ RecursionError`, `segfault __call__`, `__call__ attribute crash`, `Self | None`, `recursive __call__`, `INTERNAL ERROR __call__`, `crash callable attribute`, `call attribute own type`. Only hit: **mypy#22361** "Segfault / RecursionError when calling an instance whose class declares __call__ as an attribute of its own type" (OPEN, `crash`, `topic-recursive-types`). Read in full with `gh issue view 22361`: same reproducer (`__call__: "C"`, `"C | None"`, `Self | None`), same master traceback in `expand_self_type`. The Day-3 KB already has `MYPY-22361`, which is why the mypy side was auto-dismissed in the pipeline. Other mypy hits are unrelated (#17395 `Self` of ClassVar, #7370 SEGV in check_call endless loop for a different construct).

pyright: `gh search issues` phrases `__call__ attribute own class`, `__call__ annotation instance variable`, `recursive __call__`, `__call__ variable declaration` -> nothing relevant (#10242 is about async recursion).

Known-upstream KB: `MYPY-22361` covers the mypy side. There is **no ty entry** for ty#4148 (TY-4882, TY-4898, TY-4899, TY-4900 each require a different program feature), which is why the ty crash stayed live in the Day-3 queue. Recommendation (not applied, outside this worker's write scope): add `TY-4148`, kind `crash`, tool `ty`, signature `ty:signal-SIGABRT:stack-overflow`, `requires: call_attr_own_type`, dismissal DUPLICATE, url https://github.com/astral-sh/ty/issues/4148, note "open; fix attempt ruff#28691 closed unmerged".

### (6) PLAYGROUND

UNVERIFIED-PLAYGROUND (no browser access from the shell). Not needed: no issue will be filed for C1.

### (7) VERDICT

- ty: BUG / CRASH (stack overflow), conf 0.90, faulty_tool ty. Dismissal for filing purposes: DUPLICATE https://github.com/astral-sh/ty/issues/4148. The `Self | None`, mutual and chain forms share the root cause (resolving the `__call__` type loops back to the class).
- mypy: BUG / CRASH (SIGSEGV compiled, RecursionError/INTERNAL ERROR uncompiled), conf 0.95, faulty_tool mypy. DUPLICATE https://github.com/python/mypy/issues/22361 (the team's own report).
- pyright: NOT_BUG / SPEC_AMBIGUITY, conf 0.5.

Hit files: `runs/hits/d4v_callables_mutual_call_attr.py` (mutual pair; instructive, parents only cover the one-class loop).

---

## C2. Protocol `flatten` (`self: Stream[Stream[T]]`; day-3 seed d8c0c3a3b3ad)

`[Plan §6 / verify C2]`

### (1) REPRODUCE

Generated program `runs/day3/gen/async_generators/d3p_crash_ty_stack_overflow_protocol_flatten__mut0_7646fc90.py`: CPython ok; mypy 2.4.0 2 errors, ty 0.0.84 stack overflow, pyright 2 errors; mypy 2.4.1 2 errors, ty 0.0.97 stack overflow; mypy master 2 errors. The 2 mypy/pyright errors are line 28, `s.flatten()` ("Invalid self argument `Stream[int]` ... `Callable[[Stream[Stream[T]]], None]`", mypy `[misc]`; pyright "Could not bind method `flatten` because `Stream[int]` is not assignable to parameter `self`"), and line 32, the intended `t.missing()`. The generated program therefore has one error its author did not expect; ty reports neither because it aborts first (on the argument check of `Impl()` against `Stream[int]`).

The original Day-2 parent (`runs/hits/d3p_crash_ty_stack_overflow_protocol_flatten.py`, protocol + `@asynccontextmanager` + `reveal_type`, nothing assigned) overflows ty 0.0.84 but passes ty 0.0.97; the Day-3 variant adds `open_stream(Impl())`, which still overflows 0.0.97. Reduction showed the decorator and the async code are irrelevant. The trigger is checking a class against the protocol.

Minimal reproducer (12 lines; `runs/hits/d4v_protocols_expanding_self_receiver.py` has the same code under a 3-line header):

```python
from typing import Protocol


class Stream[T](Protocol):
    def flatten(self: "Stream[Stream[T]]") -> None: ...


class Impl:
    def flatten(self) -> None: ...


x: Stream[int] = Impl()
```

```
$ $K/python c2_protocol_receiver.py                   exit=0
$ mypy (pinned)                                       exit=0, no output
$ ty 0.0.84 (pinned)
thread '<unknown>' (561315) has overflowed its stack
fatal runtime error: stack overflow, aborting                          exit=134
$ pyright (pinned)
0 errors, 0 warnings, 0 informations                                   exit=0
$ mypy 2.4.1: exit=0;  ty 0.0.97:
thread '<unknown>' (561426) has overflowed its stack
fatal runtime error: stack overflow, aborting                          exit=134
$ pyright (latest): 0 errors;  mypy master: exit=0, no output
```

### (2) SPEC

Spec text (https://typing.python.org/en/latest/spec/protocol.html, also in the local `protocol.txt`):

- "The self-types in protocols follow the rules for other methods." (section Self-types in protocols). The rules for other methods (annotations page, "Annotating instance and class methods") only describe an unannotated `self`, `Self`, and a TypeVar-annotated `self`. An explicitly nested annotation such as `self: Stream[Stream[T]]` is not covered.
- "a class is considered assignable to the protocol in situations where the decision depends on itself." (Recursive protocols). This fixes the answer when the same relation recurs. Here each re-check needs a larger type (`Stream[int]`, `Stream[Stream[int]]`, `Stream[Stream[Stream[int]]]`, ...), so no relation repeats and the sentence does not decide it.
- "A concrete type X is assignable to a protocol P if and only if X implements all protocol members of P with assignable types." (Assignability relationships).

Spec: silent on whether `Impl` is assignable to `Stream[int]` (non-regular, ever-growing recursion). Documented intent: DESIGN.md §2 "CRASH ... Always a bug". ty's tracker treats the family as bugs (`fatal`, `protocols`): #4694, #4863 (closed, same `self: Capybara[Capybara[U]]` shape) and #4882 (open).

### (2b) The accused tool's side

ty binds the protocol method to the implementer and so checks `Impl` against the receiver annotation. For `Stream[int]` the receiver is `Stream[Stream[int]]`; proving `Impl <: Stream[Stream[int]]` needs the receiver `Stream[Stream[Stream[int]]]`, and so on. A coinductive "assume true on cycle" rule (which the spec endorses for recursive protocols) cannot fire because the type grows each round. So ty needs a depth/size bound; it does not have one for receivers. Whichever answer such a bound gives (accept like mypy/pyright, or reject) is acceptable; abort is not.

The same receiver check gives a different failure on non-expanding annotations (same symptom class as the open ty#4746, whose own program is only `self: "HasMeth"`; fix proposed in ruff#29450; that the variants below share its root cause is my inference, not verified):

```
self: "Stream[T \| None]"  or method-level  def flatten[U](self: "Stream[Stream[U]]")
ty 0.0.84 and 0.0.97:  error[invalid-assignment]: Object of type `Impl` is not assignable to `Stream[int]`
mypy, pyright:         accept
```

So ty either rejects (ty#4746) or overflows (this candidate) on the same line, depending on whether the receiver type grows. mypy and pyright terminate in both cases. Probes `q1`..`q5`: assigning `Impl()` to `Stream[int]` in a parameter, a return and a list element overflows the same way; `Stream.flatten(v)` with `v: Stream[int]`, and the call `value.flatten()` in a function, are accepted by ty while mypy reports `arg-type` / `[misc]` and pyright reports an argument or binding error (also the line-28 error above). Side observation, not part of this verdict: ty may not enforce an explicit nested `self` annotation on protocol receivers, which could be a false negative or a design difference like ty#4656; the spec is silent, so it needs its own check.

### (3) STRONGEST ORACLE

Checker abort on a program CPython runs fine, while two independent checkers terminate on it. Self-contradiction: the non-expanding sibling is judged by the same code path and produces a diagnostic.

### (4) GENERALISE (`/tmp/d4v1/c2*`; pinned ty and latest ty identical unless noted)

| variant | CPython | mypy | ty | pyright |
|---|---|---|---|---|
| minimal (above) | ok | clean | **overflow** | 0 err |
| `self: "Stream[list[T]]"` | ok | clean | **overflow** | 0 err |
| `Stream[tuple[T]]` | ok | clean | **overflow** | 0 err |
| `Stream[dict[str, T]]` | ok | clean | **overflow** | 0 err |
| self parameter named `this` | ok | clean | **overflow** | 0 err |
| old-style `TypeVar("T", covariant=True)` + `Protocol[T]` | ok | clean | **overflow** | 0 err |
| generic `Impl[T]` | ok | clean | **overflow** | 0 err |
| method returns `T` | ok | 1 err | **overflow** | 0 err |
| `use(Impl())` with `def use(v: Stream[int])`, or `return Impl()`, or `[Impl()]` | ok | clean | **overflow** | 0 err |
| `Stream[Stream[Stream[T]]]` with a call `value.flatten()` only | ok | 1 err | clean | 1 err |
| declaration only; or `def use(value: Stream[int])` only | ok | clean | clean | 0 err |
| control `self: "Stream[T]"` | ok | clean | 1 diag (ty#4746) | 0 err |
| control `Stream[T \| None]` | ok | clean | 1 diag | 0 err |
| control method-level `[U]` | ok | clean | 1 diag | 0 err |
| control unannotated `self` | ok | clean | clean | 0 err |
| non-protocol generic class with the same annotation, call `Stream[int]().flatten()` | ok | 1 err | 1 diag | 1 err |
| `Impl` without `flatten` | ok | 1 err | 1 diag | 1 err |

Related programs from the tracker, run on pinned and latest ty: ty#4863's program overflows/times out on 0.0.84 (rc 124 at 120 s) and is clean on 0.0.97 (fixed, as the issue says); ty#4882's program overflows on both; ty#4746's program is rejected (1 diag) on both; ty#4694's program gives 5 diagnostics, no crash, on both.

### (5) DUPLICATES

ty tracker regexes (title + body): `overflowed its stack.{0,3000}Protocol` and the reverse -> #4882, #4691, #4099, #3397, #3398, #3015, #4694, #1736 (none uses an explicit nested `self` receiver except #4694); `protocol_apply_self_with_receiver` -> #4746, #4337, #4222; `self: *"?\w+\[\w+\[` -> #4863, #4694, #4337 and unrelated ones; `flatten` -> #4863, #4694, #4337, #4329 (variadic callable inference); `self.{0,30}annotat.{0,60}protocol` -> #4746; `Stream\[Stream` -> #4694, #2123; `explicit receiver` -> none; `receiver annotation` -> #4746, #4619; `stack overflow.{0,1500}self: ` -> #4863, #4694, #1402; `self: .{0,300}overflowed its stack` -> none.

`gh search issues --repo astral-sh/ty`: `protocol self stack overflow`, `protocol receiver overflow`, `nested protocol stack overflow`, `protocol self annotation`, `explicit receiver protocol`, `protocol Self receiver stack overflow` -> no results; `protocol_apply_self_with_receiver` -> #4746, #4337, #4222; `overflowed its stack` -> #4898, #4691, #4882, #4900, #4148, #4104, #4099, #4694. `gh search prs --repo astral-sh/ruff "protocol receiver"` -> #29443 (merged, "Compare protocol receiver restrictions before binding"), #29341 (open), #29543 (open), #27301 (merged, "Cache protocol receiver binding"), #27227 (closed), #28293 (merged), #29450 (open, fixes ty#4746).

Read in full (`gh issue view`): ty#4746, ty#4882, ty#4694, ty#4863.

- ty#4746 (OPEN, `cycles`, `method-receiver`, `protocols`): false positive when `self` is annotated with the protocol itself; same query (`protocol_apply_self_with_receiver`), different symptom and no growth. Fix PR ruff#29450 seeds the cycle with the "receiver satisfies annotation" assumption; that does not obviously bound a growing receiver (not tested, the PR is unmerged).
- ty#4882 (OPEN): two protocols `P1.a(self, other: "P1[T2]")`, `P2.a(self, other: "P1[T2] \| P2[T2]")`; no receiver annotation, no assignment. Different program. Still overflows 0.0.97. KB entry `TY-4882` (`requires: protocol_selfref_pair`) does not match ours.
- ty#4694 / ty#4863 (CLOSED): `flatten[U](self: Stream[Stream[U]])` plus `window() -> Stream[Stream[T]]`, a factory call and a constraint-solver cause; closed (#4863 is "fixed by astral-sh/ruff#29809" per the text of #4882; the fix for #4694 was not looked up). Our program has no factory call and no `window`, and overflows after those fixes.

Our reproducer matches none of them, so I treat it as NEW. Risk: maintainers may fold it into the protocol-receiver family (#4746/#4882). KB: `TY-4882` and `TY-4900` (expanding generic base) are similar in spirit but `requires` different features, so neither closes it.

mypy and pyright: not applicable (no crash, accepted program).

### (6) PLAYGROUND

UNVERIFIED-PLAYGROUND (cannot be done from the shell; the draft keeps the `<PLAYGROUND LINK>` placeholder).

### (7) VERDICT

- ty: BUG / CRASH, conf 0.80, faulty_tool ty, NEW. Draft: `campaign/day4/issue-drafts-v1.md` draft 1. Hit file: `runs/hits/d4v_protocols_expanding_self_receiver.py`.
- mypy: NOT_BUG / NOISE (accepts the program, terminates), conf 0.80.
- pyright: NOT_BUG / NOISE, conf 0.80.

---

## C3. `partial | None` in a loop (ty salsa panic; day-3 seed c47eb01468dc)

`[Plan §6 / verify C3]`

### (1) REPRODUCE

Generated program `runs/day3/gen/callables/d3p_crash_ty_panic_partial_or_none_in_loop__mut1_82a9fbe2.py`: CPython ok; mypy 2.4.0 1 error; **ty 0.0.84 panic**; pyright 1 error; mypy 2.4.1 1 error; **ty 0.0.97 1 diagnostic (no panic)**; mypy master 1 error.

Minimal reproducer (5 lines; `/tmp/d4v1/final/c3_partial_loop.py`):

```python
from functools import partial

value = partial(print)
for _ in range(2):
    value = value | None
```

```
$ $K/python c3_partial_loop.py
TypeError: unsupported operand type(s) for |: 'functools.partial' and 'NoneType'     exit=1
$ mypy (pinned):  c3_partial_loop.py:5: error: Unsupported left operand type for | ("partial[None]")  [operator]
$ ty 0.0.84 (pinned):
fatal[panic] Panicked at /root/.cargo/registry/src/index.crates.io-1949cf8c6b5b557f/salsa-0.28.5/src/function/execute.rs:751:9 when checking `.../c3_partial_loop.py`: `infer_definition_types(Id(403)): execute: too many cycle iterations`
Found 1 diagnostic                                                      exit=101
$ pyright (pinned): 5:13 - error: Operator "|" not supported for types "partial[None]" and "None" (reportOperatorIssue)
$ ty 0.0.97 (latest): c3_partial_loop.py:5:13: error[unsupported-operator] Operator `|` is not supported between objects of type `partial[Overload[...]] | Unknown` and `None`   exit=1
$ mypy 2.4.1 / master: same error as pinned mypy;  pyright (latest): same as pinned
```

Release bisect with `uvx --from ty==X ty check ...` on the module-level variant `/tmp/d4v1/p/m3.py` and on the minimal file: 0.0.84 panics; 0.0.85, 0.0.88, 0.0.91, 0.0.94, 0.0.95, 0.0.96 report `unsupported-operator` without panic. The panic is fixed in **0.0.85** (released 2026-10-06). The 0.0.85 release notes list several cycle fixes; the likely one is ruff#29024 "Preserve cycle markers in ParamSpec specialization" (not verified by building ty; the evidence is that the ParamSpec-generic wrappers `staticmethod` and `classmethod` panic while `property`, `slice` and `object` do not).

### (2) SPEC

Not a typing-spec question. `functools.partial` defines no `__or__`, CPython raises `TypeError`, so the expected result is an operator error, which mypy, pyright and ty 0.0.97 all report. The spec does not say anything about `X | None` between runtime objects that are not types. Intent: DESIGN.md §2 "CRASH ... Always a bug". Checkers must not panic on invalid code.

### (2b) The accused tool's side

Nothing to argue: on 0.0.84 ty fails to terminate type inference of a loop-carried variable (salsa fixpoint "too many cycle iterations") on invalid code. The first iteration alone (`value = value | None` once, no loop) is fine in ty 0.0.84 (`s7`-style probe, clean), so the loop-carried fixpoint is the trigger. The latest ty converges on the same program.

### (3) STRONGEST ORACLE

Tool self-contradiction across releases: the same ty reports `unsupported-operator` on 0.0.85+ and on the non-loop program, and panics inside the loop. Runtime error and two independent checkers agree on the diagnostic.

### (4) GENERALISE (`/tmp/d4v1/c3`, `/tmp/d4v1/c3b`, `/tmp/d4v1/hv`; ty column is pinned 0.0.84 / latest 0.0.97)

| variant | CPython | mypy | ty 0.0.84 | ty 0.0.97 | pyright |
|---|---|---|---|---|---|
| `partial(f)` while loop, `value \| None` | ok | 1 err | **panic** | 1 diag | 1 err |
| `for` loop version | ok | 1 err | **panic** | 1 diag | 1 err |
| `None \| value` | ok | 1 err | **panic** | 1 diag | 1 err |
| module level | TypeError | 1 err | **panic** | 1 diag | 1 err |
| `partial(print)` for loop | TypeError | 1 err | **panic** | 1 diag | 1 err |
| `staticmethod(print)` for loop (3 lines) | TypeError | 1 err | **panic** | 1 diag | 1 err |
| `staticmethod(f)` `None \| value` | ok | 1 err | **panic** | 1 diag | 1 err |
| `classmethod(f)` | ok | 3 err | **panic** | 1 diag | 2 err |
| `classmethod(print)` | TypeError | 2 err | **panic** | 1 diag | 1 err |
| `partial(int)` | ok | 1 err | 1 diag | 1 diag | 1 err |
| `value & None`, `value + 1`, `partial + None` | TypeError / ok | errors | 1 diag | 1 diag | errors |
| `object()`, `slice(1)`, `property(print)`, `K.p` | TypeError / ok | 1 err | 1 diag | 1 diag | 1 err |
| `partial(print)`, two assignments, no loop | TypeError | 1 err | clean | 1 diag | 1 err |
| single assignment `value \| None`, no loop | TypeError | 1 err | clean | 1 diag | 1 err |

(ty 0.0.84 is silent on the two no-loop rows while ty 0.0.97, mypy and pyright report the operator error. That is a separate false negative of the pinned ty, gone in 0.0.97, and not investigated further.)

### (5) DUPLICATES

ty tracker regexes: `infer_definition_types.{0,200}too many cycle` -> 44 issues (all `[panic]` reports; the recent ones are #4905, #4618, #4615, #4492, #4443, #3838, #3627, #3499, #3011, #2564); `too many cycle iterations.{0,2000}(partial\|loop\|while)` -> 41; `(partial\|staticmethod)\(.{0,500}\| None` -> #3467 (partial typevars, unrelated), #2504; `value = value \| None` -> none; `unsupported-operator.{0,500}(panic\|cycle)` -> #1630 (closed, different query); `functools.partial.{0,300}(panic\|fatal)` -> none; `while.{0,200}\| None.{0,300}panic` -> none.

`gh search issues --repo astral-sh/ty`: `functools.partial panic`, `partial cycle`, `partial union None loop`, `cycle iterations loop`, `staticmethod panic`, `union None loop panic` -> no results. `gh search prs --repo astral-sh/ruff`: `partial panic`, `ParamSpec specialization cycle` -> no results by those words; the fix candidate was found through the 0.0.85 release notes (`gh release view 0.0.85 --repo astral-sh/ty`) and `gh pr view 29024 --repo astral-sh/ruff` (merged 2026-09-30, "Addresses the generic-specialization reproducer in ty#4615").

Closest open issues: ty#4615 ("Cycle-iteration panic when specializing a decorated generic class in a loop", OPEN, `paramspec`), ty#4613. Both are different programs. The KB entry `TY-4899` accepts `ty:panic@.*` signatures but `requires: paramspec_self_callable_init`, so it does not match.

Since the bug is already fixed in the next release, nothing needs to be filed. Playground-free reproduction on 0.0.84 stays in `runs/hits/d4v_callables_staticmethod_loop_union.py` as a regression guard.

### (6) PLAYGROUND

UNVERIFIED-PLAYGROUND (not needed, nothing to file).

### (7) VERDICT

- ty 0.0.84 (pinned): BUG / CRASH (salsa panic), conf 0.97, faulty_tool ty. Status: fixed in ty 0.0.85, so not reportable. Not a duplicate of an open issue.
- ty 0.0.97, mypy, pyright: NOT_BUG / NOISE (correct `unsupported-operator`), conf 0.95.

Hit file: `runs/hits/d4v_callables_staticmethod_loop_union.py`.

---

## Notes for the pipeline (not applied)

1. No `known_upstream.json` entry exists for ty#4148, so the Day-3 queue showed the ty stack overflow of C1 as a live crash even though the mypy twin was closed by `MYPY-22361`. Add `TY-4148` as described in C1 (5).
2. C3 is a pinned-only crash. The `RERUN-BEFORE-REPORTING` hint on the report was right: re-running on ty 0.0.97 removed it. A cheap automatic step "rerun crash findings on the latest ty before ranking them" would have removed this candidate from the queue.
3. The new hit file `d4v_callables_mutual_call_attr.py` adds the mutual-recursion form of C1; `d4v_protocols_expanding_self_receiver.py` carries the receiver-growth idea of C2 as a parent for mutation.
4. The shell tool's output was unreliable in this session (stdout sometimes lost). All evidence above comes from output files written by scripts under `/tmp/d4v1` (`run.sh`, `matrix.py`, `trk.py`, `s*.sh` and `out_s*.txt`); that directory is outside the repo and will vanish on reboot.
