# Day 3 report (Plan §3 "REPORT")

> Paths written as `[campaign working file]`, `[run output]` or `[agent working file]` point to scratch files of the original campaign that are not part of this repository.

Branch [campaign working file]. Every number below is copied from a command output kept in the repo
([campaign working file], `day3-morning.md`, `day3-stats.txt`, `day3-triage.txt`, [campaign working file], and the
report-time counts in [campaign working file]). Nothing here is a confirmed bug. Every candidate is UNVERIFIED and
needs the Plan §6 checklist by a human before anything is filed. Issues filed: **0**.

Tool versions (from the reports): mypy 2.4.0 (compiled), ty 0.0.84, pyright 1.1.414, CPython 3.13.16, target Python 3.13.

## 1. Per-step table

Commands are copied from the scripts and the log. The `generate` / file-bridge commands of the gen pass were not saved
anywhere (see section 7); only their outcome counts were logged.

| Plan label | What happened | Exact command (as recorded) | Result |
|---|---|---|---|
| setup | checkout, dirs, remove stale gate files | `git checkout [campaign working file]`; `mkdir -p [run output] [agent working file]`; `rm -f` of `day3-morning-review.json`, `day3-gen-status.json` | ok |
| §6 step 8 / record upstream | 11 crash entries (new `kind="crash"`) + 9 discrepancy entries + 2 priors in `known_upstream.json`; 2 issues not representable (pyright#11851, #11859) | commits `ce63f5c`, `ca5f30b`, `97c7bd8`, `603a895`, `ee5e6ac`, `4c3f4cc` | pytest 355 passed, kb-selftest 20 PASS (at that point); reviewer approved iteration 2 |
| off-plan fix 1 | `generate --n 3` produced 1 distinct prompt | fix `dc51a60` (seed=k passed to `complete_json`, filename `sha1(src)[:8]`); test `tests/test_generate_variants.py` | 3 distinct prompts after the fix; pytest 357 passed |
| §3 morning: replay | re-judge Day-2 `out3` under the new KB | `.venv/bin/python scripts/kbloop_replay.py [run output] [run output] --jobs 14 --verify-sample 50` ([campaign working file]) | 5086 reports, verify-sample 50/50 identical, exit 0 |
| §3 morning: stats/triage | | `.venv/bin/python scripts/kbloop_stats.py [run output]`; `.venv/bin/typediff --out [run output] triage [run output] --top 30 --details` and `--top 60` (`post_replay.sh`) | live 7277 -> 7273 |
| §3 morning: promote parents | 32 files in [run output] (30 new `d3p_*.py` + 2 existing `s3r1_*`) | [campaign working file], `mk_parents_b.py`; checks `check_hits.py`, `python -m py_compile`; no-LLM run: `typediff --out [run output] --python-version 3.13 seeds [run output]` with `TYPEDIFF_LLM=null` (`run_hits.sh`) | header/AREAS/compile/preflight 32/32 ok; each parent reproduces its signal |
| off-plan fix 2 | orphaned pyright node processes after checker timeouts | [campaign working file] (16 killed); fix `032bf3d` (`Popen(start_new_session=True)` + `os.killpg(SIGKILL)`); `tests/test_runner_timeout_kills_group.py` (3 tests) | pytest 360 passed |
| §3 morning: retire | verdicts for the 13 biggest live patterns | none (analysis in `day3-morning.md` §3) | 0 new KB/upstream entries |
| §3 gen pass (prompts, file bridge) | 160 variants written from the parents | exact `typediff generate ... --llm file:...` lines not recorded | pass 0 pending=160 written=0; pass 1 pending=1 written=159; pass 2 pending=0 written=160 |
| §3 judge | | `TYPEDIFF_LLM=null .venv/bin/python scripts/kbloop_run.py [run output] [run output] --jobs 14 --progress [run output]` ([campaign working file]) | `DONE ... total=160 {'ok': 160} elapsed=43s`; 160 report files |
| §3 stats | | `.venv/bin/python scripts/kbloop_stats.py [run output] > [campaign working file]` | see section 2 |
| §3 triage | | `.venv/bin/typediff --out [run output] triage [run output] --top 30 --details > [campaign working file]` | 48 findings in 19 patterns |
| report-time checks | | `.venv/bin/python -m pytest tests -q`; `.venv/bin/typediff --python-version 3.13 kb-selftest` | 360 passed in 63.84 s; 20 PASS, 0 FAIL |

## 2. Funnel, Day 3 vs Day 2

Day 2 was the no-LLM P1 run over harvested seeds (`day2-run-report.md`: "P2-P6 ... skipped"). Day 2 therefore has no parents,
prompts or generated programs. The Day-2 column is the final `out3` result; where the Day-3 replay of the same 5086
reports differs it is shown in brackets.

| Stage | Day 2 | Day 3 |
|---|---|---|
| parents promoted into [run output] | n/a (2 candidates copied: the two `s3r1_*`) | 32 (30 new + the 2 existing). The 160 programs come from 40 parent files x 4 each: 30 `d3p_*`, 2 `s3r1_*`, plus 8 `gen0..gen7` files (their origin is not recorded, section 7) |
| prompts written | n/a | 161 `*.prompt.md` and 161 `*.answer.json` in [run output] (one more than programs, cause not verified) |
| programs written | 5129 harvested programs in the set | 160 (`find [run output] -name '*.py'`: 17 area directories; 120 `d3p_*`, 32 `gen0..gen7`, 8 `s3r1_*`) |
| preflight-rejected | 43 of 5129 (non-stdlib import or non-determinism) | 0 at judge time (`rejected/failed: {}`); rejections at the generation step were not logged |
| programs run | 5086 | 160 (`{'ok': 160}`, 43 s, `--jobs 14`) |
| discrepancies | 10597 | 50 |
| tool crashes | 10 | 18 (14 programs; 12 are mypy SIGSEGV or ty overflow duplicates, 6 live) |
| live crash findings | 10 (6 after the Day-3 replay with the new crash entries) | 6 (5 ty SIGABRT stack overflow, 1 ty salsa panic) |
| auto-closed (dismissed) | 3330 (3334 in the replay) | 20 |
| auto-closed by the new Day-3 upstream entries | 0 (replay: 4 crash findings) | 5 (UPSTREAM-MYPY-20969 x2, UPSTREAM-MYPY-22339 x2, UPSTREAM-TY-4884-REVEAL x1). All three ids are absent from `known_upstream.json` at the Day-2 final commit `4055e85` and present now |
| auto-closed by the older rule/KB layer | 3330 | 15 (`rule:crash:signal` 12; BOTH-GRADUAL 1, LITERAL-WIDENING 1, TY-CALLABLE-DUNDER 1) |
| live review queue | 7277 (7273 after replay) | **48** (42 non-crash + 6 crash) |
| programs with a live finding | 2566 of 5086 (50.5 %) | 41 of 160 (25.6 %) |
| discrepancies per program | 10597 / 5086 = 2.08 | 50 / 160 = 0.31 |
| share of findings auto-closed | 3330 / 10607 = 31.4 % | 20 / 68 = 29.4 % |
| live by kind | only_mypy 2551, reveal_mismatch 2103, only_ty 1764, concern_mismatch 750, runtime_miss 69, reveal_unpaired 30, crash 6 (replay) | reveal_mismatch 23, only_mypy 10, only_ty 8, crash 6, reveal_unpaired 1 |

Findings check: 50 discrepancies + 18 crashes = 68 = 48 live + 20 dismissed. Dismissed by category: DUPLICATE 17, DESIGN_DIVERGENCE 2, SPEC_AMBIGUITY 1.

Area counts of the 160 programs (from [run output]): generics_variance 16, narrowing_user 16, paramspec_concatenate 16, callables 12,
constructors_metaclasses 12, descriptors_properties 12, enums_literals 12, self_classmethods 12, typeddict 12, inheritance_mro 8,
recursive_aliases 8, async_generators 4, gradual_any 4, narrowing_builtin 4, protocols 4, tuples_unpacking 4, typevartuple_unpack 4.

Reading: the two runs are not comparable per program (hand-curated small parents vs harvested test-suite fragments). Programs with a
live finding are 25.6 % here vs 50.5 % on Day 2. One plausible reason, not verified: the parents are small reproducers whose
signal is already known and often already closed. Only 5 of 20 closures came from the new upstream entries; 12 of the 18 crash findings were closed by the
pre-existing same-signature rule (the mypy SIGSEGV and repeated ty overflows of the same family). The `rule:crash:signal` dedupe can
hide a different bug that shares a signature (noted in `day3-morning.md` §6).

## 3. Patterns of the generated programs (first impressions, NOT bug classifications)

`typediff triage --top 30` returned only **19 patterns** (48 findings), so there are no patterns 20 to 30. "Strong" = the pipeline
attached CPython runtime/stack-trace evidence "supports bug". Every row is marked **for human triage**; no Plan §6 checklist was run.

| # | Pattern (count, strong) | First impression |
|---|---|---|
| 1 | reveal_mismatch / different (12 findings, 7 with strong evidence; the triage prints 3 examples): IntEnum alias, metaclass `A * B`, recursive TVT-default alias | looks like checkers disagreeing with CPython on literal values; mypy and pyright agree with each other |
| 2 | crash / ty:signal-SIGABRT:stack-overflow (5, 5 strong) | ty stack overflow on self-annotated `__call__` and `Self \| None` families; same signature as known team repros |
| 3 | reveal_mismatch / ty_more_precise (2, 2 strong) | ty reveals `int`, runtime value is `None` (stale alias of a condition) |
| 4 | reveal_mismatch / uncomparable (6, 1 strong) | display differences (`partial[int]` vs `partial[(...) -> int]`, recursive alias rendering) plus the metaclass `A \| B` case |
| 5 | only_ty / type-assertion-failure (2, 1 strong) | ty folds a comparison on a tuple subclass to `Literal[False]`; runtime `bool` |
| 6 | only_mypy / misc "property read-only" (1, 1 strong) | ty silent on assigning to a read-only property, with ty inferring the receiver as `Never` |
| 7 | only_mypy / assert-type (1, 1 strong) | mypy `Literal[True]`, ty `Never` on the same tuple-subclass shape |
| 8 | crash / ty:panic salsa `execute.rs:751:9` (1, 1 strong) | "too many cycle iterations" panic in `infer_definition_types` |
| 9 | only_mypy / arg-type (1, 1 strong) | mypy rejects a Flag combination for `Literal[F.R]`; ty infers `Never` for the operand |
| 10 | reveal_mismatch / gradual (3, 0 strong) | mypy `Any` vs ty precise type after `type(name, bases, ns)` / generic protocol |
| 11 | only_mypy / attr-defined (3, 0 strong) | mypy attr-defined on `cls.param` assigned in a metaclass-driven base |
| 12 | only_ty / invalid-argument-type (2, 0 strong) | `len()` on a TypeVar default; `Sink[float]` vs `Sink[int]` contravariance |
| 13 | only_ty / invalid-assignment to attribute (2, 0 strong) | ty rejects assignment to a descriptor attribute, mypy silent |
| 14 | only_mypy / override, return type (2, 0 strong) | stub-skew on `type.__or__` return type (hint STUB-SKEW) |
| 15 | only_mypy / override, signature (1, 0 strong) | stub-skew on `tuple.__add__` |
| 16 | only_ty / invalid-method-override (1, 0 strong) | `tuple.__len__` override, stub-skew |
| 17 | only_mypy / misc unsafely overlapping (1, 0 strong) | `total_ordering` swapped `__ge__`/`__le__` overlap, mypy only |
| 18 | reveal_unpaired (1, 0 strong; 1 medium evidence) | mypy prints nothing at a reachable `reveal_type(Keyed().__hash__())`; ty reveals `Never` |
| 19 | only_ty / invalid-assignment (1, 0 strong) | `partial(f, 10)` not assignable to a `Callable` alias; hint GRADUAL-OPERAND |

(The triage prints at most 3 examples per pattern, so patterns 1 and 2 show fewer examples than findings. [campaign working file] is
the authoritative list. Some strong-evidence counts in the right-hand cells come from the triage header lines.)

## 4. Candidates with strong evidence (all UNVERIFIED)

Important limit: none of these is a "CPython crash + silent checkers" case. In every generated program CPython ran to success
(`runtime: success` in each report). The crash candidates are checker crashes. The discrepancy candidates are cases where the
runtime value contradicts one checker's revealed type. Full reports: `[run output]<id>.md` (the `runs/` tree is not tracked; the
paths below are the generated programs).

