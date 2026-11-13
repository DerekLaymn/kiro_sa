# Round 6 report (Part B: generation, judge, decisions)

This report covers Round 6. The pipeline wrote nothing to GitHub: no issue, PR or comment was created, and the only GitHub access was read-only (`gh search`, `gh issue view`, `gh release list`). Counts come from the stored per-program reports and statistics of the round. Rates were computed while writing the report, and where a figure was not captured the report says so.

Pins: mypy 2.4.0, ty 0.0.97, pyright 1.1.414, CPython 3.13.16, target Python 3.13. Checkers ran through the memguard shims in `.venv/bin` (untouched).
Round 5 ran on ty 0.0.84, so Round 5 vs Round 6 is not like for like: the ty bump itself changed which crashes and divergences appear.

## 1. What was run

Round 6 generated 250 programs through the file bridge (`typediff --llm file:<dir> generate`), with the stand-in model `claude-haiku-5.5` at effort `medium` answering the prompts, judged them with `TYPEDIFF_LLM=null`, replayed the stored reports after each knowledge-base change, and read the remaining live findings. Pins are listed above. The counts the round relies on are in the funnel tables below. The first replay after the matcher changes matched a full re-run on a sample of 30 programs (30 of 30 identical). `check_hits.py 0.80` found 49 parent files and 0 with problems.

## 3. Funnel, Round 5 vs Round 6

| | Round 5 judge run (ty 0.0.84) | Round 6 judge run (ty 0.0.97) | Round 6 after the replay |
|---|---|---|---|
| programs | 250 (200 mutated + 50 fresh) | 250 (200 mutated + 50 fresh) | 250 |
| discrepancies | 154 | 259 | 259 |
| tool crash events | 42 | 62 | 62 |
| findings (discrepancies + crashes) | 196 | 321 | 321 |
| auto-closed (dismissed) | 60 | 103 | 109 |
| live | 136 | 218 | 212 |
| programs with a live finding | 105 | 127 | 122 |
| live crash findings | 20 | 23 | 23 |

Rates (computed here):

| | Round 5 | Round 6 judge run | Round 6 after replay |
|---|---|---|---|
| discrepancies per program | 154 / 250 = 0.62 | 259 / 250 = 1.04 | 1.04 |
| tool crashes per program | 42 / 250 = 0.17 | 62 / 250 = 0.25 | 0.25 |
| live findings per program | 136 / 250 = 0.54 | 218 / 250 = 0.87 | 212 / 250 = 0.85 |
| programs with a live finding | 105 / 250 = 42.0 % | 127 / 250 = 50.8 % | 122 / 250 = 48.8 % |
| share auto-closed | 60 / 196 = 30.6 % | 103 / 321 = 32.1 % | 109 / 321 = 34.0 % |

The Round-6 discrepancy count is inflated by one group. `C_callback` (18 programs) produced 65 discrepancies, 65 live, 0 dismissed: all mypy/ty differences around the Callback shape (draft 5 plus error cascades from invalid declarations such as `class Box[*Ts, U = int]`). Without it: 194 discrepancies in 232 programs = 0.84 and 147 live = 0.63 per program.

Crash events by tool and signature: ty `SIGABRT:stack-overflow` 41, mypy `SIGSEGV` 18, pyright `RangeError` 2, mypy `SIGKILL` 1. 39 are closed by an entry with a reference (`crash closures by closing reference`: MYPY-22361 14, TY-4148 14, TY-4898 7, MYPY-22360 3, MYPY-22344 1). The 23 live crash findings are ty overflow 20, pyright RangeError 2, mypy SIGKILL 1.

Per group after the replay:

| Group | Programs | Discrepancies | Crash events | Live | Dismissed | Programs with a live finding | Programs with strong runtime/stack evidence on a live finding |
|---|---|---|---|---|---|---|---|
| A_ty_crash | 63 | 23 | 53 | 38 | 38 | 30 | 19 |
| M_mypy_crash | 16 | 15 | 5 | 14 | 6 | 8 | 1 |
| P_pyright | 45 | 25 | 2 | 15 | 12 | 14 | 6 |
| C_callback | 18 | 65 | 0 | 65 | 0 | 18 | 3 |
| R_rest | 58 | 96 | 2 | 62 | 36 | 37 | 18 |
| fresh (6 areas) | 50 | 35 | 0 | 18 | 17 | 15 | 0 |
| total | 250 | 259 | 62 | 212 | 109 | 122 | 47 |

