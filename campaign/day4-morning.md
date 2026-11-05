# Day 4 morning decisions (Plan §3 daily loop, "morning4")

Branch `campaign/day4-p2`. Inputs: `campaign/day3-report.md` section 5, `campaign/day3-verification.md` (retire list), `campaign/day3-triage.txt`.
Tools in the project venv: mypy 2.4.0, ty 0.0.84, pyright 1.1.414, CPython 3.13.16. Nothing was pushed, no issue or PR was created, `gh` was used read-only.
Helper scripts for this step are tracked in `campaign/day4m/` (`mk_parents.py`, `check_hits.py`, `replay.sh`, `live_dump.py`, `hand_check.sh`).

## 1. Parents promoted into `runs/hits/` (git-ignored)

`campaign/day4m/mk_parents.py` copies the 8 programs of day3-report section 5. Bodies are unchanged. The generator's own comment header
(`# area:`, `# hypothesis:`, `# origin:`, sometimes twice) is replaced by one `# area:` / `# hypothesis:` / `# origin:` triple; a `# features:` line is kept when the program had one.
`area` values are real `typediff.strategy.AREAS` keys. The "Day-4 verification" column comes from `campaign/day3-verification.md`. These programs are parents
for mutation (they carry a signal worth varying); the column says what the signal turned out to be, it is not a bug claim.

