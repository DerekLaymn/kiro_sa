# Day 5 morning decisions (Plan §3 "Every morning")

Branch `campaign/day5-p2`. Inputs: `campaign/day5-stats.txt`, `campaign/day5-triage.txt`, the 250 reports in `runs/day5/out/`, `campaign/day4-report.md` sections 3 to 5, `campaign/day5-run-log.md`.
(`campaign/day5/promote-report.md` named in the task does not exist; the step-2 promotion record is in `campaign/day5-run-log.md`, "Step 2".)
Tools in the project venv: mypy 2.4.0, ty 0.0.84, pyright 1.1.414, CPython 3.13.16. Nothing was pushed, no issue or PR was created.
The pipeline never calls the network. For the duplicate checks below I used read-only `gh` (`gh search issues`, `gh issue view`) and read the issue BODIES, not only titles.
`triage.txt` shows only three examples per pattern, so I read every one of the 196 findings in the JSON reports (script output in `/tmp/d5m`, not kept) and sorted them by parent program.

## 0. Rules applied

* A finding is retired only when it is (a) a genuine DUPLICATE whose issue body names the same behaviour, or (b) a documented design difference. Anything else stays live.
* **ty#4656 (Self parameter on inherited methods) is a design difference, not a bug.** It is `prior_stances` `TY-4656` (stance `intended`) plus `kb:TY-SELF-UPPER-BOUND`. No Day-5 finding involves a Self upper-bound difference, so nothing was reclassified in either direction; no `entries` item for ty#4656 exists or was added.
* New upstream entries get no `example`, so `kb-selftest` stays at 21 PASS (they are tested in `tests/test_upstream_day5_morning.py`).

## 1. Promotions into `runs/hits/` (git-ignored, new file force-added)

| Item | Decision |
|---|---|
| The 8 `d4p_*` parents (`campaign/day4m/mk_parents.py`, the 8 programs of day3-report §5) | **Present and used.** All 8 are in `runs/hits/`; each produced exactly 4 of the 250 Day-5 programs (50 hits x 4 mutants + 50 LLM seeds = 250). Every one of them contributed findings, none was dropped. |
| `d5p_descriptors_decorated_get_pyright_rangeerror.py` (step 2) | Present. |
| **NEW** `d5p_descriptors_one_decorator_dunders_pyright_rangeerror.py` | Promoted from seed-3ec974e3a5b4 (a mutant of the step-2 hit). One class-body decorator on `__get__` and `__set__` plus an undecorated `__delete__`: a smaller reproducer. pyright 1.1.414 dies with `RangeError: Maximum call stack size exceeded` (typeUtils.ts); re-run just now on the file itself. `uvx --from pyright` (latest on PyPI) reports the same version 1.1.414 and crashes the same way, so there is no newer release to retest on. Similarity to the step-2 hit 0.78 (< 0.80). mypy and ty report ordinary arg-type errors; CPython runs it. A checker crash on runtime-valid code is a bug in any case. |

`campaign/day4m/check_hits.py 0.80`: **51 files, 0 with problems, 0 near-duplicate pairs**, nothing moved to `runs/hits-dropped/`.

Not promoted, with reason:

* Variants of the NEW bugs whose parents are already hits: C2 protocol-flatten overflows (8 findings), metaclass `A + B` / `A @ B` / `A * B` (8), stale-alias loop (22). They add no pattern, and 28 of the 87 programs with a live finding are already >= 0.80 similar to an existing hit.
* C3 ty salsa panics (9): fixed in ty 0.0.85, pinned-version artefact (Day-4 verify-v1 C3).
* The other pyright RangeError program (seed-0f7d5d15677f): 0.89 similar to the step-2 hit.
* `gen9_647c1dcd` (`dataclasses.replace(base, bogus=1)`, mypy plugin check that ty and pyright lack), `gen7_479c0287` and `19a12df31b2c` (lambda argument names against a callback protocol): feature gap or mypy leniency, not a bug pattern worth mutating.

## 2. Retired: upstream entries added or widened (`typediff/data/known_upstream.json`, `typediff/kb.py`, `typediff/crash_upstream.py`)

