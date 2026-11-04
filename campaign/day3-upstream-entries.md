# Day 3 upstream entries [Plan §6 step 8 / Day 3 morning / record upstream]

Branch `campaign/day3-p2`. Pinned tools: mypy 2.4.0 (compiled), ty 0.0.84, pyright 1.1.414, Python 3.13. Issue states
re-read with `gh issue view` on 2026-11-04/05 and written into each note.

Commits: `ce63f5c` (crash entries, `typediff/crash_upstream.py`, kb.py loader skip, pipeline hook, tests, data),
`ca5f30b` (discrepancy entries, new `requires` matchers in kb.py, priors, tests), plus one docs/report commit (see the
final message for its sha).

## Schema extension (crash)

`kind: "crash"` entries carry `tool`, `signature` (regex, `re.fullmatch` on `Crash.signature`) and a mandatory
`requires` (function of the parsed program in `crash_upstream._CRASH_REQUIRES`). `Pipeline._judge` calls `match_crash`
for findings with `symptom == CRASH` only (after `f.signature` is set, before the prior cap); a hit sets
`Tier.DISMISSED`, `Dismissal.DUPLICATE` and adds `DUPLICATE of <url> (<id>): <note>` to `review_notes`.
`abnormal_exit` findings and all discrepancy findings take the old path. `kb._upstream_entries` skips crash entries.
Discrepancy entries deliberately have no `stance` field, so `priors.py` does not turn their broad
codes/message into a REVIEW cap on unrelated findings (their precision lives in `requires`).

## Table