### 4.1 Checker crashes, not matched by any upstream entry or by an earlier same-signature finding in the run

| Program | Result |
|---|---|
| [run output] (seed-0032056ba741); `.../d3p_callables_self_call_attr__mut0_eae572b3.py` (seed-6cb04c1e6fbc) | ty 0.0.84 SIGABRT, "thread '<unknown>' has overflowed its stack"; mypy SIGSEGV (dismissed as same-signature duplicate). Variants of the team repro A1 |
| [run output] (seed-3e7d6fb5688c); `.../d3p_self_classmethods_self_call_union__mut0_a5207109.py` (seed-887c42f07fb0) | same ty stack overflow, same mypy SIGSEGV. Variants of A5 |
| [run output] (seed-d8c0c3a3b3ad) | ty stack overflow only |
| [run output] (seed-c47eb01468dc) | ty panic at `salsa-0.28.5/src/function/execute.rs:751:9`: ``infer_definition_types(Id(40a)): execute: too many cycle iterations`` |

Each report carries the pipeline hint RERUN-BEFORE-REPORTING: re-run on the newest ty before reporting (in kb-loop round 2, 5 of 11 ty
crash rows were fixed one release after the pin). Duplicate-check hints (not run; `gh search issues` rejects `--state all`, use no
state flag): `gh search issues --repo astral-sh/ty "overflowed its stack"`, `gh search issues --repo astral-sh/ty "too many cycle iterations"`,
`gh search issues --repo python/mypy "segmentation fault"`.