The 50 fresh programs found no strong-evidence finding. Their live findings are display differences (mypy prints `case.Handler` or `def (...)` where ty and pyright print the callable; `property` vs `Overload(...)`) and one recursive-alias solver difference (§4 item 5).

## 4. What the pyright pass produced

`P_pyright` (5 parents x 9 = 45 programs) plus the fresh `descriptors_properties` and `paramspec_concatenate` areas were meant to exercise pyright. Result:

* pyright crashed on 2 programs, both `pyright:internal:RangeError` (`Maximum call stack size exceeded`), both mutants of the two Round-5 `d5p_*` RangeError parents (`..._decorated_get_pyright_rangeerror__mut2_5455e8f6`, `..._one_decorator_dunders_pyright_rangeerror__mut2_dcc9f4b2`). No new pyright crash shape.
* 235 of the 250 programs had at least one pyright diagnostic. In the findings' consensus evidence pyright sides with ty 106 times and with mypy 105 times (dismissed findings included). It is a tie-breaker in the pipeline; it never produced a finding of its own, so a pyright-only bug cannot show up in this pipeline's output except as a crash.
* The group produced 15 live findings, 6 programs with strong evidence; every one belongs to a family already known (the two RangeError mutants, read-only property `Never`, `__hash__` None). The 6 `self`-parameter findings in this group are now closed by the new TY-4756 entry (§5).
* Pyright 1.1.414 is the pin; I could not read PyPI from this shell (the `curl` call returned no JSON), so "no newer pyright release" is **not re-checked** today.

## 5. Decisions (B4)

### Entries

| Change | Why | Evidence |
|---|---|---|
| New entry `TY-4756` in `typediff/data/known_upstream.json` (only_mypy, code `misc`, message `"self" parameter missing for a non-static method`, DUPLICATE) | open ty#4756 "no error when instance method has no `self` parameter" (lint label); pyright reports it too; ty does not. 6 live findings were all class-body decorator helpers in `d3p_descriptors_decorated_get` mutants | `gh issue view 4756 -R astral-sh/ty` (body and comments read, state open, updated 2026-10-23); the maintainer comment doubts it should be an error, which the note says. Replay: `UPSTREAM-TY-4756` closes 6 findings (live 218 -> 212) |
| New prior stance `TY-2171` (prior_stances, signature: tuple/NamedTuple subclass with a comparison dunder and a `Literal[True/False]` from ty) | open ty#2171 asks for a diagnostic on exactly that override; design in closed ty#2140. A prior stance only caps drafting at REVIEW and attaches the link; it dismisses nothing | issue body read; 4 tests in `tests/test_upstream_round6.py` |

### Entries I tried and removed (policy conflict, not a bug in the matcher)

I first wrote dismissals for ty#2171 (tuple fold) and ty#2792 (attribute narrowing kept after a method call, plus the read-only-property `Never` row of the same cause), with narrow AST predicates, controls and a hand-check of all 23 changed findings. A replay closed 17 more findings (19 after widening the tuple predicate to `NamedTuple`: TY-2792 8, TY-2792-READONLY 4, TY-2171 4, TY-2171-ASSERT 3). Then pytest failed 3 tests: `calibration/known_duplicates/ty_constant_fold_tuple_subclass.py` and `mypy_stale_alias.py` are pinned as "real discrepancies no dismissal may touch", and a broad `stance` on the new entry made a `find_priors` test see an extra prior. Closing those shapes contradicts that standing rule, so I reverted the predicates, entries and tests (no change left in `typediff/kb.py`) and kept the rule. Effect: 19 known-duplicate findings of this run stay live. The diff of the first replay (23 changed rows: 17 from these predicates and the 6 TY-4756 rows, each hand-checked) is not kept; the 19 is the stats line of the second replay after I widened the tuple predicate to `NamedTuple` (TY-2792 8, TY-2792-READONLY 4, TY-2171 4, TY-2171-ASSERT 3). ty#2792 shapes are in mutants of `d3p_narrowing_*`, `d4p_narrowing_stale_alias_loop`, `d4p_descriptors_readonly_prop_never`, `d4v_ty_attr_eq_narrow_unreachable`. If you want them closed anyway, the change is to add entries and move the two calibration programs out of `must_stay_live`; that is a decision about what the triage shows you, so I left it.