| id | issue URL | status (2026-11-04/05) | category | what it matches | tests | replay count |
|---|---|---|---|---|---|---|
| TY-4882 | https://github.com/astral-sh/ty/issues/4882 | open | entry (crash) | ty `ty:signal-SIGABRT:stack-overflow` + two Protocol classes, A.method takes `A[..]`, B.method takes a union holding `A[..]` and `B[..]` | ty_TB, t20a, ty_20 close; C1, D7 do not; e2e | n/a (no Day-2 out3) |
| TY-4883 | https://github.com/astral-sh/ty/issues/4883 | closed completed (ruff#29933 per team); pinned still slow | entry (crash) | ty `ty:timeout` + chain of >= 12 `type Tn = tuple[Tm, Tm]` aliases + function comparing two params of the top alias. Depth 20 takes 9.5 s (no timeout, nothing to close), depth 24 takes 148 s > 120 s runner timeout | depth24 closes (unit + e2e); depth20 stays no-finding | n/a |
| TY-4884 (+`-REVEAL`, `-ASSERT`) | https://github.com/astral-sh/ty/issues/4884 | closed completed (ruff#29903); pinned still reproduces | entry x3 | only_mypy `assignment` / reveal_mismatch ``Revealed type: `Unknown` `` / only_ty `type-assertion-failure` with `Unknown`; requires: statement calls a function whose parameter is itself a subscripted generic TypedDict over a function TypeVar | bug-05 (+witness), probe-bug05; controls: `Box[T]`, nested TypedDict (ty#4803 shape), `takes_int(c)`, `z: Resp[int] = c`; kb-selftest example | n/a |
| TY-4898 | https://github.com/astral-sh/ty/issues/4898 | open | entry (crash) | ty stack overflow + `def F[**P, R](c: Callable[P, R])` (or old-style) with `F(F)` | C1, C3 close; C4, C5, C6 stay | n/a |
| TY-4899 | https://github.com/astral-sh/ty/issues/4899 | open | entry (crash) | ty `(?:SIGABRT\|panic@.*\|timeout)` + class with `__init__(self: Callable[P,T])` and `__call__` with an extra named param, `U()` called. On the pinned tool the abort is seen as `ty:timeout` (E1/E2/E6/E10) and the plain-method case as the salsa panic (E8) | E1, E2, E6, E8, E10 close; E3, E4, E5, E7, E9 stay | n/a |
| TY-4900 | https://github.com/astral-sh/ty/issues/4900 | open | entry (crash) | ty stack overflow + `class C(Generic[X], N[N["C[C[X]]"]])`, N uses its parameter (PEP 695 N must mention it; old-style N not covariant), annotation `N[C[..]]` outside C | D1, D7, D10, D11 close; D4, D8, A1 stay; mypy's crash on the same program is MYPY-22360 | n/a |
| MYPY-22339 | https://github.com/python/mypy/issues/22339 | open | entry | only_ty `invalid-argument-type`/`invalid-assignment` on a generic named in ty's message whose PEP 695 class stores a non-Final, non-underscore `Callable[[..T..], R]` attribute | bug-03, probe CbInit, CbAnn; controls CbFinal, CbMethod, Plain, Producer; kb-selftest example | n/a |
| MYPY-22343 | https://github.com/python/mypy/issues/22343 | open | entry (crash) | mypy `SIGSEGV\|RecursionError@..` + `type X = M[..X..]` with `type M[T] = type[T]` (RHS of M a subscript) | mypy_A closes; mypy_B (`type Id[T] = T`, hangs, `mypy:timeout`) stays | n/a |
| MYPY-22344 | https://github.com/python/mypy/issues/22344 | open | entry (crash) | mypy segv + `T = TypeVar("T", default="T")` and `Generic[T]` class | mypy_E, mypy_25 close | n/a |
| MYPY-22360 | https://github.com/python/mypy/issues/22360 | open | entry (crash) | mypy segv + contravariant `Z`, `N(Generic[Z])`, `C(N[N["..C.."]])`, annotation using `N[..]` outside C | B1, B4, D1, D7, D9, D10, D11 close; B3, B5, B6, D4, D8 stay | n/a |
| MYPY-22361 | https://github.com/python/mypy/issues/22361 | open | entry (crash) | mypy segv + `__call__: C` / `Self` / union with either, and `C()()` or a `C`-typed name called | A1, A2, A4, A5, A6 close; A3, A8, A9, A10 stay; A7 (decorated `__get__`) also segfaults mypy but relation unproven, left live | n/a |
| PYRIGHT-11961 | https://github.com/microsoft/pyright/issues/11961 | open | entry (crash) | pyright `pyright:internal(:RangeError)?` + `__init__`/`__new__`/metaclass `__call__` declared `type["C"]` and `C()` called | pyright_init_attr, new_attr, call_metaclass close; A9 (unrelated pyright RangeError) stays | n/a |
| PYRIGHT-11960 | https://github.com/microsoft/pyright/issues/11960 | **closed completed** (task text said open; PR #11968), pinned 1.1.414 still hangs (no output after 60 s) | entry (crash) | pyright `pyright:timeout` + growing PEP 695 alias specialised in an annotation | e2e `pyright_11960_growing_alias` closes | n/a |
| MYPY-20969 (+`-REVEAL`) | https://github.com/python/mypy/issues/20969 | open | entry x2 | only_ty (5 diagnostic codes) / reveal_mismatch; constant-index subscript narrowed, assigned, then used in the statement. Covers list index, dict key, isinstance form | bug-01, probe list/dict/isinstance; controls: attribute, variable index, `del`, narrowed-not-assigned, other function; kb-selftest example | n/a |
| MYPY-21937 | https://github.com/python/mypy/issues/21937 | open (reopened) | entry | only_ty in the final `else` of an `x is F.A / elif x is F.B` chain (>= 2 tests) over a Flag/IntFlag subclass | bug-06, probe-bug06 `h`; controls: plain Enum, statement inside the chain, single test; kb-selftest example | n/a |
| TY-876 (+`-ASSERT`) | https://github.com/astral-sh/ty/issues/876 | open (umbrella, Flag item unchecked) | entry x2 | reveal_mismatch ``Revealed type: `Literal[`` / only_ty assert_type failure with `Literal[..]`; statement uses a bitwise combination of two Flag/IntFlag members (directly or via variable) | bug-02, probe operators (R\|W, R&W, R^R, IntFlag), assert witness; control: plain Enum; kb-selftest example (ASSERT) | n/a |
| MYPY-19889 | https://github.com/python/mypy/issues/19889 | open | prior_stance | only_mypy `attr-defined` "has no attribute" in a program with `InitVar[` | bug-04 gets the prior and is not in `matching_entries` | n/a |
| TY-3765 | https://github.com/astral-sh/ty/issues/3765 | closed duplicate (target ty#876 per maintainer comment) | prior_stance | reveal_mismatch/only_ty/concern_mismatch, statement with `& \| ^`, program with `IntFlag` | IntFlag program gets it; IntEnum does not; never in `matching_entries` | n/a |
| TY-4656 | https://github.com/astral-sh/ty/issues/4656 | closed not planned (re-verified) | existing prior, unchanged | not duplicated | `test_prior_ty4656_unchanged_and_not_duplicated` | n/a |
| pyright#11851 | https://github.com/microsoft/pyright/issues/11851 | open | not representable | pyright false negative; discrepancies only come from mypy-vs-ty differences, an entry would close an `only_mypy` finding and could hide a real ty false negative | none | n/a |
| pyright#11859 | https://github.com/microsoft/pyright/issues/11859 | open | not representable | same reason | none | n/a |