### 4.2 Runtime value contradicts a checker's revealed type

| Program (all under [run output]) | mypy / ty / pyright / runtime |
|---|---|
| `enums_literals/d3p_enums_literals_intenum_true_aliases_one__mut1_2f2cf71e.py` L21 `reveal_type(Integer.TRUE)` (seed-0de4710c02b5) | mypy `Literal[Integer.TRUE]`, ty `Literal[Integer.ONE]`, pyright like mypy; runtime `<Integer.ONE: 1>` |
| `constructors_metaclasses/d3p_constructors_metaclasses_reflected_operator_on_metaclass__mut0_848753c0.py` L25 `A * B` (seed-229f1d38c10b) | mypy `Literal['left']`, ty `Literal["right"]`, pyright like mypy; runtime `'right'` |
| same family `__mut1_714d2273.py` L25 `A \| B` (seed-83edc0d9bc6c) | mypy `Literal['left']`, ty `types.UnionType special-form`, pyright like ty; runtime `'right'`. Also mypy `[override]` on `__or__`/`__ror__` (STUB-SKEW hint) |
| `narrowing_builtin/d3p_narrowing_builtin_stale_alias_condition__mut1_71417fc0.py` L21 and `__mut0_7429471b.py` L25 `reveal_type(a.x)` (seed-61524ebfb287, seed-e027e3604195) | mypy `int \| None`, ty `int`, pyright like mypy; runtime `None` |
| `tuples_unpacking/d3p_tuples_unpacking_constant_fold_subclass__mut1_abe32df5.py` L23 and `__mut0_fef00a03.py` L16 (seed-e1e14ede1dfc, seed-b25f9bf52142) | `assert_type(r, bool)`: ty `Literal[False]` (mut1) or `Never` (mut0), mypy `bool` / `Literal[True]`; runtime `bool`. Same shape as the Day-2 log-only constant-fold candidate |
| `descriptors_properties/gen7_14eb1842.py` L32 `t.readonly = 5` (seed-4aa8be0814f0) | mypy `[misc] Property "readonly" ... read-only`, ty silent and infers `t: Never`, pyright like mypy; runtime type `Thing` |
| `enums_literals/d3p_enums_flag_or_literal_union__mut0_41da72aa.py` L32 (seed-e4277cc03f53) | mypy `[arg-type] ... "F"; expected "Literal[F.R]"`, ty silent and infers `combined: Never`, pyright like mypy; disagreement persists with `strict-equality-semantics=true` (E3), so TY-STRICT-EQUALITY does not explain it |
| `recursive_aliases/d3p_crash_mypy_segv_recursive_tvt_default_alias__mut0_9fca6f47.py` L20 (seed-4d6aa9e30260) | mypy `tuple[int, tuple[str, ...]] \| None`, ty fully literal nested tuple, pyright like ty; runtime nested tuple does not inhabit mypy's type |
| `inheritance_mro/d3p_inheritance_mro_hash_none_from_eq__mut1_fdf751d0.py` L28 (seed-a43a619b6518) | mypy prints no `reveal_type`, ty `Never`; medium evidence "mypy treats reachable code as unreachable" |

