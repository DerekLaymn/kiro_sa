# Stage 3 round 2: constant-fold fix, error-recovery and aliased-condition entries, normaliser refinements

Round 2 closes the confirmed round-1 holes. The `Literal[True]/[False]` fold hole in ASSERT-TYPE-LITERAL-RETENTION is fixed with a matcher exclusion and a pyright-agreement requirement, and the same bool-literal hole in INFERENCE-DOWNSTREAM is closed. ANNOTATION-ONLY-READ is re-labelled as a tracked mypy limitation (python/mypy#15416, #17373, #4019). Two new auto-dismissal entries were added (REVEAL-ERROR-RECOVERY, MYPY-13807-ALIASED-CONDITIONS), and the normaliser now treats intersections, `LiteralString`, `type[X]` and `Never` as refinements. Sampling found no real bug hidden by any new or changed rule. The review queue shrank only 6.25% overall (7841 to 7351), 6.71% on tuning (6300 to 5877) and 4.35% on hold-out (1541 to 1474), far short of the more-than-50% target.

Watch for: the Plan target is not met (confirmed, blocking, 6.71% / 4.35% against more than 50%). MYPY-13807-ALIASED-CONDITIONS does not check that the aliased expression is left unmodified between the alias and the `if` (confirmed, minor). The NameError policy decision is still open and gates about 129 `unresolved-reference` rows plus about 67 error-recovery reveals (confirmed, product decision).

**Verdict**: NEEDS_CHANGES

## High-level view

The round-1 blocking issue is fixed. The `Literal[True]/[False]` exclusion in ASSERT-TYPE-LITERAL-RETENTION and INFERENCE-DOWNSTREAM re-opened 76 findings, and the ty-folds-`<`-on-a-tuple-subclass program is kept live by a pytest that runs the real pipeline. The coder stored that program in `calibration/must_stay_live/` instead of `calibration/negatives/`, because the negatives metric counts a kept negative as a miss. I accept the deviation.

REVEAL-ERROR-RECOVERY is the largest new dismissal (151 findings, 113 tuning and 38 hold-out). It drops a reveal row only when the revealing tool also reports an error inside the revealed argument, and never when CPython raised on that statement. In all 41 rows I sampled, the separate error finding stays live or is dismissed by ANNOTATION-ONLY-READ (the ty-correct case). It fires across mypy-suite and ty-mdtest programs alike, which is why hold-out shrank more than tuning this round.

MYPY-13807-ALIASED-CONDITIONS (38 findings) is a single-family rule (ty `narrow/aliased_conditions`) and has one gap: it does not require that the narrowed expression is unmodified between the alias assignment and the `if`.

The normaliser change relabels about 108 rows from "different" to a precision relation and adds only 3 dismissals plus 4 disappearing findings, so it improves measurement without shrinking the queue. What remains is dominated by reveal classes (gradual 510, uncomparable 444, different 403, ty_more_precise 297) where 94% to 98% of rows carry an origin expectation comment. No independent oracle exists for them, so the round stops short of the target rather than inventing dismissals (Plan §7).

<details>
<summary>Issues (6)</summary>

1. **Plan target not met (blocking, confirmed)** — queue shrank 6.25% overall, 6.71% tuning (6300 to 5877), 4.35% hold-out (1541 to 1474) against the required more-than-50% on both. Continue next round; do not invent dismissals (Plan §7).
2. **NameError policy undecided (blocking progress, confirmed)** — `kb.runtime_contradiction` treats NameError as strong evidence while `rules.attach_runtime_evidence` treats it as neutral. This gates 129 `only_ty [unresolved-reference]` rows (50 with CPython NameError) and about 67 error-recovery reveals. Get the user's decision, then either add a mypy-limitation entry for possibly-unbound/class-body names or leave them live.
3. **Stale-alias gap in MYPY-13807-ALIASED-CONDITIONS (confirmed, minor)** — `m_aliased_condition` checks that the alias is bound once before the `if` and contains the revealed expression, but not that the expression is unchanged in between. Reproduced with `is_none = a.x is None; a.clear(); if not is_none: reveal_type(a.x)`: ty says `int`, mypy `int | None`, and the finding is dismissed. Require no store to the aliased target (and no call on its root for attribute targets) between alias and `if`, and add a negative test.
4. **Negatives for the two new entries are not closed by `calibrate --no-pyright` (confirmed, non-blocking)** — `kb-REVEAL-ERROR-RECOVERY` and `neg-reveal_error_recovery` stay open there because the ty unresolved-reference in those programs needs pyright agreement for ANNOTATION-ONLY-READ. The closed-negatives metric fell to 19 of 26. Make the calibration negatives not depend on a second entry, or run the negatives with pyright on.
5. **must_stay_live is enforced only by pytest (possible)** — `calibration/must_stay_live/` is not read by `typediff calibrate`, so a regression would show only in pytest. Optional: have `calibrate` report must-stay-live programs that get dismissed.
6. **Biggest remaining tuning patterns for the next round** — reveal gradual 510 (260 ty Unknown without any error and 276 mypy Any without any error need a per-construct reason), reveal uncomparable 444 and different 403 (the ORIGIN-MISMATCH hint could be extended), ty_more_precise 297, only_mypy [assignment] 197 (pyright agrees in 52 or more rows), only_mypy [assert-type] 197 (about 52 plus 65 pyright-origin rows; the installed pyright fails the same assertion), only_ty [type-assertion-failure] 157 (62 bool-literal rows deliberately re-opened), only_ty [unresolved-reference] 129, only_mypy [arg-type] 118, concern_mismatch [assignment] 114, only_ty [invalid-assignment] 94.

</details>

<details>
<summary>Details</summary>

### Audit of REVEAL-ERROR-RECOVERY dismissals

I sampled 25 random tuning dismissals (seed 3) and 16 random hold-out dismissals (seed 8) out of 113 and 38. `kbloop_sample.py` skips dismissed findings, so I used a throwaway script outside the repo that also prints every other discrepancy on the same statement with its tier.

The ty-side rows (ty `Unknown`, mypy a concrete type) are mostly mypy-suite programs whose variable is declared annotation-only (`x: Final[int, str]`, `a: C[D]`, `cs: C[str]`) and then read. ty reports `unresolved-reference`, pyright reports "unbound", and CPython raises NameError. The sibling `only_ty [unresolved-reference]` finding is dismissed by ANNOTATION-ONLY-READ in all of those. The any-exception guard held: `campaign/s3-r2-raised.txt` is empty.

The mypy-side rows (mypy `Any`, ty concrete) each have a live `only_mypy` error finding on the same statement: `attr-defined` on `Person.metadata` (InitVar), `misc` on `super(Meta, cls)`, `index` on `type[A] | type[B]`, `has-type` on `state`/`c`/`y`, `operator` on `<=` in `total_ordering`. Three programs showed no sibling in my first print (`ty__type_qualifiers__initvar__5`, `ty__class__super__14`, `ty__subscript__class__3`); the report JSON shows their error discrepancies at `review/gate`.

Two ty-side observations for later rounds. In `ty__comparison__tuples__8` and `__3`, ty reveals `Unknown` for a tuple comparison where mypy and pyright answer `bool` (ty reports `unsupported-operator` on a tuple with an incomparable element). In `ty__class__super__5`, pyright agrees with mypy that `super(Meta, cls)` is invalid while ty is silent. In both, the error finding stays live, so any ty bug remains visible.

The matcher accepts any ERROR inside the revealed argument, so an unrelated error in a sub-expression could sit next to a gradual type with a different cause. None of the 41 sampled rows is like that. The live sibling error finding is the only mitigation.

### Audit of MYPY-13807-ALIASED-CONDITIONS dismissals

I sampled 20 of the 32 tuning dismissals. All are ty `narrow/aliased_conditions` programs of the form `alias = <condition on x>; if alias / else: reveal_type(x)`; ty narrows, mypy returns the declared union, and every program ran with `runtime=success`. In three of them (`__10`, `__11`, `__29`, targets `a.x` and `l[0]`) pyright agrees with mypy and ty alone narrows, so the rule dismisses the difference against pyright as well.

I probed the stale-alias hole with `/tmp/rev_alias_prog.py`. For `is_none = a.x is None; a.clear(); if not is_none: reveal_type(a.x)`, the pipeline dismisses the row as MYPY-13807 although `a.x` may have changed between alias and `if`. The risk is low because member-access narrowing across calls has the same unsoundness in all three tools in the inline form. Rebinding the target itself (`x = None` after the alias) produces no discrepancy.

### Audit of ASSERT-TYPE-LITERAL-RETENTION after the fix

The entry now holds 64 dismissals, all in the tuning set; hold-out has none (it had 4 before the fix). I sampled 24 of 64. Every row is a one-sided Literal widening: `Literal[1]` vs `int`, `Literal["abc"]` vs `str`, `tuple[Literal[0]]` vs `tuple[int]`, `slice[Literal[1234], Any, Any]` vs `slice[int, Any, Any]`, and nested forms. Where mypy is the failing tool, pyright reports the identical `expected/received` pair. Several rows sit in conformance files marked `# E?` or "either is acceptable". None contains a bool literal, and no CPython exception sits on the statement (`pyright__sentinel1` raised at an earlier line, 13).

### Audit of normaliser changes and PRECISION-RUNTIME-CONSISTENT

The refinement rules add three dismissals through PRECISION-RUNTIME-CONSISTENT (`campaign/s3-r2-trans.txt`): `(int & ~AlwaysFalsy) | None` vs `int | str | None` (the variable was assigned `None`, so ty is right and pyright agrees) and two `type` vs `type[object]` rows. I also sampled 40 of the 66 rows of the entry; the runtime probe holds and pyright agrees with ty in nearly all of them. Four `int | Never` findings disappear because the types are now equal.

### Evidence, tests and hygiene

I did not re-run anything. Recorded results: pytest 176 passed, 0 failed (`campaign/s3-r2-pytest.txt`); `kb-selftest` 15 of 15 PASS (`s3-r2-kb-selftest-final.txt`); calibration shows the same 11 dismissed positives as Stage 2 and round 1, none new (`s3-r2-calib-compare.txt`). Each code change has a test in `tests/test_stage3_round2.py`, including the fold program through the real pipeline, the INFERENCE-DOWNSTREAM bool-literal case, pyright agree/disagree/silent, both REVEAL-ERROR-RECOVERY sides with the any-exception guard, MYPY-13807 positives and negatives, and the normaliser relations with the `list[LiteralString]` invariance check.

The diff from d479c03 to HEAD touches no `runs/`, `seeds/harvested`, `findings/2026-10-27-llm-run/` or `-l` path, and `git ls-files` lists none of them. There is no `origin/campaign/day2-p1` and no push in the reflog. The log's `[Plan §...]` labels match the work: the matcher and pyright fix, the ANNOTATION-ONLY-READ record, REVEAL-ERROR-RECOVERY plus the normaliser, MYPY-13807, and no-decision entries for patterns 4, 5, 7 and 10. The two off-plan notes (the `must_stay_live` directory, and a KB entry instead of `known_upstream.json`) each state a reason. The coder did not link python/mypy#948 as the round-1 review suggested and cited four more fitting trackers instead; their search output is in `campaign/s3-r2-gh1.txt`.

### Target and overfitting gap

The queue is 7351 overall, 5877 tuning and 1474 hold-out, so the shrink against Stage 2 is 6.25%, 6.71% and 4.35% (5877 + 1474 = 7351, matching `runs/day2/out2-stats.txt`). The target needs at most 3920, 3149 and 770, so about 3400 more tuning findings and 700 more hold-out findings must go. The cumulative gap is 2.4 points (down from 3.4 after round 1), and this round alone hold-out shrank more (2.38% vs 1.39%). ASSERT-TYPE-LITERAL-RETENTION and MYPY-13807 still sit almost entirely in the tuning set. Only the reveal classes and the NameError rows are large enough to reach the target: the first needs a per-construct oracle, the second a policy decision.

</details>

<details>
<summary>File map</summary>

- `typediff/kb.py`: bool-literal exclusion in INFERENCE-DOWNSTREAM and ASSERT-TYPE-LITERAL-RETENTION, pyright-agreement check, ANNOTATION-ONLY-READ re-labelled, new REVEAL-ERROR-RECOVERY and MYPY-13807-ALIASED-CONDITIONS entries
- `typediff/typenorm.py`: `has_bool_literal`, refinement rules for `Never`, `LiteralString`, `type[X]` and intersections
- `tests/test_stage3_round2.py`: tests for all of the above; `tests/test_stage3_round1.py`: one assertion updated
- `calibration/must_stay_live/ty_constant_fold_tuple_subclass.py`, `calibration/negatives/{mypy_aliased_condition,reveal_error_recovery}.py`: calibration programs
- `campaign/day2-run-log.md`, `campaign/s3-r2-*`, `campaign/tmp/r2*`: log and round-2 outputs

Full diff: `git -C /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa diff d479c03 HEAD`

</details>