Totals: 20 new `entries` (11 crash + 9 discrepancy: TY-4884 x3, MYPY-22339, MYPY-20969 x2, MYPY-21937, TY-876 x2),
2 new `prior_stances` (MYPY-19889, TY-3765), 2 not representable (pyright#11851, #11859).

## Leads and behaviour notes

- **Unfiled ty lead:** ty overflows its stack on A1 (`class C: __call__: "C"` then `C()()`) and A4, which is not in
  ty#4882/#4898/#4900. No entry matches it (tested and confirmed e2e: stays `confirmed`).
- **Unfiled mypy hang:** `type Id[T] = T; type X = Id[X]` hangs mypy 2.4.0 (> 60 s, pipeline `mypy:timeout`), unlike #22343.
- A7 crashes mypy; relation to #22361 unproven, left live.
- **Changed classification of existing findings:** `probe-bug06 D3` (reveal of a Flag combination) was
  DESIGN_DIVERGENCE via `LITERAL-WIDENING` and is now DUPLICATE of ty#876; `bug-02-ty-flag-or-assert-type` D1 was
  DESIGN_DIVERGENCE via `INFERENCE-DOWNSTREAM` and is now DUPLICATE via `TY-876-ASSERT`. Both stay dismissed.
- mypy#21937 as filed shows the opposite direction (`==` early returns, mypy false positive `in` operator); not
  covered, the entry covers the unreachable-else direction only.
- `del xs[0]` stale narrowing (probe D4) is not covered by MYPY-20969 (the issue is about assignment).
- Priors only cap CONFIRMED/CANDIDATE findings; the bug-04 findings are already held at REVIEW by the gate, so the prior
  is verified by unit test (`find_priors`), not by the e2e run.
- Replay of Day-2 outputs: skipped. `runs/day2` is empty on this machine (no `runs/day2/out3`), so there is nothing to
  replay; this is not a failure of the script.

## Calibration regression (scripts/kbloop_calib_subset.py, all 194 positives + negatives + must_stay_live)

Baseline = commit 096a153 code (`git archive`, `PYTHONPATH`), new = branch head, same settings. 222 vs 227 rows (five
new rows are the new kb-selftest examples). Only one row changed outcome:
`ty-4882 kept -> dismissed` (crash C1 now closed by TY-4882, the exact issue this work records). No other known-real bug
changed. Outcome counts: base kept 121 / invisible 62 / dismissed 32 / excluded 5 / live 2; new kept 120 / invisible 62 /
dismissed 38 / excluded 5 / live 2 (38 = 32 + ty-4882 + 5 new example rows).

Commands: `scripts/kbloop_calib_subset.py <out> <all ids from calibration/positives.json> --negatives` for both code trees.

## Verification (verbatim)

### `.venv/bin/python -m pytest tests -q` (baseline 201 passed)

```
........................................................................ [ 20%]
........................................................................ [ 40%]
........................................................................ [ 61%]
........................................................................ [ 81%]
................................................................         [100%]
352 passed in 71.92s (0:01:11)
```

### `typediff --python-version 3.13 kb-selftest` (all PASS; 20 entries incl. 5 new examples, baseline 15)

```
PASS  KB:UPSTREAM-MYPY-948  findings=[('D1', 'kb:UPSTREAM-MYPY-948')]
PASS  KB:UPSTREAM-TY-4884  findings=[('D1', 'kb:UPSTREAM-TY-4884')]
PASS  KB:UPSTREAM-MYPY-22339  findings=[('D1', 'kb:UPSTREAM-MYPY-22339')]
PASS  KB:UPSTREAM-MYPY-20969  findings=[('D1', 'kb:UPSTREAM-MYPY-20969')]
PASS  KB:UPSTREAM-MYPY-21937  findings=[('D1', 'kb:UPSTREAM-MYPY-21937')]
PASS  KB:UPSTREAM-TY-876-ASSERT  findings=[('D1', 'kb:UPSTREAM-TY-876-ASSERT')]
PASS  KB:TY-REDECLARATION  findings=[('D1', 'kb:TY-REDECLARATION'), ('D2', 'rule:cascade-of:D1')]
PASS  KB:TY-CALLABLE-DUNDER  findings=[('D1', 'kb:TY-CALLABLE-DUNDER')]
PASS  KB:TY-STRICT-EQUALITY  findings=[('D1', 'kb:TY-STRICT-EQUALITY')]
PASS  KB:TY-SELF-UPPER-BOUND  findings=[('D1', 'kb:TY-SELF-UPPER-BOUND')]
PASS  KB:ANNOTATION-ONLY-READ  findings=[('D1', 'kb:ANNOTATION-ONLY-READ')]
PASS  KB:MYPY-15182-NEW-RETURNS  findings=[('D1', 'gate'), ('D2', 'gate'), ('D3', 'kb:MYPY-15182-NEW-RETURNS')]
PASS  KB:JOIN-VS-UNION-CALLABLE  findings=[('D1', 'kb:JOIN-VS-UNION-CALLABLE')]
PASS  KB:MDTEST-TODO  findings=[('D1', 'gate'), ('D2', 'kb:MDTEST-TODO')]
PASS  KB:PYRIGHT-REVEAL-EXPECTED-KWARG  findings=[('D1', 'kb:PYRIGHT-REVEAL-EXPECTED-KWARG')]
PASS  KB:MYPY-SUITE-ALLOW-EMPTY-BODIES  findings=[('D1', 'kb:MYPY-SUITE-ALLOW-EMPTY-BODIES')]
PASS  KB:MYPY-13807-ALIASED-CONDITIONS  findings=[('D1', 'kb:MYPY-13807-ALIASED-CONDITIONS')]
PASS  KB:REVEAL-ERROR-RECOVERY  findings=[('D1', 'kb:REVEAL-ERROR-RECOVERY')]
PASS  KB:ASSERT-TYPE-LITERAL-RETENTION  findings=[('D1', 'kb:ASSERT-TYPE-LITERAL-RETENTION')]
PASS  KB:MYPY-FIRST-ASSIGNMENT-TYPE  findings=[('D1', 'kb:MYPY-FIRST-ASSIGNMENT-TYPE')]
exit=0
```

### Each reproducer and control through the real pipeline (`TYPEDIFF_LLM=null`, one fresh `--out` per file; `scripts/upstream_day3_check.py`)

Crash rows: `closed_by` is the upstream id that dismissed the crash (`tier=confirmed` = stays live). Rows for E1/E2/E6/E10 show `ty:timeout` because the pinned ty aborts after memory blow-up and the runner records a timeout.

```
== ty_TB_protocol_stack_overflow
   crash:ty       tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:signal closed_by=TY-4882 sig=ty:signal-SIGABRT:stack-overflow
== t20a
   crash:ty       tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:signal closed_by=TY-4882 sig=ty:signal-SIGABRT:stack-overflow
== ty_20
   crash:ty       tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:signal closed_by=TY-4882 sig=ty:signal-SIGABRT:stack-overflow
== C1
   crash:ty       tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:signal closed_by=TY-4898 sig=ty:signal-SIGABRT:stack-overflow
== C3
   crash:ty       tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:signal closed_by=TY-4898 sig=ty:signal-SIGABRT:stack-overflow
== C4
   (no findings)
== C5
   (no findings)
== C6
   (no findings)
== E1
   crash:ty       tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:timeout closed_by=TY-4899 sig=ty:timeout
== E2
   crash:ty       tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:timeout closed_by=TY-4899 sig=ty:timeout
== E6
   crash:ty       tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:timeout closed_by=TY-4899 sig=ty:timeout
== E8
   crash:ty       tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:panic closed_by=TY-4899 sig=ty:panic@/root/.cargo/registry/src/index.crates.io-1949cf8c6b5b557f/salsa-0.28.5/src/function/execute.rs:751:9
== E10
   crash:ty       tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:timeout closed_by=TY-4899 sig=ty:timeout
== E3
   disc:D1        tier=review     dismissal=None decided_by=gate closed_by=None sig=None
   disc:D2        tier=review     dismissal=None decided_by=gate closed_by=None sig=None
== E4
   (no findings)
== E5
   disc:D1        tier=review     dismissal=None decided_by=gate closed_by=None sig=None
== E7
   (no findings)
== E9
   (no findings)
== D1
   crash:mypy     tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:signal closed_by=MYPY-22360 sig=mypy:signal-SIGSEGV
   crash:ty       tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:signal closed_by=TY-4900 sig=ty:signal-SIGABRT:stack-overflow
== D7
   crash:mypy     tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:signal closed_by=MYPY-22360 sig=mypy:signal-SIGSEGV
   crash:ty       tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:signal closed_by=TY-4900 sig=ty:signal-SIGABRT:stack-overflow
== D10
   crash:mypy     tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:signal closed_by=MYPY-22360 sig=mypy:signal-SIGSEGV
   crash:ty       tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:signal closed_by=TY-4900 sig=ty:signal-SIGABRT:stack-overflow
== D11
   crash:mypy     tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:signal closed_by=MYPY-22360 sig=mypy:signal-SIGSEGV
   crash:ty       tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:signal closed_by=TY-4900 sig=ty:signal-SIGABRT:stack-overflow
== D9
   crash:mypy     tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:signal closed_by=MYPY-22360 sig=mypy:signal-SIGSEGV
== B1
   crash:mypy     tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:signal closed_by=MYPY-22360 sig=mypy:signal-SIGSEGV
== B4
   crash:mypy     tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:signal closed_by=MYPY-22360 sig=mypy:signal-SIGSEGV
== B3
   (no findings)
== B5
   (no findings)
== B6
   (no findings)
== D4
   (no findings)
== D8
   (no findings)
== mypy_A_typealias_segfault
   crash:mypy     tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:signal closed_by=MYPY-22343 sig=mypy:signal-SIGSEGV
== mypy_E_typevar_default_self
   crash:mypy     tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:signal closed_by=MYPY-22344 sig=mypy:signal-SIGSEGV
== mypy_25
   crash:mypy     tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:signal closed_by=MYPY-22344 sig=mypy:signal-SIGSEGV
== A2
   crash:mypy     tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:signal closed_by=MYPY-22361 sig=mypy:signal-SIGSEGV
== A4
   crash:mypy     tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:signal closed_by=MYPY-22361 sig=mypy:signal-SIGSEGV
   crash:ty       tier=confirmed  dismissal=None decided_by=rule:crash:signal closed_by=None sig=ty:signal-SIGABRT:stack-overflow
== A5
   crash:mypy     tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:signal closed_by=MYPY-22361 sig=mypy:signal-SIGSEGV
== A6
   crash:mypy     tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:signal closed_by=MYPY-22361 sig=mypy:signal-SIGSEGV
== A1
   crash:mypy     tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:signal closed_by=MYPY-22361 sig=mypy:signal-SIGSEGV
   crash:ty       tier=confirmed  dismissal=None decided_by=rule:crash:signal closed_by=None sig=ty:signal-SIGABRT:stack-overflow
== A3
   (no findings)
== A8
   (no findings)
== A10
   (no findings)
== A7
   crash:mypy     tier=confirmed  dismissal=None decided_by=rule:crash:signal closed_by=None sig=mypy:signal-SIGSEGV
== A9
   crash:pyright  tier=confirmed  dismissal=None decided_by=rule:crash:internal_error closed_by=None sig=pyright:internal:RangeError
== ty_TA_depth24
   crash:ty       tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:timeout closed_by=TY-4883 sig=ty:timeout
== ty_TA_nested_tuple_compare
   (no findings)
== mypy_B_typealias_hang
   crash:mypy     tier=confirmed  dismissal=None decided_by=rule:crash:timeout closed_by=None sig=mypy:timeout
== pyright_11960_growing_alias
   crash:pyright  tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:timeout closed_by=PYRIGHT-11960 sig=pyright:timeout
   disc:D1        tier=review     dismissal=None decided_by=gate closed_by=None sig=None
== bug-01-narrowing-mypy-stale-index-narrowing
   disc:D1        tier=dismissed  dismissal=DUPLICATE decided_by=kb:UPSTREAM-MYPY-20969 closed_by=MYPY-20969 sig=None
   disc:D2        tier=dismissed  dismissal=DUPLICATE decided_by=kb:UPSTREAM-MYPY-20969-REVEAL closed_by=MYPY-20969-REVEAL sig=None
== bug-02-enums-ty-flag-or-literal-union
   disc:D1        tier=dismissed  dismissal=DUPLICATE decided_by=kb:UPSTREAM-TY-876 closed_by=TY-876 sig=None
== bug-02-ty-flag-or-assert-type
   disc:D1        tier=dismissed  dismissal=DUPLICATE decided_by=kb:UPSTREAM-TY-876-ASSERT closed_by=TY-876-ASSERT sig=None
== bug-03-generics-mypy-callable-attr-contravariant
   disc:D1        tier=dismissed  dismissal=DUPLICATE decided_by=kb:UPSTREAM-MYPY-22339 closed_by=MYPY-22339 sig=None
   disc:D2        tier=review     dismissal=None decided_by=gate closed_by=None sig=None
== bug-04-dataclasses-mypy-initvar-default-class-attr
   disc:D1        tier=review     dismissal=None decided_by=gate closed_by=None sig=None
   disc:D2        tier=review     dismissal=None decided_by=gate closed_by=None sig=None
   disc:D3        tier=dismissed  dismissal=NOISE decided_by=kb:REVEAL-ERROR-RECOVERY closed_by=None sig=None
== bug-05-typeddict-ty-generic-typeddict-typevar-unknown
   disc:D1        tier=dismissed  dismissal=DUPLICATE decided_by=kb:UPSTREAM-TY-4884 closed_by=TY-4884 sig=None
   disc:D2        tier=dismissed  dismissal=DUPLICATE decided_by=kb:UPSTREAM-TY-4884 closed_by=TY-4884 sig=None
   disc:D3        tier=dismissed  dismissal=DUPLICATE decided_by=kb:UPSTREAM-TY-4884-REVEAL closed_by=TY-4884-REVEAL sig=None
== bug-05-ty-generic-typeddict-crash-witness
   disc:D1        tier=dismissed  dismissal=DUPLICATE decided_by=kb:UPSTREAM-TY-4884 closed_by=TY-4884 sig=None
   disc:D2        tier=review     dismissal=None decided_by=gate closed_by=None sig=None
== bug-06-enums-mypy-flag-is-narrowing-else-unreachable
   disc:D1        tier=dismissed  dismissal=DUPLICATE decided_by=kb:UPSTREAM-MYPY-21937 closed_by=MYPY-21937 sig=None
== probe-bug01-index-variants
   disc:D1        tier=dismissed  dismissal=DUPLICATE decided_by=kb:UPSTREAM-MYPY-20969-REVEAL closed_by=MYPY-20969-REVEAL sig=None
   disc:D2        tier=dismissed  dismissal=DUPLICATE decided_by=kb:UPSTREAM-MYPY-20969-REVEAL closed_by=MYPY-20969-REVEAL sig=None
   disc:D3        tier=dismissed  dismissal=DUPLICATE decided_by=kb:UPSTREAM-MYPY-20969-REVEAL closed_by=MYPY-20969-REVEAL sig=None
   disc:D4        tier=review     dismissal=None decided_by=gate closed_by=None sig=None
== probe-bug02-flag-operators
   disc:D1        tier=dismissed  dismissal=DUPLICATE decided_by=kb:UPSTREAM-TY-876 closed_by=TY-876 sig=None
   disc:D2        tier=dismissed  dismissal=DUPLICATE decided_by=kb:UPSTREAM-TY-876 closed_by=TY-876 sig=None
   disc:D3        tier=dismissed  dismissal=DUPLICATE decided_by=kb:UPSTREAM-TY-876 closed_by=TY-876 sig=None
   disc:D4        tier=dismissed  dismissal=DUPLICATE decided_by=kb:UPSTREAM-TY-876 closed_by=TY-876 sig=None
   disc:D5        tier=review     dismissal=None decided_by=gate closed_by=None sig=None
   disc:D6        tier=review     dismissal=None decided_by=gate closed_by=None sig=None
== probe-bug03-variance-variants
   disc:D1        tier=dismissed  dismissal=DUPLICATE decided_by=kb:UPSTREAM-MYPY-22339 closed_by=MYPY-22339 sig=None
   disc:D2        tier=dismissed  dismissal=DUPLICATE decided_by=kb:UPSTREAM-MYPY-22339 closed_by=MYPY-22339 sig=None
== probe-bug05-typeddict-variants
   disc:D1        tier=dismissed  dismissal=DUPLICATE decided_by=kb:UPSTREAM-TY-4884-ASSERT closed_by=TY-4884-ASSERT sig=None
   disc:D2        tier=dismissed  dismissal=DUPLICATE decided_by=kb:UPSTREAM-TY-4884-ASSERT closed_by=TY-4884-ASSERT sig=None
== probe-bug06-flag-param-and-local
   disc:D1        tier=dismissed  dismissal=DUPLICATE decided_by=kb:UPSTREAM-MYPY-21937 closed_by=MYPY-21937 sig=None
   disc:D2        tier=review     dismissal=None decided_by=gate closed_by=None sig=None
   disc:D3        tier=dismissed  dismissal=DUPLICATE decided_by=kb:UPSTREAM-TY-876 closed_by=TY-876 sig=None
   disc:D4        tier=dismissed  dismissal=DESIGN_DIVERGENCE decided_by=kb:MYPY-SKIPS-UNREACHABLE closed_by=None sig=None
== probe-bug02-bug05-runtime-and-assignability
   (no findings)
== pyright_init_attr
   crash:pyright  tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:internal_error closed_by=PYRIGHT-11961 sig=pyright:internal:RangeError
== pyright_new_attr
   crash:pyright  tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:internal_error closed_by=PYRIGHT-11961 sig=pyright:internal:RangeError
   disc:D1        tier=review     dismissal=None decided_by=gate closed_by=None sig=None
== pyright_call_metaclass
   crash:pyright  tier=dismissed  dismissal=DUPLICATE decided_by=rule:crash:internal_error closed_by=PYRIGHT-11961 sig=pyright:internal:RangeError

violations: 0
exit=0
```

### Calibration comparison (baseline vs branch)

```
rows 222 227
changed rows: 6
ty-4882 BASE kept [['C1', 'confirmed', 'rule:crash:signal', 'CRASH']] NEW dismissed [['C1', 'dismissed', 'rule:crash:signal', 'CRASH']]
kb-UPSTREAM-TY-4884 BASE None None NEW dismissed [['D1', 'dismissed', 'kb:UPSTREAM-TY-4884', 'DUPLICATE']]
kb-UPSTREAM-MYPY-22339 BASE None None NEW dismissed [['D1', 'dismissed', 'kb:UPSTREAM-MYPY-22339', 'DUPLICATE']]
kb-UPSTREAM-MYPY-20969 BASE None None NEW dismissed [['D1', 'dismissed', 'kb:UPSTREAM-MYPY-20969', 'DUPLICATE']]
kb-UPSTREAM-MYPY-21937 BASE None None NEW dismissed [['D1', 'dismissed', 'kb:UPSTREAM-MYPY-21937', 'DUPLICATE']]
kb-UPSTREAM-TY-876-ASSERT BASE None None NEW dismissed [['D1', 'dismissed', 'kb:UPSTREAM-TY-876-ASSERT', 'DUPLICATE']]
base outcomes Counter({'kept': 121, 'invisible': 62, 'dismissed': 32, 'excluded': 5, 'live': 2})
new outcomes Counter({'kept': 120, 'invisible': 62, 'dismissed': 38, 'excluded': 5, 'live': 2})
new dismissed: ['kb-ASSERT-TYPE-LITERAL-RETENTION', 'kb-MYPY-13807-ALIASED-CONDITIONS', 'kb-MYPY-FIRST-ASSIGNMENT-TYPE', 'kb-MYPY-SUITE-ALLOW-EMPTY-BODIES', 'kb-PYRIGHT-REVEAL-EXPECTED-KWARG', 'kb-REVEAL-ERROR-RECOVERY', 'kb-TY-CALLABLE-DUNDER', 'kb-TY-REDECLARATION', 'kb-TY-SELF-UPPER-BOUND', 'kb-TY-STRICT-EQUALITY', 'kb-UPSTREAM-MYPY-20969', 'kb-UPSTREAM-MYPY-21937', 'kb-UPSTREAM-MYPY-22339', 'kb-UPSTREAM-MYPY-948', 'kb-UPSTREAM-TY-4884', 'kb-UPSTREAM-TY-876-ASSERT', 'mypy-4554', 'mypy-5289', 'mypy-6079', 'mypy-7984', 'neg-assert_type_literal_retention', 'neg-assignment_narrowing', 'neg-join_vs_union', 'neg-literal_widening', 'neg-mypy_aliased_condition', 'neg-mypy_first_assignment', 'neg-reveal_error_recovery', 'neg-suppression_codes', 'neg-unknown_attribute', 'neg-unreachable_reveal', 'ty-1090', 'ty-1172', 'ty-4713', 'ty-4786', 'ty-4817', 'ty-4835', 'ty-4872', 'ty-4882']
```
