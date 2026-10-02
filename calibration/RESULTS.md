# Calibration results

These results answer one question: does the deterministic stage ever dismiss a real bug? The LLM
was off (`TYPEDIFF_LLM=null`), so every case the rules could not close went to review.

Setup: ty 0.0.84, mypy 2.4.0, CPython 3.12.13, `--python-version 3.12`, 30 s timeout per
checker, pyright off. Run on 2026-10-02 with:

```bash
typediff --no-pyright calibrate --fetch --timeout 30
```

## Data

- **Positives (156):** open bug reports with a standard-library-only repro.
  - 80 from `astral-sh/ty` (label `bug`).
  - 76 from `python/mypy` (labels `bug` + `false-positive`, or `crash`).
- **Negatives (10):** documented mypy/ty differences: `calibration/negatives/*.py` plus the
  examples bundled with the KB entries.
- `results/calibration_rows.jsonl` has one row per case: issue URL, labels, outcome and findings.
  It does not include the repro source; `calibrate --fetch` downloads that again.

## Outcomes

| | kept | invisible | dismissed | excluded |
|---|---|---|---|---|
| ty bug reports (80) | 58 | 17 | **0** | 5 |
| mypy bug reports (76) | 38 | 34 | **4** | 0 |

- **kept**: at least one finding is confirmed, candidate or review. 14 of these were crashes
  confirmed automatically: 6 ty panics, 4 ty hangs, 1 mypy hang and 3 mypy internal errors.
- **invisible**: mypy and ty agree on this input, so differential testing cannot see the bug.
  This is mostly mypy crash reports that no longer crash on 2.4, or need flags or plugins.
- **excluded**: the repro imports `ty_extensions` (ty-only test helpers), so there is nothing to
  compare against mypy.
- **Recall on visible cases**: 96 / 100.
- **Negatives**: 9 of 10 were closed automatically, each with a KB citation. The tenth produced
  no discrepancy at all.

### The 4 dismissed mypy reports

| issue | dismissed by | assessment |
|---|---|---|
| mypy#7984 | LITERAL-WIDENING | The reported bug no longer reproduces: mypy 2.4 reveals `str`, as the issue says it should. What remains is ty's `Literal["x"]`, a documented difference. |
| mypy#5289 | TY-CHECK-NOT-IMPLEMENTED | The reported assignment error no longer reproduces. What remains is mypy's documented `[var-annotated]`. |
| mypy#4554 | TY-CHECK-NOT-IMPLEMENTED | Same as #5289: the original error is gone, only `[var-annotated]` remains. |
| mypy#6079 | JOIN-VS-UNION | Still reproduces (`dict[object, int]`). This is deliberate policy: mypy tracks join-vs-union as an issue class (`topic-join-v-union`), so a pure reveal difference is logged as KNOWN_LIMITATION and not filed again. A false positive that the join causes is still adjudicated. |

So among bugs that still reproduce, nothing was wrongly dismissed; #6079 is the only one closed,
and that is the policy above.

## False-dismissal bugs found by this calibration and the earlier smoke runs, now fixed

| bug in typediff | swallowed | fix |
|---|---|---|
| TY-REDECLARATION also matched redefined `def`s and classes | mypy#6158 (property-subclass setter, a mypy false positive) | Only matches re-*annotating* a name that already has a declaration in the same scope |
| BOTH-GRADUAL dismissed explicit `Any` vs ty `Unknown` | ty#4536 (explicit `Any` lost to `Unknown`) | Ignored when the source spells `Any` and ty answers `Unknown`; also requires *every* differing position to be gradual on both sides |
| BOTH-GRADUAL matched any type containing `Any` anywhere | ty#2871 (`Coroutine[Any, ...]` vs `CoroutineType[Any, ...]`) | Structural `gradual_diff()`; `CoroutineType` is recognised as a refinement of `Coroutine` |
| JOIN-VS-UNION matched a type variable as the "join" | ty#4296 (`A[T]` vs `A[T \| Unknown]`, a real ty inference bug) | The join side must be `object` or a concrete class, and the union must contain no gradual member |
| TY-CHECK-NOT-IMPLEMENTED cleared mypy as well as ty | mypy#6140 (an overload-overlap false positive) | Auto-dismisses only codes whose mypy side is documented design (`var-annotated`, …); other codes get the hint TY-CHECK-MISSING-JUDGE-MYPY |
| The "missing ty check" table also listed `attr-defined` | InitVar case (`a.scale`) | Codes that also appear in a row with a ty rule are only partially missing and never auto-dismiss |
| Incomplete repros, e.g. missing imports | mypy#6140 | New rule `rule:undefined-name`: a statement that depends on a name *both* checkers call undefined is INVALID_TEST |

## Remaining dismissals inside kept cases (checked by hand, all correct)

- **ty#4593, ty#1163:** TY-REDECLARATION on mypy's `no-redef` for repeated annotations. The ty bug
  each issue reports is still kept.
- **ty#2057:**
  - `[var-annotated]` dismissed by TY-CHECK-NOT-IMPLEMENTED.
  - mypy `Any` vs ty `Unknown` in a program with no explicit `Any`, dismissed by BOTH-GRADUAL.
- **mypy#6224, mypy#6140:** repros missing their imports and classes, dismissed by
  `rule:undefined-name`.

## Not measured yet

- **Precision of CONFIRMED verdicts:** this needs a real LLM judge. Without one, everything except
  crashes stays in review.
- **Review volume:** 168 of 198 findings on positives went to review. That queue is what the LLM
  judge and the experiments are meant to shrink.