### Parents (49 before, 49 after)

Promoted (2, force-added to git; each one still crashes ty 0.0.97 when run alone, `ty check` rc 134 `stack overflow`):

| New parent | Source mutant | Shape it adds | Max similarity to any hit |
|---|---|---|---|
| `d6p_protocols_expanding_self_receiver_dict_arg_ty.py` | `d4v_protocols_expanding_self_receiver__mut2_6ddbd777` | `self: Stream[dict[str, T]]`, legacy `TypeVar`, `from __future__ import annotations`, the protocol is the type of a function parameter (call position) | 0.65 |
| `d6p_protocols_expanding_self_receiver_tuple_nesting_ty.py` | `d4v_protocols_expanding_self_receiver__mut2_b43fa1f0` | `self: "Stream[tuple[Stream[T]]]"`, PEP 695, generic implementing class | 0.67 |

Not promoted: other expanding-receiver mutants (0.72 to 0.99 similar to existing hits); `mypy:signal-SIGKILL` mutant `d3p_crash_mypy_segv_recursive_tvt_default_alias__mut0_460fd06e` (it ran into the 4 GB cap; promoting it would add a process that eats the cap at `--jobs 14`); the Callback mutants (the CPython `TypeError` is python/typing#2211, the mypy part is draft 5); `seed-d38ecc92765c` (strong runtime evidence but no crash); the metaclass and tuple mutants (families already represented).

Retired to `seeds/parents/` (reversible with `mv`): `d4p_tuples_fold_subclass_eq`, `d4v_ty_tuple_subclass_dunder_fold` (all their Round-6 findings are ty#2171; `d3p_tuples_unpacking_constant_fold_subclass` and the calibration program keep the shape). I moved two more parents out and put them back (`d3p_narrowing_user_attr_narrowing_kept_after_method_call`, `d3p_narrowing_builtin_stale_alias_condition`) because their entry was removed. Hits: 49 files, `check_hits.py 0.80`: 0 with problems, no near-duplicate pair.

### Live families classified by hand (not closed)

| Family | Live findings | Classification | Source |
|---|---|---|---|
| ty overflow on a protocol method whose `self` is `Stream[Stream[T]]` or similar (mutants of 4 hits) | 20 crash findings | draft 1 (user verified on the playground); related open ty#4882, ty#4746 read today; TY-4882 closes only the two-protocol shape | recorded during the round |
| mypy `Foo[int, str]` on `class Foo[*Ts, **P = [bool]]` and variants | 65 findings (group C) | draft 5 (mypy); CPython `TypeError` is python/typing#2211 | recorded during the round |
| mypy reflected operator on class objects with related metaclasses (`A * B`) | 6 (`d4v_metaclass_reflected_op`) + 2 (`d4p_metaclass_or_reflected_ror`, ty/mypy disagree on `left*`/`right*`, runtime `right*`) | draft 3 (mypy) | recorded during the round |
| ty `__eq__`-only class accepted as `Hashable` and the `__hash__` reveals | 5 + 2 + 1 | draft 4 (ty); see candidate 1 for mypy | recorded during the round |
| ty stale alias / attribute narrowing after a method call; read-only property `Never` | 12 matched by the removed predicates, 3 more variants they did not match | ty#2792 (open); alias-in-loop back edge is draft 2 | recorded during the round |
| ty tuple-subclass fold | 6 live before the replay (7 matched by the removed predicates; one of the 7 was already closed as LITERAL-WIDENING) | ty#2171 (open) | recorded during the round |
| `d3p_generics_callable_attr_contravariant__mut0_0bac40f6`: `runtime_miss` with all three checkers silent at `h.add(lambda v: print(v.bit_length()))` | 1 | **harness artefact, not a bug**: all three checkers reject the expected-error line 34 (`use(hf)`), the AttributeError comes from that line's consequence; the finding anchors on the lambda frame | program read in full |
| mypy `Attribute function "__call__" ... does not accept self argument` | 3 | mypy treats a callable class attribute as a method (long-standing, e.g. closed mypy#9489, #6910); ty is silent. Not searched for an exact issue | UNVERIFIED |
| `d3p_paramspec_self_annotated_dunder_call` mutants: ty `unresolved-attribute` on `self.args = args` with `self: Callable[P, T]`, mypy silent | 13 | not analysed beyond the triage text; neighbourhood of TY-4899 | UNVERIFIED |

## 6. Candidate bugs (UNVERIFIED unless stated)

None of these is a new bug family beyond drafts 1 to 5.

1. **mypy accepts a class with `__eq__` and no `__hash__` as `Hashable`.** Minimal program, run by hand with the pins: mypy `Success: no issues found`, ty `All checks passed!`, pyright 1 error (`__hash__` is `None`), CPython `TypeError unhashable type: 'B'`. Counterpart of draft 4 (ty). Duplicate search: three phrases on python/mypy, no result; python/mypy#20230 is related (unhashable not detected for `hash()`, `in set()`, `{obj}`) but does not mention the `Hashable` parameter, so I did not close this as a duplicate. Needs a proper search before drafting.
2. **ty solves `T` in `Nested[T] = T | list[Nested[T]]` differently.** Five fresh recursive-alias programs (`gen5_e68c574b`, `gen4_2f36c930`, `gen0_8410dfae`, `gen2_155b6aa6`, `gen3_89967888`): for `flatten(nested)` with `nested: Nested[int] = [...]` ty reveals `list[list[int | list[Nested[int]]] | int]` while mypy and pyright reveal `list[int]` (and `list[Nested[T@Nested]]`/`int | list[...]` for the leaf rows). The runtime value is a `list[int]`, so the output is not refuted by runtime. It may be the declared-type narrowing on assignment (a design difference already noted on Round 5) plus an ambiguous union solution. No reduction, no duplicate search.
3. **mypy memory blow-up on a recursive TypeVar-default alias**: `seed-eb1b134676f7` (mutant of `d3p_crash_mypy_segv_recursive_tvt_default_alias`) hit the 4 GB cap and was killed (`mypy:signal-SIGKILL`, the kernel `oom-kill` in the guard cgroup). The parent already segfaults or is killed (MYPY-22344 family). No entry covers this signature; no upstream search done.
4. **pyright `RangeError`** on descriptors with class-body decorators on `__get__`/`__set__`: 2 more live programs, same two parents as Round 5. Four queries on microsoft/pyright issues (`Maximum call stack size exceeded RangeError`, descriptor/decorator variants) returned nothing; the old closed RangeError issue bodies were not read. Still no verification checklist and no check for a newer pyright.
5. **New shapes for draft 1** (ty overflow): 20 live findings from mutants with `dict[str, T]`, `tuple[Stream[T]]`, PEP 695, `runtime_checkable`, argument position. Same root cause, useful as extra evidence in the draft; two are now parents.

## 7. Remaining weaknesses

* The must-stay-live policy keeps about 19 findings of two known issues (ty#2171, ty#2792) live in every run, plus the 65 findings of the Callback group. Together with the 20 ty-overflow findings of draft 1, roughly 100 of the 212 live findings are shapes already written up. Recommendation for Round 7: drop `C_callback` and the two retired tuple parents from generation and move that budget to areas with no hit yet.
* Closing a crash needs a source-shape predicate (`crash_upstream`), so the 20 expanding-receiver overflows stay live although they are one bug. A shape-family predicate for draft 1 would need the draft filed first (there is no upstream URL to cite).
* The runtime-evidence rule still reads `...` in recursive-alias reveals as a variadic tuple (`d4v_recursive_alias_dots`: "strong" evidence against mypy that is an artefact), and a `runtime_miss` can anchor on the wrong frame when the program has an `# expect-error` line (candidate above, harness artefact). Both are unchanged from Round 5.
* The generator stand-in produced valid programs for 250 of 250 prompts (no retry prompt). I did not review their quality beyond the preflight and the hypotheses I read while triaging; the fresh set found no strong-evidence finding.
* `--effort medium` was passed but not confirmed in a log.
* The three replays used the same 250 reports; `verify-sample` re-ran 30 programs fully each time and matched (30/30), so matcher changes were validated on 30 programs per replay, not on all 250.

## 8. Not verified

* All candidates in §6 (no verification checklist, no reduction except the Hashable minimal program in item 1).
* Whether ty 0.0.97 `main` still shows any of the above; no `main` build was used.
* Whether pyright 1.1.414 is still the latest release (network read failed).
* The classification of the 13 `paramspec_self_annotated_dunder_call` and the 3 mypy `__call__` rows in §5.
* The "17" and "19" counts come from replays with entries that are no longer in the tree; the diff file of the first one is committed, the second one is only the stats line quoted above.
