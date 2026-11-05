# Stage A verify-review: Day-3 verification and issue drafts

Reviewed: `campaign/day3-verification.md` and `campaign/day3-issue-drafts.md` on branch `campaign/day4-p2` (HEAD 3383e2f).
Venvs: pinned `.venv` (mypy 2.4.0, ty 0.0.84, pyright 1.1.414, Python 3.13) and `/tmp/d3v-latest` (mypy 2.4.1, ty 0.0.97, pyright 1.1.414, called through `memguard.sh`).
Nothing was pushed and no GitHub write call was made. All `gh` calls were `search`, `issue view`, `pr view` or `api` GET.

**Verdict: APPROVED.** All four claimed new bugs reproduce exactly as recorded on both ty/mypy versions, no duplicate was found that matches the same program, and the flaky-test fix holds. Several non-blocking accuracy gaps in the drafts' duplicate lists are listed at the end.

## 1. Reproducer re-runs

I ran the four `runs/hits/d4v_*.py` reproducers and, separately, the code blocks pasted verbatim from each draft (so a transcription error in a draft would show). Pyright exists only as 1.1.414 in both venvs, so it was run once per file (the first attempt through `memguard.sh` hit a systemd "scope already loaded" collision and was retried).

| Claimed bug | pinned (ty 0.0.84 / mypy 2.4.0) | latest (ty 0.0.97 / mypy 2.4.1) | others | Matches record |
|---|---|---|---|---|
| ty: stack overflow on protocol `flatten` (`self: Stream[Stream[T]]`) | `overflowed its stack`, exit 134 | same | mypy: Success; pyright: 0 errors | yes |
| ty: alias narrowing across a loop back edge | `All checks passed!` | same | mypy `Unsupported operand types for + ("None" and "int")`; pyright `reportOptionalOperand`; CPython `TypeError` | yes |
| ty: `__eq__`-only class accepted as `Hashable` | accepts `Plain()`, `Sub()`; rejects `Record` (mutable dataclass) | same | mypy accepts; pyright rejects Plain, Sub, Record; CPython `unhashable type` | yes |
| mypy: metaclass reflected operator | 2 errors (`assignment`, `assert-type`) at lines 18/19 of the draft code | same | pyright same 2 errors; ty accepts; CPython prints `str` | yes |

