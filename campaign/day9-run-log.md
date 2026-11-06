# Day 9 run log

Branch `campaign/day9-p2` (from `campaign/day8-p2`), local only. Nothing was pushed; no issue, PR or comment was written on GitHub (no `gh` call was needed in this phase). Pins unchanged: mypy 2.4.0, ty 0.0.97, pyright 1.1.414, CPython 3.13.16. `-l`, `.kiro/` and `findings/2026-10-27-llm-run/` untouched. `campaign/day7-report.md` and `campaign/day8/phase6/results/commit.out` carry uncommitted edits that are not mine; they are not committed here.

Each action names the FUZZING_PLAN.md step it follows. The plan has no Day-9 pipeline step of its own (its Day 8 to 13 line is P5 judging and filing), so, as on Days 5 to 8, pipeline work follows "Every morning" (retire patterns you have classified), §3 P1 ("harness noise (fix the rule)"), §6 checklist item 8 ("record it") and the P2/P3 daily loop (generate with mutation operators, judge deterministically).

The priorities were set from `campaign/day8-report.md` section 7 ("Weaknesses"). Day 9 had to fix at least one listed weakness with a test, and to add a mutation operator or a feature area.

## Phase 1: pipeline improvements

### Day-8 weaknesses fixed

| # | Day-8 weakness (report §7) | Plan step | Fix | Tests |
|---|---|---|---|---|
| W1 | `mentions_self` does not read a quoted `'Self'` annotation: 2 live `only_mypy` findings of `self_param_inherited__mut0_3a63c673` (a ty#4656 duplicate) | §3 P1 "design difference ... harness noise (fix the rule)"; §6 item 5 duplicate check | `typediff/selfparam.py`: `mentions_self` reads the expression inside a string annotation (`'Self'`, `'list[Self]'`), skips `Literal[...]` and the metadata of `Annotated[...]`. `typediff/experiments.py`: the spec-desugar probe (which the entry needs before it dismisses) rewrites `Self` inside the string and keeps it a string; a string that is no expression still raises `ExperimentError` (inconclusive). Side effect in the safe direction: `has_self_typed_state` now sees `nxt: 'Self \| None'`, so the "ty is genuinely unsound" demotion also fires for quoted state | `tests/test_day9_pipeline.py` (W1 block: 10 positives, 10 controls, state, plan, desugar rewrite, Literal kept, non-expression refused, one real-tools end-to-end test that the quoted KB example is dismissed by `kb:TY-SELF-UPPER-BOUND` like the plain one) |
| W2 | `TY-2792-READONLY` requires the assignment in the scope of the stale narrowing (D8-2: 2 programs, 3 strong findings) | §6 item 8 "record it"; entry text updated in `known_upstream.json` | `typediff/kb.py`: the chain test moved into `_stale_chain_before`; `_readonly_prop_after_stale_narrowing` also looks at each enclosing scope with the position set half a line above the `def` of the function that holds the statement. ty treats the code after the contradiction as unreachable, a `def` included, so the chain only has to precede the `def`, through any receiver name of that scope | `tests/test_day9_pipeline.py` (W2 block: 6 positives incl. decorated function, two function levels, chain inside the outer function; 10 controls: function before the chain, chain in a sibling function, no call, call before narrowing, no read after the call, setter property, receiver rebound, direct store, not a property, chain in another class's method; 2 message/kind controls) |

Effect on the saved Day-8 reports (`results/replay-day8.out`, `results/replay-day8-diff.txt`; `kbloop_replay.py runs/day8/out ... --pyright-only --rerun-runtime --verify-sample 30`, **30/30 identical to a full re-run**): 224 findings compared, **3 changed**, all `review/gate` to dismissed: `seed-9193b5cc679d` D1 and D2 (`3a63c673`, `kb:TY-SELF-UPPER-BOUND`) and `seed-78dcbe5d81b6` D1 (`d4p_descriptors_readonly_prop_never__mut1_17c399aa`, `kb:UPSTREAM-TY-2792-READONLY`). Live 155 to **152**. No other finding changed.

Not fixed in the same family, on purpose:

* `d4p_descriptors_readonly_prop_never__mut0_f116e46b` (D1, D2) keeps its findings live: its mutation is a `t.__dict__['doubled'] = 99` write, not a method call or a descriptor store. Treating a `__dict__` write like a mutating call would also close the retained parent `d4p_descriptors_readonly_prop_never` itself; that widens what the entry means and is a decision for the morning review, not for a code fix.
* The `reveal_type(c.readonly)` rows (`Never` in ty, `int` in mypy, D2 of both D8-2 programs) are not covered by `TY-2792`; the entry matches a reveal of the narrowed attribute itself.
* The two other §7 matcher/entry weaknesses (queued KB entries `TY-NONFINAL-PATTERN`, `ASSERT-NEVER-ALL-REJECT`, widened `JOIN-VS-UNION`) decide what the review queue shows; they are not changed without a decision.

### New mutation operators and feature areas (Day 9 priority: new, not exhausted families)

* `typediff/operators.py` (new): operators that carry their own instruction. `generate --ops` now builds `mutation_spec(op)`; the 21 older operators still produce `{"operator": op}`, so their prompts (and file-bridge keys) are byte-identical (test `test_generate_prompt_of_an_old_operator_is_unchanged`).
  * `dunder_instance_shadow`: a special method that exists only as an annotation or only on the instance. CPython looks dunders up on the type, so the use raises `TypeError`; this is the runtime oracle and generalises the Day-8 lead (annotation-only `__call__: Callable[[], int]`, ty and pyright accept `C()()`, confidence 0.4, `day8-report.md` §5).
  * `exit_swallow_flip`: `__exit__` annotated `bool` / `None` / `Literal[True]` / `Literal[False]` around a `with` that raises, with narrowing or `reveal_type` after the block; CPython shows whether the block swallowed the exception.
* `typediff/strategy.py`: two feature areas without any parent or hit so far, `dunder_dispatch` and `context_managers` (22 to 24 areas). `prompts.py` strategist operator list and `DESIGN.md` §6 updated.
* Tests: `test_new_operators_have_instructions_and_old_ones_stay_bare`, `test_new_operator_instructions_name_the_runtime_oracle`, `test_new_areas_are_registered_with_descriptions`, `test_generate_puts_the_instruction_of_a_new_operator_into_the_prompt`, `test_generate_without_area_covers_the_new_areas` (file bridge round trip: 2 prompts, answers, 2 programs written).

No generation was run in this phase; the operators and areas are for the generation step of Day 9.

### Checks (counts read from the files in `campaign/day9/phase1/results/`)

* Baseline before any edit: `pytest tests -q` 604 passed (`pytest-baseline.out`); `kb-selftest` 20 PASS, 0 FAIL (`kb-selftest-baseline.out`).
* Final: `.venv/bin/python -m pytest tests -q` **655 passed** in 84.10 s (604 + 51 new in `tests/test_day9_pipeline.py`), rc 0 (`pytest.out`); `.venv/bin/typediff --python-version 3.13 kb-selftest` **20 PASS, 0 FAIL**, rc 0 (`kb-selftest.out`, `kb-pass-count.out`); `campaign/day4m/check_hits.py 0.80` **40 files; 0 with problems**, no near-duplicate pair (`check_hits.out`).
* Probe of the three Day-8 programs: `probe-before-w2.out` (after W1, before W2) and `probe-after-w2.out`. Scripts in `campaign/day9/phase1/scripts/`.
* Reviewer iteration file `.agents/tasks/day9-pipeline-review.json` did not exist; the work was done from scratch.

Log line: Day 9 phase 1: 0 programs generated, 3 Day-8 findings newly auto-closed (live 155 to 152 on replay), 0 new candidates, 0 issues filed.
