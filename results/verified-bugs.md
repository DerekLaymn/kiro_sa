# Verified bugs (drafts 1 to 12)

Copied from section 5 of [FINAL-SUMMARY.md](FINAL-SUMMARY.md). The full reports with reduced programs, tool versions and duplicate searches are in [bugs.md](bugs.md). Issue states were read on 2026-11-06 and may have changed since.


"Verified" here means: reduced, run on CPython 3.13.16 and on the pinned and newest versions of each tool, and searched on the trackers, with verdict STILL-BUG-NEW in `results/bugs.md`. It does not mean a maintainer confirmed it. **Only drafts 1 and 2 were verified by the authors on a playground;** drafts 3 to 12 have a `<PLAYGROUND LINK>` placeholder (drafts 3 to 9 were filed anyway by the authors' account; whether the authors ran them on a playground first is not recorded). Confidence is the draft's own number. Filing state is from the author listing and `gh issue view` of 2026-11-06 (read-only).

| # | Tool | One-line description | Verdict | Conf. | User playground | Filed / state |
|---|---|---|---|---|---|---|
| 1 | ty | stack overflow when a class is checked against a protocol whose method annotates `self` as `Stream[Stream[T]]` | STILL-BUG-NEW (CRASH), none found | 0.80 | yes | ty#4933, open (labels `bug`, `fatal`; maintainer comment says a fix PR has blockers) |
| 2 | ty | alias narrowing (`is_none = x is None`) survives a reassignment that reaches the use over a loop back edge | STILL-BUG-NEW, none found | 0.9 | yes | ty#4934, **closed completed** 2026-11-05; fixed by astral-sh/ruff#30074 "[ty] Invalidate aliased conditions across loop iterations" (merged 2026-11-05 22:09 UTC) |
| 3 | mypy | reflected operator of a subclass metaclass ignored for class-object operands (`A * B`); cause confirmed by instrumenting mypy master | STILL-BUG-NEW | 0.7 | no | mypy#22377, open; a contributor offered to fix it (2026-11-06) |
| 4 | ty | class with `__eq__` and no `__hash__` accepted as `Hashable` | STILL-BUG-NEW | 0.7 | no | ty#4941, open (labels `bug`, `runtime semantics`, `unsoundness`) |
| 5 | mypy | `Foo[int, str]` on a class with a `TypeVarTuple` followed by a defaulted `ParamSpec` is rejected and inferred as `Any`; runtime half is python/typing#2211 | STILL-BUG-NEW (mypy only) | 0.7 | no | mypy#22375, open (`bug`) |
| 6 | ty | `except` clause sees the old value after a nested unpacking target failed half-way through an assignment | STILL-BUG-NEW (ty 0.0.97 and 0.0.98) | 0.5 | no | ty#4958, open, no labels |
| 7 | pyright | `RangeError: Maximum call stack size exceeded` when a descriptor `__get__` is decorated by a class-body function without `self` | STILL-BUG-NEW (CRASH, pyright 1.1.414 = latest) | 0.8 | no | pyright#11984, open (`bug`) |
| 8 | mypy | overloaded `__post_init__` of a dataclass: every overload item is checked against the InitVar signature, so an item without the InitVar type gets `[override]` | STILL-BUG-NEW (2.4.0, 2.4.1, master) | 0.6 | no | mypy#22385, open (`bug`) |
| 9 | mypy | `a < b` for two operands of the same type tries `b.__gt__` first when `__lt__` and `__gt__` come from different classes of the MRO; the inferred type is that of the wrong method | STILL-BUG-NEW | 0.6 | no | mypy#22386, open (`bug`) |
| 10 | mypy | `possibly-undefined` does not report a name assigned in a `with` block whose `__exit__` returns `bool`, although the name is unbound after a swallowed exception (pyright reports it; ty only with an off-by-default rule) | STILL-BUG-NEW (opt-in check, FALSE_NEGATIVE) | 0.4 | no | **not filed** |
| 11 | mypy | a `lambda` with other parameter names (or positional-only parameters) is accepted for a callback protocol whose `__call__` names its parameter, while the equivalent `def` is rejected | STILL-BUG-NEW (2.4.0, 2.4.1, master; ty and pyright reject) | 0.5 | no | **not filed** |
| 12 | pyright | `closed=True` and `extra_items=` on a `typing.TypedDict` class are accepted for `pythonVersion` below 3.15, where CPython raises `TypeError` | STILL-BUG-NEW (1.1.414 = latest); same report exists for mypy (#21747) and was fixed in ty (#4031) | 0.35 | no | **not filed** |

Notes on the table:

* Days of origin: drafts 1 to 4 from Day 3 candidates (verified on Day 4, re-checked on Day 6), 5 from Day 6, 6 and 7 from Day 7, 8 from Day 8, 9 and 10 from Day 9, 11 and 12 from Day 10.
* By tool: ty 4 (drafts 1, 2, 4, 6), mypy 6 (3, 5, 8, 9, 10, 11), pyright 2 (7, 12); 12 in total.
* By class (the drafts' own labels, grouped here): 2 crashes (1, 7); 5 false negatives (2, 4, 10, 11, 12); 5 false positives or wrong inference (3, 5, 6, 8, 9).
* Draft 2 is the highest-confidence draft (0.9, playground-verified). It was fixed upstream the day it was filed (ruff#30074 merged), which is the only confirmed maintainer outcome that is a fix. Of the open drafts, only ty#4933 (a maintainer reply about a fix PR with blockers) and mypy#22377 (a contributor offered a fix) have comments; ty#4941, mypy#22375, ty#4958, pyright#11984, mypy#22385 and mypy#22386 have none.
* The Day-10 draft 11 text originally said "21 `only_ty` rows"; the saved reports give 10 in the three named mutants. Corrected afterwards (`days/day10-report.md` section 5).
