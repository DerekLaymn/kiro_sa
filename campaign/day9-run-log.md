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

## Phase 2: morning decisions and generation plan (no generation)
Branch `campaign/day9-p2`, local only; nothing pushed, no GitHub write, no `gh` call. Pins unchanged (ty 0.0.97 confirmed by `ty --version`). Plan steps: §3 "Every morning" (promote programs with new patterns into `runs/hits/`; retire classified patterns; keep a log line per day) and the P2/P3 daily loop step 1 (generate: mutate hits, fresh briefs). The Day 9 and Day 10 requirement is to prefer new areas and new mutation operators over exhausted families. Plan and evidence: `campaign/day9-morning.md`, `campaign/day9/phase2/` (`results/`, `scripts/`, `repro/`).
1. [§3 "Every morning", crash probe] `phase2/scripts/probe_crash_parents.sh` probed all 59 ty targets in `runs/hits` (40) and `runs/hits-dropped` (19), the mypy crash parent and the two pyright parents (`results/crash-parents-probe.tsv`, `probe-counts.out`): ty rc 134 on 11 files, rc 101 on 1, rc 1 on 21, rc 0 on 26. 5 of the rc-134 files are the draft-1 family (no KB entry, not mutated); the others are closed by `TY-4148`, `TY-4882`, `TY-4898`, `TY-4900`. `d3p_generics_contravariant_recursive_generic_base` (TY-4900) was not in the Day-8 probe list and still crashes. mypy rc 137 and pyright rc 2 (two parents) as on Day 8.
2. [§3 "Every morning", promote] Promoted 1 program to `runs/hits`: `d8p_dunder_dispatch_annotation_only_call` (Day-8 mutant `d3p_callables_self_call_attr__mut0_5445453a`, parent of the new area `dunder_dispatch`; `phase2/scripts/promote.sh`). `runs/hits` 40 to 41; `check_hits.py 0.80` 40 files / 0 problems before, 41 files / 0 problems after.
3. [§3 "Every morning", retire] Stopped mutating the Day-8 escape-watch parents (`A_ty_escape`: 8 programs, 7 closed crash events, 0 escapes); no file moved. Cut `C_pyright_range` from 12 to 6 programs (all Day-8 rows rediscoveries of draft 7). Decision D-1: `TY-2792-READONLY` is not widened to `__dict__` writes. Decision D-2: the three queued KB entries stay unimplemented; the plan sends 0 fresh programs to match_statement, tuples_unpacking, recursive_aliases, dataclasses.
4. [§3 daily loop, reserve] Two Day-8 live items checked on the pins (`phase2/repro/`): ty rejects `fn.__name__` on `Callable` and on a TypeVar bound to it (ty FAQ, mypy and pyright accept): NOT-A-BUG, design. `Config('svc')` on `@dataclass(kw_only=True)`: all three tools reject, mypy adds a third consequence message: noise. Both left out of the reserve. 6 reserve parents chosen (`scripts/mk_groups.sh`, `results/reserve-check.out`: 0 flagged at 0.80).
5. [P2/P3 daily loop step 1] Adapted the Day-8 scripts into `campaign/day9/` (`mk_groups.sh`, `gen_pass.sh`, `gen_worker.sh`, `answer_pending.sh`, `judge.sh`, `gen-pass-dryrun.sh`, `check_reserve.py`, `only_pyright_relations.py`) with `runs/day9` paths, generator `kiro-cli --agent-engine v3 --model claude-haiku-5.5 --effort medium` via `--llm file:/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/runs/day9/inbox`. `bash -n` on every shell script and `py_compile` on the two Python helpers: 20 ok, 0 bad (`results/syntax.out`).
6. [P2/P3 daily loop step 1, dry run] `campaign/day9/gen-pass-dryrun.sh` (scratch inbox `/tmp/d9-dryrun`, no answers): **`pending=250 written=0`**, `inbox_check.py`: `prompts=250 (retry prompts=0) answers=0 answered=0 pending=250 orphan_answers=0 malformed_keys=0`, 250 distinct keys, 0 keys shared with the inboxes of Days 3 to 8 (`results/gen-pass-dryrun.out`, `overlap-prior.out`). A first dry run had 1 shared key (Day 3 and 4); the `C_tvt` operator of that slot was changed and the dry run repeated. Nothing was written under `runs/day9/{inbox,gen}`; no real gate file was written.
7. [§3 daily loop, plan] 250 programs: 109 fresh (44 in the new areas `dunder_dispatch` and `context_managers`, 65 in nine areas with no program on Days 7 and 8), 48 with the new operators `dunder_instance_shadow` and `exit_swallow_flip` (+4 inside the crash groups), 47 with the six operators no earlier day used (+10 inside the crash groups), 22 crash-family programs, 24 pass-2 reserve. The ten areas that took 230 of Day 8's 250 programs get 43 (`results/budget.out`). No pytest or kb-selftest run: no code, KB or pin changed in this step.

Log line: Day 9 phase 2: 0 programs generated (250 planned, dry run `pending=250 written=0`), 1 program promoted to `runs/hits` (40 to 41), 0 retired by move, 0 new candidates, 0 issues filed.

## Cleanup note (pre-generation)

- Shell probe passed (bash script, output read back).
- Removed untracked leftovers from the failed step: probe-d9.out, probe-d9.txt.
- Branch campaign/day9-p2, HEAD 377d3d8 before this note.
- Left uncommitted and unchanged: campaign/day7-report.md (stray garbled text "se=0-9rches" in one line) and campaign/day8/phase6/results/commit.out (captured git output). Neither is meaningful.
- Untouched untracked: -l, .kiro/, findings/2026-10-27-llm-run/.
- Pins unchanged: mypy 2.4.0, ty 0.0.97, pyright 1.1.414, CPython 3.13.16.