| # | File in `runs/hits/` | Source (`runs/day3/gen/...`, seed) | Why it is a parent | Day-4 verification of the Day-3 signal |
|---|---|---|---|---|
| 1 | `d4p_descriptors_readonly_prop_never.py` | `descriptors_properties/gen7_14eb1842.py` (seed-4aa8be0814f0) | ty infers the receiver as `Never` after contradictory attribute asserts and a `__dict__` write; mypy and pyright report the read-only property assignment | ty drops the line as unreachable (attribute narrowing not invalidated, related ty#2792); "ty is silent on the property" refuted |
| 2 | `d4p_enums_flag_or_literal_union_only_r.py` | `enums_literals/d3p_enums_flag_or_literal_union__mut0_41da72aa.py` (seed-e4277cc03f53) | ty `Never` after Flag expansion; the strict-equality explanation does not apply | ty#876 Flag item (now closed by `TY-876-ARGTYPE`, section 2) |
| 3 | `d4p_narrowing_stale_alias_loop.py` | `narrowing_builtin/d3p_narrowing_builtin_stale_alias_condition__mut1_71417fc0.py` (seed-61524ebfb287) | ty `int` where the runtime value is `None`; same file also has the alias-in-loop shape | alias then method call = ty#2792; the loop back-edge shape is a NEW ty bug (draft in `day3-issue-drafts.md`) |
| 4 | `d4p_metaclass_or_reflected_ror.py` | `constructors_metaclasses/d3p_constructors_metaclasses_reflected_operator_on_metaclass__mut1_714d2273.py` (seed-83edc0d9bc6c) | adds `\|` to the `*` parent: ty infers a `UnionType`, mypy picks the left `__or__` | ty side = ty#4683; mypy side = NEW mypy bug (draft) |
| 5 | `d4p_enums_intenum_true_alias_one.py` | `enums_literals/d3p_enums_literals_intenum_true_aliases_one__mut1_2f2cf71e.py` (seed-0de4710c02b5) | enum value-duplicate aliases: mypy/pyright keep two members, ty one | ty is right; mypy/pyright known limitation |
| 6 | `d4p_tuples_fold_subclass_eq.py` | `tuples_unpacking/d3p_tuples_unpacking_constant_fold_subclass__mut0_fef00a03.py` (seed-b25f9bf52142) | ty folds `==` on a tuple subclass with `__eq__` to `Literal[False]`, then `Never` | ty#2171 / ty#2140 design (diagnostic planned) |
| 7 | `d4p_callables_crash_ty_panic_partial_loop.py` | `callables/d3p_crash_ty_panic_partial_or_none_in_loop__mut1_82a9fbe2.py` (seed-c47eb01468dc) | still panics ty 0.0.84 (salsa cycle); regression guard for the pinned version | fixed in ty 0.0.85, not reportable |
| 8 | `d4p_inheritance_hash_none_from_eq.py` | `inheritance_mro/d3p_inheritance_mro_hash_none_from_eq__mut1_fdf751d0.py` (seed-a43a619b6518) | `__eq__` without `__hash__` makes `__hash__` None at runtime; neither checker models it | mypy#20230 duplicate; ty `Hashable` false negative is a NEW ty bug (draft) |

### Check of every file in `runs/hits`

`campaign/day4m/check_hits.py` (venv python 3.13.16) checks, for each file: the 3 header lines, the area key in `AREAS`, `compile()`, `typediff.generator.preflight(src, "3.13")` has no ERROR,
a CPython run, and pairwise near-duplicates (`difflib.SequenceMatcher` ratio of the bodies without header comments).
First run (51 files, threshold 0.70): 0 problems. Pairs at or above 0.80:

| ratio | pair |
|---|---|
| 0.92 | `d3p_constructors_metaclasses_reflected_operator_on_metaclass` ~ `d4p_metaclass_or_reflected_ror` |
| 0.83 | `d3p_constructors_metaclasses_reflected_operator_on_metaclass` ~ `d4v_metaclass_reflected_op` |
| 0.86 | `d3p_generics_contravariant_recursive_base` ~ `d3p_generics_contravariant_recursive_generic_base` |

Rule applied: greedy by priority d4v (verified minimal reproducers) > d4p > d3p, so a file is dropped when its ratio to an already kept file is >= 0.80.
Dropped (moved, not deleted, to `runs/hits-dropped/`): `d3p_constructors_metaclasses_reflected_operator_on_metaclass.py` (covers the `*` operator already held by `d4v_metaclass_reflected_op` and the operator family of `d4p_metaclass_or_reflected_ror`)
and `d3p_generics_contravariant_recursive_generic_base.py` (0.86 to the simpler `..._recursive_base`; both are the mypy#22360 shape).
Result: 49 files in `runs/hits`, 0 with problems, 0 pairs at >= 0.80. Remaining pairs at >= 0.60 (kept on purpose, different signal or different tool):
0.76 `d4p_metaclass_or_reflected_ror` ~ `d4v_metaclass_reflected_op` (`|` vs `*`), 0.72 `d3p_enums_literals_intenum_true_aliases_one` ~ `d4p_enums_intenum_true_alias_one`, 0.70 `d3p_generics_contravariant_recursive_base` ~ `d3p_generics_typevar_default_refers_to_itself`,
0.63 `d4p_tuples_fold_subclass_eq` ~ `d4v_ty_tuple_subclass_dunder_fold`, 0.61 `d3p_inheritance_mro_total_ordering_inherited_lt` ~ `d4v_ty_tuple_subclass_dunder_fold`.
Not text-similar but the same root cause: `d3p_crash_ty_panic_partial_or_none_in_loop`, `d4p_callables_crash_ty_panic_partial_loop` and `d4v_callables_staticmethod_loop_union` (one fixed ty panic, three bodies); kept because the bodies differ and the item-7 parent was requested explicitly.
The 49 files' `runtime=` column also shows that several Day-3 parents exit non-zero under CPython (for example `NameError: reveal_type`); that is old behaviour of those files, not checked by this step.

## 2. Retire: entries added and rejected

Policy applied (task): at most 4 entries, only for a clear verdict (DESIGN_DIVERGENCE with documentation/spec evidence, or DUPLICATE of a real issue URL that I read through `gh`), narrow, never one that
could close a finding with CPython-crash evidence or a different tool's bug, confirmed NEW bugs stay live.

### Added (2)

| Entry (file `typediff/data/known_upstream.json`) | Kind / matcher | Issue (read-only `gh issue view`, 2026-11-05) | Narrowness and safety |
|---|---|---|---|
| `TY-4148` | crash, tool `ty`, signature `ty:signal-SIGABRT:stack-overflow`, requires `call_attr_own_type` (existing function used by `MYPY-22361`) | https://github.com/astral-sh/ty/issues/4148 OPEN, labels fatal/attributes/callables/cycles, body is `class C: __call__: "C"` + `C()()` | needs a class with `__call__` annotated as itself / `Self` / a union holding either AND an instance call. Does not match mutual pairs, a `__call__` method, `__call__: int`, a class that is never called, other signatures (SIGABRT without the overflow text, timeout, SIGKILL, panic), mypy or pyright crashes. Does not match the NEW ty protocol-flatten overflow (control test) |
| `TY-876-ARGTYPE` | `only_mypy`, code `arg-type`, message `has incompatible type "X"; expected "Literal[X.m]"`, requires new `flag_combo_literal_arg` (message names a Flag/IntFlag class of the program, statement uses a bitwise combination of two of its members, directly or via a variable), `demote_on_exception: true` | https://github.com/astral-sh/ty/issues/876 OPEN, checklist item "Handling of `enum.Flag`" unchecked | plain Enum, a non-combination, another message, another class name, another code do not match. New optional field `demote_on_exception` (default off) makes the entry step aside when CPython raised a type-related exception in that statement (`kb.demote_exception_at_statement`), so a finding with CPython-exception evidence is never closed by it |

kb-selftest example: `TY-876-ARGTYPE` has one (`PASS KB:UPSTREAM-TY-876-ARGTYPE`). `TY-4148` is a crash entry; crash entries build no KB entry and have no kb-selftest example by design (see `_doc` in the JSON). Its tests are
`tests/test_upstream_day4.py` (exact issue program, two Day-3 programs, `Self`/`| None` variants, 5 signature-gate cases, 3 shape controls, protocol-flatten and mutual-pair controls, the older ty entries still win on their programs).
`tests/test_upstream_day3.py` had two tests that encoded "ty on A1 is unfiled / stays confirmed"; they now expect `TY-4148` on A1 and use the unfiled protocol-flatten program for the "unmatched crash stays confirmed" check.

### Rejected, with evidence

| Candidate (day3-verification retire list) | Decision | Evidence |
|---|---|---|
| `ty#2792` stale alias after a method call | not added | the repository guards this exact program as must-stay-live: `calibration/must_stay_live/mypy_stale_alias.py` and `tests/test_stage3_round3.py::test_stale_alias_program_stays_in_review_with_real_tools`. In ty#2792 carljm says all checkers narrow attributes this way and keeps it open as a possible improvement, so the closure would also hide the loop back-edge NEW bug family (draft 1b) next to it |
| `ty#2792` read-only property `Never` (seed-4aa8be0814f0) | not added | the mutation in that program is a `t.__dict__[...] = 99` write, not a method call; ty#2792 is about method calls. Verdict not clear enough |
| `ty#2171` tuple-subclass constant fold | not added | `calibration/must_stay_live/ty_constant_fold_tuple_subclass.py` and `tests/test_stage3_round2.py::test_constant_fold_program_stays_in_review` require this program to stay live |
| `ty#4683` `A \| B` metaclass `__or__` | not added | the finding (seed-83edc0d9bc6c D3) also carries mypy's wrong `Literal['left']`, the NEW mypy bug (draft 1); an entry would close another tool's bug |
| mypy enum value aliases (`mypy#16830`, `#21117`) | not added | `gh pr view 20492` (merged 2026-01-16, "Fixes #16830") shows #16830 was fixed; #21117 (open) is the explicit alias form `DEFAULT = V2`. The Day-3 findings are value duplicates (`TRUE = True` after `ONE = 1`, `HIGH = 2`, `READ = 1` vs `auto()`), where the spec is silent (verify-v3 section 1.2) and pyright declines (pyright#11100). No clear duplicate |
| mypy recursive-alias `...` display and no-narrowing-on-assignment (`mypy#2008`) | not added | the KB already has `MYPY-FIRST-ASSIGNMENT-TYPE`; the row stays live because of a runtime-evidence rule that reads the `...` as a variadic tuple (verify-v3 section 3), which needs a normalizer change, not an entry |
| `mypy#20230` `__hash__` None reveal | not added | the finding is a `reveal_unpaired` caused by reachability after `assert Plain.__hash__ is None`; #20230 is about hashing unhashable objects, not this symptom |
| ty `partial \| None` panic | not added | fixed in ty 0.0.85, not an upstream duplicate; disappears on a pin bump |
| `ty#4656` Self parameter, `mypy#13807` aliased conditions | nothing to add | already covered by `TY-4656` / `TY-SELF-UPPER-BOUND` and `MYPY-13807-ALIASED-CONDITIONS` |
| C2 protocol flatten, 1b alias loop back edge, 6a mypy metaclass operator, 8b `Hashable` | stay live | confirmed NEW bugs (drafts in `campaign/day3-issue-drafts.md`), no entries |

Read-only `gh` commands (`/tmp/d4m/gh.sh`, retried up to 3 times, all succeeded first try): `gh issue view N --repo R --json ...` for ty#4148, #2792, #876, #2171, #2140, #4683 and mypy#16830, #21117, #2008, #20230, #22361;
`gh api repos/python/mypy/issues/16830/timeline`; `gh pr view 20492 --repo python/mypy`. States seen: ty#4148 OPEN, ty#2792 OPEN, ty#876 OPEN (Flag box unchecked), ty#2171 OPEN, ty#2140 CLOSED COMPLETED,
ty#4683 OPEN, mypy#16830 CLOSED COMPLETED 2026-01-16 (PR #20492), mypy#21117 OPEN, mypy#2008 OPEN, mypy#20230 OPEN, mypy#22361 OPEN.

## 3. Replay of the Day-3 outputs under the final KB

Baseline: the same 160 saved reports re-judged BEFORE the entries (`runs/day4/replay-d3-base`, same code as the Day-3 end state). Final: the command given in the task.

```
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
.venv/bin/python scripts/kbloop_replay.py runs/day3/out runs/day4/replay-d3-base --jobs 14        # baseline, before the change
.venv/bin/python scripts/kbloop_stats.py runs/day4/replay-d3-base
.venv/bin/python scripts/kbloop_replay.py runs/day3/out runs/day4/replay-d3 --jobs 14 --verify-sample 30   # final (campaign/day4m/replay.sh)
.venv/bin/python scripts/kbloop_stats.py runs/day4/replay-d3
.venv/bin/python campaign/day4m/live_dump.py runs/day4/replay-d3 --diff runs/day4/replay-d3-base
```

Output of the final replay (verbatim; trimmed only in the `live_dump` note lines):

```
replayed 160 reports into runs/day4/replay-d3
verify-sample: 30/30 identical to a full re-run (mismatches: 0)
replay exit 0
[all] programs=160 discrepancies=50 live=43 (programs with live=36, crash findings=2) dismissed=25 tool_crashes=18
   dismissed by category: {'DUPLICATE': 22, 'SPEC_AMBIGUITY': 1, 'DESIGN_DIVERGENCE': 2}
   dismissed by entry: {'rule:crash:signal': 16, 'kb:UPSTREAM-MYPY-20969': 2, 'kb:UPSTREAM-MYPY-22339': 2, 'kb:UPSTREAM-TY-4884-REVEAL': 1, 'kb:BOTH-GRADUAL': 1, 'kb:LITERAL-WIDENING': 1, 'kb:TY-CALLABLE-DUNDER': 1, 'kb:UPSTREAM-TY-876-ARGTYPE': 1}
   live by kind: {'reveal_mismatch': 23, 'only_ty': 8, 'only_mypy': 9, 'reveal_unpaired': 1, 'crash': 2}
5 findings changed
```

Baseline stats (before the entries): `live=48 (programs with live=41, crash findings=6) dismissed=20 tool_crashes=18`, `rule:crash:signal: 12`, `live by kind: crash 6, reveal_mismatch 23, only_ty 8, only_mypy 10, reveal_unpaired 1`.

| Live Day-3 findings | before | after |
|---|---|---|
| total | 48 | **43** |
| crash | 6 | 2 (ty protocol-flatten overflow `seed-d8c0c3a3b3ad`, ty salsa panic `seed-c47eb01468dc`) |
| only_mypy | 10 | 9 |
| reveal_mismatch / only_ty / reveal_unpaired | 23 / 8 / 1 | 23 / 8 / 1 |
| programs with a live finding | 41 | 36 |

Closed per new entry (diff of the two replay directories shows exactly these 5 findings changed, nothing else):

| Entry | Findings closed | Seeds |
|---|---|---|
| `TY-4148` | 4 of 48 | seed-0032056ba741, seed-3e7d6fb5688c, seed-6cb04c1e6fbc, seed-887c42f07fb0 (crash C2 of each, tier confirmed to dismissed DUPLICATE; the report line shows `by=rule:crash:signal` and the review note `DUPLICATE of https://github.com/astral-sh/ty/issues/4148 (TY-4148)`) |
| `TY-876-ARGTYPE` | 1 of 48 | seed-e4277cc03f53 D1 (`kb:UPSTREAM-TY-876-ARGTYPE`) |

### Hand check of every closed finding (`campaign/day4m/hand_check.sh`: saved report, source, fresh run of the pinned ty, mypy, pyright and CPython)

| Seed | Program shape | Fresh run | Verdict |
|---|---|---|---|
| 0032056ba741 | `class C: __call__: "C"`, `C()()` inside `try/except TypeError` | ty exit 134 "has overflowed its stack"; mypy exit 139 (SIGSEGV); pyright 0 errors; CPython exit 0 | exactly the ty#4148 program; closure correct |
| 3e7d6fb5688c | `class Broken: __call__: Self \| None = None`, `Broken()()` (plus an ordinary `Node.__call__` method) | ty 134 stack overflow; mypy 139; pyright `reportOptionalCall`; CPython exit 0 | self-typed `__call__` attribute, the "Self or union" variant named in the entry; closure correct. The `Node.__call__` method part is not the trigger |
| 6cb04c1e6fbc | `class C: __call__: "C"`, `C()()` in `try/except TypeError`, two unrelated classes | ty 134; mypy 139; pyright 0 errors; CPython prints `witness: TypeError`, exit 0 | ty#4148 program; correct |
| 887c42f07fb0 | `class C: __call__: Self \| None = None`, `x: C = C()`, `x()` | ty 134; mypy 139; pyright `reportOptionalCall`; CPython exit 0 | correct |
| e4277cc03f53 | `F(enum.Flag)`, `combined = F.R \| F.W`, `assert combined.value == 3`, `assert only_r(combined) == 1` with `only_r(x: Literal[F.R])` | ty "All checks passed"; mypy `[arg-type] ... "F"; expected "Literal[F.R]"`; pyright `reportArgumentType`; CPython exit 0 | mypy and pyright are right, ty is silent only through the Flag expansion (ty#876); closure as duplicate correct, CPython status `success` so the exception demotion does not apply |

No closed finding has CPython-crash evidence (runtime status `success` in all five reports), and none belongs to a different tool's bug: the ty crashes are ty#4148, the mypy twin of the same four programs was already closed by `MYPY-22361`.

## 4. Tests and kb-selftest

```
.venv/bin/python -m pytest tests -q          ->  373 passed in 63.54s (0:01:03)   exit 0   (360 before, +13 in tests/test_upstream_day4.py)
.venv/bin/typediff --python-version 3.13 kb-selftest   ->  21 lines, all PASS, exit 0 (includes PASS KB:UPSTREAM-TY-876-ARGTYPE)
```

## 5. Exact commands run in this step (in order)

1. `.venv/bin/python campaign/day4m/mk_parents.py` writes the 8 `d4p_*.py` files (output: `wrote d4p_... <- ... (dropped 5 old header lines, ...)` x 8).
2. `.venv/bin/python campaign/day4m/check_hits.py 0.70`: `51 files; 0 with problems`, near-duplicate list of section 1.
3. `mv runs/hits/d3p_constructors_metaclasses_reflected_operator_on_metaclass.py runs/hits/d3p_generics_contravariant_recursive_generic_base.py runs/hits-dropped/`
4. `.venv/bin/python campaign/day4m/check_hits.py 0.80`: `49 files; 0 with problems`, empty near-duplicate list.
5. Baseline replay and stats (section 3), `bash /tmp/d4m/gh.sh` (read-only gh), `gh api repos/python/mypy/issues/16830/timeline`, `gh pr view 20492 --repo python/mypy`.
6. Edits: `typediff/kb.py` (`_flag_combo_literal_arg`, `demote_on_exception`), `typediff/data/known_upstream.json` (`TY-4148`, `TY-876-ARGTYPE`, `_doc`), tests and `tests/data/upstream_day4/*`.
7. `.venv/bin/python -m pytest tests -q`, `.venv/bin/typediff --python-version 3.13 kb-selftest` (section 4).
8. `bash campaign/day4m/replay.sh` (final replay, stats, diff; section 3), `bash campaign/day4m/hand_check.sh` (section 3 table).

## 6. Not verified / limits

- The `TY-4148` shape check (`call_attr_own_type`) is a syntactic match. A different ty stack overflow in a program that also contains a self-typed `__call__` attribute and a call of it would be closed too. The mutual-pair form of the same bug is not matched (stays live).
- ty#4148 was checked on ty 0.0.84 (fresh runs above) and, by the verify-v1 file, on 0.0.97; I did not re-run 0.0.97 in this step.
- The `TY-876-ARGTYPE` claim "ty is silent only because of the Flag expansion" rests on the verify-v2 bisection (`Never` after `assert combined.value == 3`) and the fresh run above; a program where ty is silent for another reason and which also uses a Flag combination would be closed.
- `ty#2792` for the read-only property row and the enum value-alias rows may become clear later; they were rejected here, not disproved.
- The 43 remaining live findings were not re-triaged beyond the Day-3 verification. Among them are findings tied to confirmed NEW bugs (the ty protocol-flatten overflow `seed-d8c0c3a3b3ad`, the metaclass `A * B` / `A | B` rows of seed-229f1d38c10b and seed-83edc0d9bc6c); they stay live on purpose.