| Entry | What changed | Evidence (issue body read, 2026-11-05) | Findings closed |
|---|---|---|---|
| `TY-4148`, `MYPY-22361` (crash) | `call_attr_own_type` also follows a local bound by `c = C()` and then called | seed-0bc328316b4c is the exact ty#4148 program with one extra line (`class C: __call__: 'C'`; `c = C(); c()`). ty 0.0.84 stack overflow, mypy 2.4.0 SIGSEGV; the matcher required `C()()` or an annotated name. ty#4148 and mypy#22361 are both OPEN. | 2 (one program, both tools) |
| `MYPY-21937-REVEAL` (new, kind `reveal_unpaired`) | mypy prints nothing in the final `else` of an `is` / `==` chain over a Flag | mypy#21937 "Incorrect narrowing of Enum.Flag" (OPEN, reopened): mypy expands Flag into members. Same matcher as `MYPY-21937` (`flag_is_chain`). Day-4 verify-v2 §4.4 measured the same: mypy "no output", ty `Never`/intersection, pyright `F`, CPython runs the branch ("both"). | 3 of 4 |
| `TY-876` (widened) | `requires flag_member_op` also accepts the inversion `~F.X` of a Flag member | ty#876 checklist item "Handling of enum.Flag" (OPEN, unchecked). Day-4 verify-v2 §4.4 table: `~F.R` ty `Literal[F.R]`, runtime `F.W`. Here: `b = ~F.W`, ty `Literal[F.W]`, CPython `b is F.R` is True. | 3 |
| `MYPY-22339` (widened) | a public property whose `@x.setter` takes `Callable[[T], R]` | mypy#22339 body: "The same behavior occurs with ... a property with a setter" and "read-only `@property`" is listed as the control that stays contravariant, which the matcher keeps unmatched. CPython raises the predicted `AttributeError` (caught by the program). | 1 (seed-a660052c7821) |
| `MYPY-16830` (new, `only_mypy`: assignment, arg-type, assert-type) and `MYPY-16830-REVEAL` (new, `reveal_mismatch`), `requires enum_value_alias` | an enum member that is a runtime alias (same constant value as an earlier member, `True` after `1` included, or assigned an earlier member) is treated by mypy as a member of its own | mypy#16830 body: "aliases or duplicate values are treated as never-equal", with the Python docs rule that the second member is an alias. It is CLOSED/COMPLETED, but PR #20492 (the fix) reworked equality and identity narrowing only; mypy 2.4.0 still rejects `x: Literal[E.A] = E.B`, `assert_type(E.B, Literal[E.A])` and `assert_never` on the alias (Day-4 verify-v3 §1 measured master as well). `assert_never` on an explicit alias is the open mypy#21117. ty matches CPython (`E.B is E.A`); pyright has the same limitation (pyright#11100, open). | 10 + 7 |

Closing a finding as DUPLICATE of a closed-but-still-reproducing issue follows the existing precedent (`TY-4884`, `TY-4883`, `PYRIGHT-11960`): the note says so.
`_doc` and `ALLOWED_KINDS` (tests/test_upstream_day3.py) now list `reveal_unpaired` as an allowed entry kind.

Matchers are narrow on purpose (controls in the tests): `auto()` values, a custom `__new__`, a Flag class, a canonical (first) member, an underscore-named property, a read-only property, a plain Enum chain, and a reveal in the first branch of a chain all stay live.

### Hand check of the 26 changed findings (`runs/day5/replay` vs `runs/day5/out`, reports and source read)

All 26 have CPython `runtime: success`; none carries CPython exception evidence and none belongs to a different tool's bug.