Draft variant claims I re-ran and confirmed: ty overflows for `Stream[list[T]]` and for the old-style `TypeVar` + `Protocol[T]` form; it does not overflow when `value.flatten()` is only called on a `Stream[int]` parameter; `Stream[T | None]` is rejected by ty (not a crash) while mypy and pyright accept. For the loop alias: a `while` loop reveals `int` on ty (bug), moving the reassignment before the use reveals `None`, and recomputing the alias inside the loop reveals `int` (sound). For hashability: `__ne__`-only and `__lt__`-only classes are accepted by ty, mypy and pyright (so the draft's "must not flag" note holds); `{WithEqSlots()}` is accepted by ty and flagged by pyright (`reportUnhashable`). For the metaclass operator: the instance form `L() * R()` gives no mypy error, and the `A | B` class-object form reproduces the same mypy error and the ty behaviour from ty#4683. The `covers_at_runtime(right_type, left_type)` guard the draft names is at `mypy/checkexpr.py:4194-4195`, and `covers_at_runtime` only treats the supertype specially when it is a type-object callable, so the draft's "possible cause" is plausible (the draft marks it unverified, correctly). The ruff mdtest section "Narrowing is invalidated when target is reassigned" exists in `narrow/aliased_conditions.md` with the quoted sentence.

Dismissed-candidate reproducers also re-run: Flag combination (ty reveals `Literal[F.R, F.W]` and `Never` in the final `else`), read-only property (ty reveals `Never`, mypy and pyright report the read-only assignment), recursive alias (mypy prints `tuple[str, ...]`, ty and pyright narrow), tuple-subclass fold, enum value alias (mypy and pyright report 3 errors, ty none), self-referential `__call__` mutual pair (ty overflow, compiled mypy core dump, pyright clean), `partial | None` staticmethod loop (ty 0.0.84 panics, 0.0.97 reports `unsupported-operator`). All match the verification table. The claim that the panic is "fixed in 0.0.85" could not be checked here because only 0.0.84 and 0.0.97 are installed.

## 2. Duplicate searches (different phrasings from the consolidate step)

About 60 phrasings across `gh search issues/prs`, plus regexes over the 4060-issue ty dump `/tmp/d3v-trk/ty.json`. Many multi-word `gh search` queries returned empty, which is GitHub's AND-matching and not evidence of absence, so the tracker dump and one-or-two-word queries were the real check.

Stack overflow on protocol flatten: queries "flatten", "protocol receiver", "method-receiver", "overflow protocol", "fatal runtime error stack overflow", "Stream[Stream[T]]", regexes for `overflow(ed) its stack`, `Stream[Stream`, `self: .*[.*[T]]`. No issue contains this program. Nearest: #4882 (open, two protocols, different program), #4746 (open, non-crashing rejection), #4694 and #4863 (closed, need `window` plus a factory call; #4863 states that deleting `flatten` or `window` makes it pass), #3773 (closed, `cast`). Not listed in the draft and worth adding as related: #4337 (closed panic, `flatten[G](self: Proto[Proto[G]])`, same `protocol_apply_self_with_receiver` path), #4222 (closed panic, receiver `HableT[_T]`, same regression window as #4746), #4900 (open, stack overflow from a base class that expands its own type argument, same "ever-growing type" mechanism), #1587 (open, mutually recursive generic protocols). None is the same program. Verdict stays "new".

Alias narrowing in a loop: queries "aliased", "alias narrowing", "conditional alias", "narrowing alias loop", "narrowing reassigned loop", "stale narrowing loop", ruff PR search "aliased conditional", regexes for `aliased? (condition|conditional)`, `is_none =`. Only #719 (closed, completed by ruff#24302, the feature itself), #23937 (the feature PR), #4379 (closed, direct narrowing in a `while` loop) and #2792 (open, calls) match. Same program: none. Verdict stays "new".

`__eq__`-only class as `Hashable`: queries "__hash__", "unhashable", "Hashable", "hashability", "__eq__ hash", ruff PR search "unhashable", "Hashable". Nearest: #3781 (open, set/dict displays, dataclass example only), #4157 (closed by ruff#27441, explicit `__hash__: ClassVar[None]`), #4748 (closed, restoring `__hash__`), ruff#29471 (merged, subclasses restoring hashability). The PR text of ruff#27441 covers "unhashable classes, built-in containers, mutable dataclasses", with no mention of implicit `None` from `__eq__`. One find the draft omits: ruff#26040 (closed unmerged, "Model hashability for union simplification") states explicitly that "a final class can ... implicitly disable hashing by defining `__eq__`", so ty maintainers know the rule and have not implemented it for protocol checks; this supports the report and should be linked. Verdict stays "new".

mypy metaclass reflected operator: queries "metaclass __rmul__", "metaclass reflected", "metaclass operator", "type object operator metaclass", "__ror__ metaclass", "reverse operand subclass class objects", "metaclass __radd__", "reflected operator", "covers_at_runtime", PR searches. Only #4929 and #4789 (both about `Type[Foo]` operators, closed, not about reflected priority) and #19006 (tuple subclass, closed) surface. No duplicate. Verdict stays "new".

## 3. Challenges to the verdicts

ty protocol overflow, BUG. A crash is never spec-ambiguous; ty aborts on a program that CPython runs and two other checkers accept. The only soft spot is the draft's root-cause paragraph, which states the mechanism (receiver grows each round, cycle assumption never fires) as fact. Nothing in the reproducer shows that; it is an inference from #4863's stack trace. It should be hedged before filing.

ty loop-alias narrowing, BUG. ty documents invalidation on reassignment in its own mdtest, the unsoundness shows at runtime, and the same sound behaviour holds for straight-line code and branches. The loop back edge is the only gap. Not intended.

ty `Hashable`, BUG (confidence 0.7 is right). The typing spec is silent on implicit `__hash__ = None`, typeshed gives `object.__hash__`, and mypy accepts the program (open mypy#20230, #18622, #2455 call that a false negative). The deciding point is ty's own inconsistency: it rejects the mutable dataclass, which gets the identical implicit `None`. Maintainers could call it "known, scoped out" (ruff#26040 suggests they know), but no issue says so.

mypy metaclass reflected operator, BUG at 0.7. Pyright's maintainer rejects the instance version because a declared `Foo` may be a subclass (pyright#4088). That argument does not apply to two named classes, and mypy already implements the rule for instances, so the inconsistency in mypy is real. The remaining risk is that mypy maintainers treat class objects as out of scope.

Dismissals that could hide something:
- Self-referential `__call__` (`#4148`, `mypy#22361`): the cited issues use the one-class form. The mutual pair `A.__call__: "B"` / `B.__call__: "A"` crashes the same way but is a different cycle shape, and a fix for the self-cycle might not cover it. Dismissal is acceptable; add the mutual-pair program as a comment when someone engages those issues.
- IntEnum/value alias: the cited `mypy#16830` is CLOSED/COMPLETED (2026-01-16) yet the identical false positives reproduce on mypy 2.4.0 and 2.4.1 (also for `B = A` name aliases, which is #21117, still open). So "already reported" holds through #21117, but #16830 was closed without fixing this, which the verification does not say. The upstream entry should reference #21117 as the live issue and record #16830 as closed-but-still-reproducing.
- Flag combination (`ty#876`): #876 is an umbrella tracking list with one checkbox for `enum.Flag`. A duplicate in the "covered by roadmap" sense, not a specific bug report. Fine for retiring the pattern, but not evidence that anyone has the `Never` else-branch on their radar.
- Read-only property `Never` and stale alias after a method call (`ty#2792`): the repro mutates `self.n` in a method between two asserts, which is exactly the title of #2792. Same root cause.
- Tuple-subclass fold (`ty#2171`/`#2140`): #2140 is closed-completed, a deliberate assumption; #2171 is the open request for a diagnostic. DESIGN_DIVERGENCE is correct.
- Recursive alias `...` (`mypy#2008`): covers only the missing binder narrowing on initial assignment, as the verification itself admits. The `...` display of a recursive placeholder is unreported; the NOT_BUG call rests on it being a printing artefact, which is reasonable.
- `__hash__` None reveal (`mypy#20230`): that issue's example is exactly an `__eq__`-only class, so the dismissal is exact.
- ty#4656/#4673/#4849 side outcome: states and dates match (4656 closed not planned 2026-10-05, 4673 closed duplicate 2026-10-05, 4849 closed duplicate 2026-10-28).

## 4. Flaky-test fix

`tests/test_runner_timeout_kills_group.py` run 10 times with 4 `yes > /dev/null` burners: 10/10 runs "3 passed" (about 5.05 s each). Burners killed afterwards; no `yes` process remained. The test body is as the log describes (5 s timeout, atomic pidfile, 30 s polling deadlines, `_alive` tolerant of `/proc` races, `finally` kill). One weakness, not a defect: if `_read_pid` never finds a pidfile the test fails with a clear message instead of flaking, which is the intended behaviour.

## 5. Non-blocking observations

Duplicate lists in the drafts are incomplete for draft 1 (missing #4337, #4222, #4900, #1587) and draft 4 (missing ruff#26040). The drafts say "none found", which stays true, but a maintainer reading the issue would expect these links. The root-cause paragraph in draft 1 should say "probably". Draft 2's "handled correctly" list includes a `for x in xs` case I did not re-run in that exact shape. The consolidate doc cites `mypy#16830` as a plain duplicate without noting it is closed. An untracked file named `-l` sits in the repository root (`git status`), likely from a mistyped command; it is not part of either document and should not be committed. The `d4v_eq_no_hash_hashable.py` reproducer loops over `(Plain(), Sub())` and so checks the union `Plain | Sub`, while the draft calls `need(Plain())` directly; both behave the same on ty 0.0.84 and 0.0.97.

## Blocking issues

None.