Cheap duplicate-check hints (read-only, not run): ty `Never` operand inference: `gh search issues --repo astral-sh/ty "inferred Never narrowing"`;
metaclass reflected operator: `gh search issues --repo python/mypy "metaclass __ror__"`; IntEnum alias: `gh search issues --repo python/mypy "enum alias member"`;
stale condition alias is MYPY-13807 on the mypy side, here ty is the side that disagrees with runtime, so it is not covered by that entry.

## 5. Proposed [run output] additions for Day 4

Copy these generated programs into [run output] with the 3 header lines (`# area:`, `# hypothesis:`, `# origin:`). Proposed because they
carry strong evidence and differ from their parents:

1. [run output] (ty infers `Never` on a read-only property receiver)
2. [run output] (ty `Never`; E3 shows the strict-equality explanation does not apply)
3. [run output] (ty `int` where runtime is `None`)
4. [run output] (adds `|` operator)
5. [run output]
6. [run output] (ty `Never` instead of `Literal[False]`)
7. [run output] (still panics; shortest salsa cycle repro)
8. [run output]

Not proposed: the SIGABRT/SIGSEGV variants (same shape as parents A1/A5/protocol_flatten, already in [run output]), and all programs whose
only evidence is stub-skew or gradual differences (patterns 10 to 19 above).