| Entry | Seeds | Check |
|---|---|---|
| TY-4148 + MYPY-22361 | 0bc328316b4c | exactly the issue program; both crash signatures; `rule:crash:signal`, `closed_by` set |
| MYPY-21937-REVEAL | 21e5664f55a9, 7517113c9957, b3771201cb49 | final `else` of `is` chain over `enum.Flag`, mypy silent, ty reveals `F & ~Literal[F.R] & ~Literal[F.W]`, pyright `F` |
| TY-876 | 3e406bea8b95, 8d8891bc53da, a58464057175 | `b = ~F.W` (or `~F.R`) then `reveal_type(b)`; runtime strong evidence says ty's type is wrong, which is the ty#876 item |
| MYPY-22339 | a660052c7821 | setter form of the issue program; pyright rejects, ty rejects, CPython `AttributeError: 'float' object has no attribute 'bit_length'` |
| MYPY-16830 | 5b98a456c114 (2), 744e0c9a2bca (2), 99f2b5bbcca2 (2), bf85c3cc7d9a (2), bcac6db24c36, c4abcbc71843 | `ONE = 1; UNO = 1` (IntEnum), `RED = 'red'; CRIMSON = 'red'` (StrEnum), `A`/`B` same value; stdout shows `UNO is ONE` True; ty and CPython agree, mypy and pyright reject |
| MYPY-16830-REVEAL | 15050f63eb1b, c96335a99642 (2), 445fbcda8148, bcac6db24c36, c4abcbc71843, e5e3cbef63c0 | `reveal_type(Integer.TRUE)` / `.value` (`TRUE = True` after `ONE = 1`): mypy shows the alias as a member, ty shows `Integer.ONE` / `Literal[1]`, CPython `Integer.TRUE is Integer.ONE` |

## 3. Replay under the final KB

```
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
.venv/bin/python scripts/kbloop_replay.py runs/day5/out runs/day5/replay --jobs 14 --verify-sample 30
```

Output: `replayed 250 reports into runs/day5/replay`, `verify-sample: 30/30 identical to a full re-run (mismatches: 0)`, exit 0, 50 seconds. **OOM kills: 0** (journal grep for oomd / OOM-killer lines over the last 3 hours: 0; `--jobs 14` kept).

| | live before (`runs/day5/out`) | live after (`runs/day5/replay`) |
|---|---|---|
| live findings | **136** | **110** |
| dismissed | 60 | 86 (DUPLICATE 44 -> 70) |
| programs with a live finding | 105 | 87 |
| crash findings live | 20 | 18 |
| by kind | reveal_mismatch 46, only_mypy 44, only_ty 22, crash 20, reveal_unpaired 4 | reveal_mismatch 36, only_mypy 34, only_ty 21, crash 18, reveal_unpaired 1 |
| crash closures by reference | TY-4148 6, MYPY-22361 6, TY-4898 4, MYPY-22360 3, TY-4882 2, MYPY-22344 1 | TY-4148 7, MYPY-22361 7, others unchanged |

Exactly 26 findings changed (script comparing every finding's tier and decider): crash 2, MYPY-16830 10, MYPY-16830-REVEAL 7, TY-876 3, MYPY-21937-REVEAL 3, MYPY-22339 1.

The 110 live findings, grouped by parent file name (approximate):

| Live | Group | Decision |
|---|---|---|
| 8 | ty protocol-flatten overflow (C2) | NEW ty bug, draft 1 in `day3-issue-drafts.md` (no duplicate: ty#4746, #4882, #4694, #4863 read there). Stays live, strong stack-trace evidence |
| 8 | mypy reflected operator on metaclasses (`A * B`, `A + B`, `A @ B`) | NEW mypy bug, draft 3 (no duplicate found there). CPython calls the reflected method of the subclass metaclass first; mypy and pyright pick the left operand. Strong runtime evidence. Stays live |
| 22 | stale aliased-condition narrowing / loop back edge, attribute narrowing across calls | loop back edge is NEW ty bug, draft 2; the method-call form is ty#2792 (open) which stays live on purpose (`calibration/must_stay_live`, Day-4 morning) |
| 15 | ty folds `==` on a tuple subclass with `__eq__` | ty#2171 / ty#2140 design discussion, kept live by calibration (Day-4 morning) |
| 9 | ty salsa panics (C3) | fixed in ty 0.0.85, pinned-version artefact, not reportable, no duplicate issue, so no entry |
| 2 | pyright RangeError | unfiled; `PYRIGHT-11961` is a different trigger (constructor annotated `type["C"]`). `gh search` on microsoft/pyright finds #11961 and old closed telemetry issues (#6783, #9283, ...) whose bodies I did not read, so this duplicate check is **not complete**. Stays live |
| 9 | recursive alias dots / TVT-default alias | mypy#2008 design (display `...`, no narrowing on first assignment); the "strong" evidence there reads `...` as a variadic tuple, a false positive of the runtime-evidence rule (needs a normaliser change, as in Day 4). Not retired |
| 9 | ParamSpec `self: Callable[P, T]` mutants | both tools reject the invalid `self` annotation at different places (mypy at the `def`, ty at `self.x`). Neither is a bug; not retired because no documented reference |
| 4 | `type(..., (IntBase, StrBase))` / `types.new_class` | mypy checks no inconsistent generic bases (also for a plain `class` statement); no mypy issue found by search; candidate for a later report, not a duplicate |
| 3 | TypeVarTuple followed by a default | old-style `Generic[*Ts, D]` is accepted by ty 0.0.84 but rejected by ty 0.0.97 (`invalid-type-variable-default`, tested now); CPython raises `TypeError`. Pinned artefact, not reportable. The ParamSpec-default form (`**P = [bool]`) was not tested on mypy |
| 2 | enum alias residue | `ONE = auto(); TRUE = True` (alias at runtime but `auto()` is not judged statically) and a `match ... case _` over a Flag (the mypy#21937 body only shows the `==` form). Left live |
| 3 | `Handler[T]` with a `Caller[T]` Protocol attribute and lambda arguments | the `use(hf)` row is probably the mypy#22339 root cause but the issue body names only `Callable`; the constructor row is a lambda-argument-name difference (ty and pyright reject, mypy accepts). Left live |
| 16 | mypy-only checks, `dataclasses.replace`, declared-type narrowing on assignment (`gen3`/`gen6`/`gen5`: ty and pyright narrow to the assigned value, mypy keeps the declared type), overrides | design differences or feature gaps, not bugs; none has a verified reference, so no entry |

## 4. Reclassified or corrected

* Bug -> **not a bug / design difference** (nothing newly dismissed): `gen3_01446d71`, `gen6_0adac9f0`, `gen5_92e53331` (narrowing of a declared type on assignment, pyright agrees with ty); ParamSpec `self` mutants; recursive-alias `...` rows (as in Day 4); the `Integer.TRUE.value` "strong" evidence only shows that mypy's `Literal[True]` is not the runtime int `1`, a consequence of the alias row above.
* Bug -> **pinned-version artefact**: old-style `Generic[*Ts, D]` (ty 0.0.97 reports it), C3 panics (ty 0.0.85).
* Bug -> **duplicate**: the enum alias rows (mypy#16830 / #21117), the Flag `else` reveal (mypy#21937), `~F.X` (ty#876), the property-setter variance row (mypy#22339), the `c = C(); c()` crash (ty#4148 / mypy#22361).
* Confirmed bug, kept live: C2, mypy metaclass operator, ty loop back edge, pyright RangeError.
* ty#4656 (Self): unchanged, design difference, no entry; the regression test from step 1 still pins it.

## 5. Tests and commands

```
.venv/bin/python -m pytest tests -q                      -> 422 passed in 63.35s, exit 0   (408 before; +14 in tests/test_upstream_day5_morning.py)
.venv/bin/typediff --python-version 3.13 kb-selftest      -> 21 PASS, 0 FAIL, exit 0
.venv/bin/python campaign/day4m/check_hits.py 0.80        -> 51 files; 0 with problems; no near-duplicate pair
```

One existing test needed a data change: `tests/test_upstream_day3.py::test_entry_schema` listed the allowed entry kinds and now includes `reveal_unpaired`.
The first full run (before that change) had exactly that one failure.

## 6. Not verified / limits

* The new matchers are syntactic. `enum_value_alias` ignores `auto()` and custom `__new__`; a mypy message that names `Literal[E.alias]` for another reason would also be closed. `flag_is_chain` does not check that the chain covers every member.
* The `MYPY-22339` setter variant relies on the issue body sentence; I did not re-run mypy on a property-setter-only program beyond the saved Day-5 report (mypy silent, ty and pyright reject, CPython `AttributeError`).
* pyright duplicate search is title-level for the old closed RangeError issues.
* The mypy#16830 closure note says "mypy 2.4.0 still reproduces"; I checked the saved reports of this run and the Day-4 notes, not a fresh run on mypy master.
* Shell tooling replayed an old command once during this step (the full test script ran twice); results above are from the completed runs.