## 6. Pipeline findings

Worked:
- Variants-collapse fix (`dc51a60`): `--n 3` now yields distinct prompts and stable filenames. The gen pass produced 160 distinct program files for 40 parents x 4.
- Hash-name fix: output names use `sha1(src)[:8]` instead of `hash()`. All 160 file names carry an 8-hex suffix. Stability across runs was not re-tested in this report.
- Runner process-group kill (`032bf3d`): checker timeouts no longer leave pyright node children. 16 old orphans (1.4 to 4.4 h, ~100 % CPU) were found and killed before it.
- Judge of 160 programs: 43 s with 14 jobs, no runner errors (`{'ok': 160}`), no OOM or kiro exit recorded during the judge run.
- Day-3 upstream entries: 5 live findings closed, 4 Day-2 crash findings closed by replay (verify-sample 50/50 identical).

Broke / rough:
- File-bridge ergonomics: 160 prompts needed three passes (160 pending -> 1 pending -> 0). The leftover item was `cf76eb214a9a3afa` (generics_variance, narrowing_construct_swap). The command lines are not saved, so the run cannot be re-created from the log alone (section 7).
- 161 prompts and 161 answers vs 160 programs: one extra bridge item; not traced.
- Memory-guard events: the morning run-log records one `SIGKILL (4 GB guard)` on the mypy TVT-alias segfault parent and TY-4899 now also accepts `ty:signal-SIGKILL`. The user's earlier reports of repeated out-of-memory exits are attributed in the log to the orphaned pyright processes, which is plausible but was not proven.
- `rule:crash:signal` dismisses same-signature crashes in one run. 12 of 18 crash findings were closed this way, so a different bug sharing a signature can be hidden.
- Queue is still large on the Day-2 corpus: 7277 -> 7273 live (Phase-1 target was more than 50 % shrink).

## 7. Not verified

- Every candidate in section 4 is unverified: no Plan §6 checklist, no reduction, no run on newer tool releases, no duplicate search (`gh` was not successfully run).
- That the A1/A5 variants and the salsa panic are not already filed: no entry matches them, but no issue search was made.
- Origin of the `gen0..gen7` files (32 of the 160 programs) and the exact `generate` / file-bridge commands and model used for the answers.
- Why there are 161 prompts/answers for 160 programs; how many items the generation preflight rejected (not logged).
- That the 12 `rule:crash:signal` closures are all true duplicates; only the signature string was compared.
- The 8 kb-closed discrepancies (BOTH-GRADUAL, LITERAL-WIDENING, TY-CALLABLE-DUNDER and the 5 upstream ones) were not re-read by hand in this report.
- Whether ty's `Never` inference (descriptor, Flag) is one underlying bug or two.
- The "first impression" column of section 3 comes from the triage text only; the programs were not read.
- The Day-3 replay figures for Day 2 come from `day3-morning.md`; the Day-2 final figures come from `day2-run-report.md`.
- Final verification: pytest passed 360 on 2 of 3 full runs. One full run had 1 failure, `tests/test_runner_timeout_kills_group.py::test_timeout_kills_grandchild`, and it passed 3/3 in isolation. Suspected cause (not confirmed): the test uses a 1 s timeout, so under full-suite load bash may be killed before it writes the pidfile. The test is from commit `032bf3d`; not changed here. kb-selftest: 20 PASS, 0 FAIL.
