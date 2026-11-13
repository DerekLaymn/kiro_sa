# Round 4 report

This report covers Round 4. The pipeline wrote nothing to GitHub: no issue, PR or comment was created, and the only GitHub access was read-only (`gh search`, `gh issue view`, `gh release list`). Counts come from the stored per-program reports and statistics of the round. Rates were computed while writing the report, and where a figure was not captured the report says so.

Tool versions (from the reports): mypy 2.4.0 (compiled), ty 0.0.84, pyright 1.1.414, CPython 3.13.16, target Python 3.13.
Latest releases used during verification: mypy 2.4.1, ty 0.0.97, mypy master 2.5.0+dev.879da562.

## Verification of the Round-3 candidates

The 14 candidate rows below were checked on the newest tool versions (reviewer approved); the drafts are in `results/bugs.md`.

| Candidate | Verdict | Duplicate / status | Draft |
|---|---|---|---|
| C1 self-referential `__call__` (4 programs) | ty BUG (crash), mypy BUG (crash), pyright NOT_BUG | duplicate: ty#4148, mypy#22361 | no |
| C2 protocol `flatten` (`self: Stream[Stream[T]]`) | ty BUG (stack overflow, 0.80) | NEW, none found | yes (ty) |
| C3 `partial \| None` in a loop | ty 0.0.84 BUG (panic), fixed in ty 0.0.85 | not reportable | no |
| 1a stale alias condition | NOT_BUG (all tools) | duplicate ty#2792, mypy#13807 | no |
| 1b alias narrowing survives reassignment on a loop back edge | ty BUG (0.9) | NEW, none found | yes (ty) |
| 2 constant fold, tuple subclass | NOT_BUG, design difference | duplicate ty#2171 (design in ty#2140) | no |
| 3 read-only property `Never` | NOT_BUG ("ty is silent" refuted) | duplicate ty#2792 | no |
| 4 Flag combination `Never` | NOT_BUG as new | duplicate ty#876 | no |
| 5 IntEnum alias | NOT_BUG (ty is right) | mypy#16830, mypy#21117, pyright#11100 | no |
| 6a metaclass reflected operator `A * B` | mypy BUG (0.7), pyright NOT_BUG (design) | NEW (mypy), none found | yes (mypy) |
| 6b metaclass `A \| B` | ty NOT_BUG | duplicate ty#4683 | no |
| 7 recursive TVT-default alias reveal | NOT_BUG (mypy prints `...`, no narrowing on assignment) | duplicate mypy#2008 | no |
| 8a `__hash__` None reveal | NOT_BUG (reachability effect) | duplicate mypy#20230 | no |
| 8b `Hashable` accepts class with `__eq__` and no `__hash__` | ty BUG (FALSE_NEGATIVE, 0.7) | NEW, none found | yes (ty) |

Result: 4 new-bug drafts (C2, 1b, 6a, 8b), none filed. Round-3 "strong" evidence for IntEnum alias and recursive alias was an artefact
(literal identity, recursive-alias printer), so neither is a bug. 

**ty#4656** (Self parameter not enforced on inherited methods, reported by the authors): closed "not planned" 2026-10-05; ty#4673 closed as
duplicate 2026-10-05; ty#4849 closed as duplicate 2026-10-28 (carljm: intentional). Outcome: design difference, not a bug. The pipeline
already dismisses these as DESIGN_DIVERGENCE (`kb:TY-SELF-UPPER-BOUND`); only wording and data changed (`known_upstream.json`,
`kb.py`, README, seeds/README, DESIGN §8). Commits 074ceb4, adead10.

**Flaky test** `test_timeout_kills_grandchild`: not reproduced before the fix (30/30 with 4 burners, 30/30 with 72 burners on 24 cores).
After a first rewrite 1/30 failed under load because `_alive()` raised ProcessLookupError reading `/proc/<pid>/stat`. Test-only fix
(timeout 1 s to 5 s, atomic pidfile write, polling with 30 s deadlines, tolerant `_alive`, cleanup in `finally`); production `_exec` unchanged.
After the fix: 30/30 under 4 burners, 3/3 full suites at 360 passed. Commit 1c3cd05. A full-suite run at the end of this report is in section 6.

## 1. Run setup

The round verified the 14 Round-3 candidates on the pinned and the newest tool versions, promoted 8 generated programs into `seeds/parents/`, added 2 `known_upstream.json` entries, replayed the Round-3 reports under the final KB, wrote 246 variants through the file bridge in three passes, judged them with `TYPEDIFF_LLM=null` and triaged the result. Final checks of the round: 373 tests passed, kb-selftest 21 PASS, 0 FAIL.

## 2. Funnel, Round 3 vs Round 4

Round-3 figures are from `results/rounds/round-3-report.md` section 2. Round-4 figures are from the stored reports.

| Measure | Round 3 | Round 4 |
|---|---|---|
| parents in `seeds/parents/` | 32 (40 distinct parent files used) | 49 `.py` files after promotion (+8) and 2 dropped as near-duplicates; 49 distinct mutated parents used; 50 fresh programs (P3) |
| prompts (pass 0) | 161 `*.prompt.md` | 246 at pass 0. The inbox now holds 270 `*.prompt.md` and 271 `*.answer.json` (24 and 25 more than 246; cause not traced, section 7) |
| programs written | 160 | 246 (196 mutated, 50 fresh; 19 area dirs, counts below) |
| preflight rejections at generation | not logged | 25 (pass 1 `pending=25`; 25 retry prompts), all resolved in pass 2 |
| programs run | 160 | 246 (`{'ok': 246}`, 77 s, `--jobs 14`) |
| discrepancies | 50 | 175 |
| tool crashes | 18 (14 programs) | 40 (33 programs): ty SIGABRT stack overflow 17, mypy SIGSEGV 16, ty salsa panic 6, pyright RangeError 1 |
| auto-closed (dismissed) | 20 | 73: DUPLICATE 59, DESIGN_DIVERGENCE 12, KNOWN_LIMITATION 2 |
| auto-closed by crash rules | 12 (`rule:crash:signal`) | 24: `rule:crash:signal` 22, `rule:crash:panic` 2 |
| auto-closed by upstream entries | 5 (MYPY-20969 x2, MYPY-22339 x2, TY-4884-REVEAL x1) | 35: TY-876 12, MYPY-20969 7, MYPY-20969-REVEAL 4, TY-4884 4, TY-4884-REVEAL 3, MYPY-22339 3, MYPY-21937 1, TY-876-ARGTYPE 1 |
| auto-closed by other KB entries | 3 (BOTH-GRADUAL, LITERAL-WIDENING, TY-CALLABLE-DUNDER) | 14: PRECISION-RUNTIME-CONSISTENT 10, INFERENCE-DOWNSTREAM 1, MYPY-13807-ALIASED-CONDITIONS 1, JOIN-VS-UNION 1, LITERAL-WIDENING 1 |
| live | 48 | **142** (126 non-crash + 16 crash) |
| live by kind | reveal_mismatch 23, only_mypy 10, only_ty 8, crash 6, reveal_unpaired 1 | reveal_mismatch 53, only_mypy 49, only_ty 13, crash 16, reveal_unpaired 11 |
| programs with a live finding | 41 | 83 |

Check: 175 discrepancies + 40 crashes = 215 findings = 142 live + 73 dismissed. Dismissals by entry type, from the `dismissed by entry` statistics: crash rules 24 + upstream entries 35 + other KB entries 14 = 73.

Round 4's live count is higher mainly because the run is larger and its parents include crash and bug reproducers promoted on Round-4
the first half of the round (many programs are variants of the Round-4 verification candidates). Per-program rates are the fair comparison (computed here):

| Rate | Round 3 | Round 4 |
|---|---|---|
| discrepancies per program | 50 / 160 = 0.31 | 175 / 246 = 0.71 |
| tool crashes per program | 18 / 160 = 0.11 | 40 / 246 = 0.16 |
| programs with a crash | 14 / 160 = 8.8 % | 33 / 246 = 13.4 % |
| live findings per program | 48 / 160 = 0.30 | 142 / 246 = 0.58 |
| non-crash live per program | 42 / 160 = 0.26 | 126 / 246 = 0.51 |
| programs with a live finding | 41 / 160 = 25.6 % | 83 / 246 = 33.7 % |
| share of findings auto-closed | 20 / 68 = 29.4 % | 73 / 215 = 34.0 % |

Per program the Round-4 run produced about twice as many live findings (0.58 vs 0.30). Part of the difference is the seeding: 49 parents from
Round 3 and Round 4 that were chosen because they disagree or crash, and 50 fresh programs in 5 areas. The closure share rose only from 29.4 % to 34.0 %,
so the review queue grew almost in proportion to the program count times 2.

Programs per area directory: enums_literals 38, callables 24, narrowing_user 20, protocols 18, constructors_metaclasses 16,
inheritance_mro 16, typevartuple_unpack 14, generics_variance 12, narrowing_builtin 12, tuples_unpacking 12, dataclasses 10, overloads 10,
descriptors_properties 8, paramspec_concatenate 8, async_generators 4, gradual_any 4, self_classmethods 4, typeddict 4, recursive_aliases 12
(sum 246). Live findings split by Round-4 verification family (assigned by parent file name, so this is a first grouping):

| Family (by parent) | Live | Dismissed | Programs with a live finding |
|---|---|---|---|
| 5 IntEnum alias (not a bug) | 18 | 1 | 7 |
| 1a stale alias (ty#2792 / mypy#13807) | 13 | 4 | 8 |
| 2 tuple-subclass fold (ty#2171) | 11 | 1 | 6 |
| 4 Flag `Never` (ty#876) | 10 | 15 | 4 |
| 6a/6b metaclass reflected operator | 10 | 0 | 5 |
| 7 recursive alias `...` (not a bug) | 10 | 0 | 5 |
| C3 `partial \| None` loop panic (fixed ty 0.0.85) | 6 | 0 | 6 |
| C1 self-referential `__call__` (ty#4148, mypy#22361) | 6 | 8 | 3 |
| 1b alias loop back edge (NEW) | 5 | 0 | 1 |
| 3 attribute narrowing / read-only property (ty#2792) | 5 | 0 | 3 |
| C2 protocol flatten (NEW) | 5 | 0 | 5 |
| 8b Hashable / `__hash__` None | 4 | 0 | 4 |
| no Round-4 verification family | 39 | 44 | 26 |
| total | 142 | 73 | |

(Live column: 18+13+11+10+10+10+6+6+5+5+5+4+39 = 142. Dismissed column: 1+4+1+15+0+0+0+8+0+0+0+0+44 = 73.)

## 3. Top patterns (first impressions, NOT bug classifications)

`typediff triage --top 30` returned 29 patterns for 142 findings. "Strong" = the pipeline attached CPython runtime or stack-trace evidence that supports a bug.
Every row is **for human triage**; no verification checklist was run here. Columns on the right say how it relates to the Round-4 verification.

| # | Pattern (findings, strong) | First impression | Relation to the Round-4 verification / existing entries |
|---|---|---|---|
| 1 | reveal_mismatch / ty_more_precise (20, 16): `reveal_type(a.x)` ty `int`, runtime `None`; `~F.R` ty `Literal[F.R]`, runtime `F.W` | ty narrowing outlives a reassignment/mutation | variants of 1a/1b (stale alias, `d4p_narrowing_stale_alias_loop`) and of Flag (ty#876); both already assessed in the Round-4 verification. Which of ty#2792 and the new 1b a given program shows is not separated |
| 2 | reveal_mismatch / different (21, 13): recursive-alias dots, `Integer.TRUE`, `gen7_a8725dda.py` (`tuple[int, str]` vs `tuple[object, ...]`) | first two are known non-bugs | recursive alias (verification item #7, mypy#2008) and IntEnum alias (#5, mypy#16830/#21117). The `gen7` TypeVarTuple concatenation is **not** explained by the Round-4 verification (section 4) |
| 3 | crash / ty:signal-SIGABRT:stack-overflow (8, 8): `d3p_self_classmethods_self_call_union__mut1_e3936d2f`, `d4v_protocols_expanding_self_receiver` x2 shown | ty stack overflow | 5 findings are C2 variants (new bug draft); 3 are C1 variants (ty#4148 family). The `rule:crash:signal` dedupe did not close them |
| 4 | crash / ty:panic salsa `execute.rs:751:9` (4, 4) | "too many cycle iterations" | C3 variants: ty 0.0.84 only, fixed in 0.0.85 (the Round-4 verification). |
| 5 | crash / mypy:signal-SIGSEGV (3, 3) | mypy segfault | C1 variants (mypy#22361 family). `MYPY-22361` closed none of them in this run |
| 6 | only_mypy / misc read-only property (3, 3): `d4v_ty_attr_eq_narrow_unreachable` | ty infers `Never` at a read-only assignment | verification item #3: ty#2792 (stale attribute narrowing). Variant, covered by a duplicate, but left live by design (must-stay-live calibration) |
| 7 | only_ty / type-assertion-failure (2, 2): tuple-subclass fold | ty `Literal[False]`, runtime `bool` | verification item #2: ty#2171, design difference |
| 8 | reveal_mismatch / uncomparable (7, 1): metaclass `A \| B` | mypy `Literal['left']`, runtime `'right'` | the Round-4 verification 6a (mypy bug, draft) and 6b (ty#4683). The other 6 are display differences |
| 9 | only_mypy / assert-type (6, 1) | mypy `Literal[True]` and `int` vs `str` | tuple fold (ty#2171) and 6a (mypy metaclass operator, new draft) |
| 10 | crash / pyright:internal:RangeError (1, 1): `d3p_descriptors_decorated_get__mut1_17c68570.py` | pyright stack overflow in `typeUtils.ts` | **neither**: matches no entry and no Round-4 verification candidate (section 4) |
| 11 | reveal_unpaired (11, 0): `d4v_ty_flag_or_else_never` | mypy prints nothing, ty `F & ~Literal[F.R] & ~Literal[F.W]` | Flag family (ty#876); hint REACHABILITY-VS-COVERAGE |
| 12 | only_mypy / arg-type (9, 0): `assert_never(Literal[E.B])`, `classmethod(...)` | mypy enum alias false positives | IntEnum alias (mypy#16830/#21117); `classmethod` row from C3 parent |
| 13 | only_mypy / operator (9, 0): `d4v_ty_alias_loop_backedge` | mypy `None + int` where ty is silent | 1b (new ty bug draft): this is the mypy view of the same programs |
| 14 | reveal_mismatch / gradual (5, 0): overloads `Any` vs `Unknown` | gradual type display | neither; noise class |
| 15 | only_mypy / overload-overlap (4, 0): `gen5_f7a2ebdd.py`, `gen6_f95d31ec.py` | mypy overlap check that ty lacks | neither; hint TY-CHECK-MISSING-JUDGE-MYPY |
| 16 | only_mypy / assignment (4, 0) | enum alias and metaclass `A * B` assigned to `str` | IntEnum alias and 6a |
| 17 | only_mypy / override return type (4, 0): metaclass `__or__` | mypy override vs `type.__or__` | STUB-SKEW hint; 6a/6b family |
| 18 | only_ty / unsupported-operator (3, 0): `d3p_narrowing_user_index_assign_stale` | ty reports `None + 1` after index assignment | neither as a verified item; related to MYPY-20969 (the mypy side of the same parent was closed 7+4 times) |
| 19 | only_ty / invalid-argument-type (3, 0): `need(obj)` expects `Hashable`, found `Plain \| Mutable` | ty rejects the mutable member, mypy accepts | 8b family (`Hashable`, `__eq__` without `__hash__`); here ty rejects, so the shown side is the mypy gap (mypy#20230) |
| 20 | only_mypy / return-value (3, 0): `return (*a, *b)` | mypy `tuple[object, ...]` vs `tuple[*Ts]` | same TypeVarTuple concatenation as pattern 2 `gen7`; **not** explained by the Round-4 verification |
| 21 to 29 | invalid-generic-class (2), union-attr (2), attr-defined (2), variadic-unpack misc (1), invalid-return-type (1), unresolved-attribute (1), override signature (1), has-type (1), invalid-method-override (1); none strong | mostly stub-skew, GRADUAL-OPERAND and PARTIAL-TYPES hints | none; `invalid-generic-class` (`type("Mixed", (IntBase, StrBase), {})`, seed 2d4bcd20aac0) is the only one with a plausible mypy gap |

Which patterns are covered by `rule:crash:signal`: the dedupe removed 22 crash findings (and `rule:crash:panic` 2) from the queue. They never appear in the
table above. Section 6 breaks them down. Patterns 1 to 9, 12, 13, 16 to 19 are variants of the four verified new bugs or of already-filed or
already-known items. Patterns 10, 14, 15, 20 and 21 to 29 are neither.

The already-filed issues named in the task (ty#4898, #4899, #4900, mypy#22360, #22361) were not searched for again here. `MYPY-22361` is the entry
for the C1 mypy crash family; the other four are not read in this report (section 7).

## 4. Candidates with strong evidence NOT explained by the Round-4 verification (all UNVERIFIED)

None of these is a "CPython crash + silent checkers" case: CPython ran to success in all 246 programs.

| Candidate | Evidence | Report |
|---|---|---|
| pyright RangeError "Maximum call stack size exceeded" in `typeUtils.ts` (pyright 1.1.414) on a descriptor whose `__get__` and `__set__` are decorated with a plain function defined in the class body | crash signature `pyright:internal:RangeError`, `rule:crash:internal_error`, live; matches no entry, no Round-4 verification candidate | seed-947242212886 |
| mypy TypeVarTuple concatenation `join(a: tuple[*Ts], b: tuple[*Us]) -> tuple[*Ts, *Us]` with `return (*a, *b)` | mypy reveals `tuple[int, str]` for `join((1, "x"), (2.5,))`, runtime value `(1, 'x', 2.5)`; mypy also reports `[return-value] got tuple[object, ...], expected tuple[*Ts]`; ty reveals `tuple[object, ...]` | seed-7448e0c4c99f; related: seed-8176b83d0a7d (`gen3_504999f8.py`, `tuple[*Left]`) |
| ty salsa panic (`execute.rs:751:9`, same signature as C3) in two programs that are not C3 variants by parent | dismissed by `rule:crash:panic` only | seed-81b29558828f; seed-32e61dbea91a. Whether they contain a `partial \| None` loop or are a different trigger is not checked |
| mypy missing a check that ty makes: `type("Mixed", (IntBase, StrBase), {})` with `Container[int]` and `Container[str]` bases | ty `invalid-generic-class`, mypy silent; CPython runs fine | seed-2d4bcd20aac0; `constructors_metaclasses/*type_call_generic_base__mut0_1ff6bc79.py`. Possibly a known mypy gap; no search made |
| C1-family programs that stay live although `TY-4148` and `MYPY-22361` exist | `d4v_callables_mutual_call_attr` (seeds 6e1aafbae77b, bf0eb5293b88) and `d3p_self_classmethods_self_call_union__mut1_e3936d2f` (seed-13ae8bc04894) crash ty and mypy, but none of the three was closed by `kb:UPSTREAM-TY-4148` or `kb:UPSTREAM-MYPY-22361` (neither appears in `dismissed by entry`) | not a new bug; an entry gap: the entry conditions (e.g. TY-4148 `requires call_attr_own_type`) do not match these shapes. Why is not checked |

The 5 C2 programs (seeds 828f18e26dd0, 9772b1db20b6, 4550a3778719, 6af4a0e947c7, 7e0097f1eb45) are variants of the verified new bug C2 and are not listed
as new candidates. The 4 live ty panics (seeds 00550e0697ae, 97094f3481d4, 2b3d96603864, c11c643b4f80) are C3 and are fixed in ty 0.0.85.

## 5. Programs proposed as parents for Round 5

Copy with the 3 header lines (`# area:`, `# hypothesis:`, `# origin:`); run `scripts/check_hits.py` before use.

1. Generated program (not kept): only program with the pyright RangeError signature.
2. Generated program (not kept): mypy reveal drops the second operand of a TypeVarTuple concatenation (runtime 3 elements). Also `gen3_504999f8.py` as a variant only if it differs after reading.
3. Generated program (not kept): ty salsa panic on an enum-parent mutant; check whether the trigger is new.
4. Generated program (not kept): crashes ty and mypy and survives the C1 entries; useful as a regression test for the entry gap rather than as a mutation parent.
5. Generated program (not kept) with seed 2d4bcd20aac0 (`type_call_generic_base__mut0_1ff6bc79`): mypy gap on conflicting generic bases built with `type()`.

Not proposed: variants of C2, 1b, 6a, 8b (their `d4v_*` parents are already in `seeds/parents/`), C1 and C3 variants, IntEnum alias and recursive alias programs
(not bugs), and programs whose only evidence is stub-skew or gradual display.

## 6. Pipeline findings

Worked:
- Variants fix: `generate --n 2` gives distinct filenames and cache keys (fix `dc51a60`). For `feature_crossover` the prompt bodies are still identical (see Broke).
- The inbox check script ran in about 1 s and is idempotent. Three passes took the inbox from pending=246 to 25 to 0.
- Judge: 246 programs in 77 s with `--jobs 14`, `{'ok': 246}`, no runner errors. Round 3 needed 43 s for 160 programs (0.27 s vs 0.31 s per program).
- Memory guard and process-group kill: `journalctl -u systemd-oomd --since -10h --no-pager | grep -c Marked` returned **0** (oomd kills in the last 10 h). No orphan `pyright` processes at report time (`ps aux | grep -c '[p]yright'` returned 0).
- Preflight lint at generation caught 25 of 246 answers before they were written (10.2 %), and all were replaced in one retry round.
- Crash dedupe keeps the queue small: 24 of 40 crash findings (60 %) were closed by `rule:crash:signal` (22) or `rule:crash:panic` (2).

Broke / rough:
- The first Round-4 workflow's gen-pass step failed because its shell tool returned garbled or stale output and one call timed out at 15 minutes. The saved script itself takes about 1 s. The same shell problem occurred in this step: commands printed a different working directory and the pasted heredoc did not create the script, so all scripts were written with the file tool and their output was read from files.
- A consolidate step died with a TLS error (network); the consolidate was redone (commit 3383e2f). Also the first `gh` call at setup failed with "network unreachable" and succeeded on retry.
- `--n 2` for `feature_crossover`: 98 prompts but 49 unique bodies (pairs byte-identical), because the seed is not in the prompt text. Non-crossover prompts: 148 files, 103 unique. Total 246 prompts, 152 unique bodies. So 94 prompts (246 - 152) carry no new information for the model. Recommendation: add a "variant k of n" line to the prompt (Round 5).
- Inbox accounting: 270 prompt files and 271 answer files for 246 programs. Not traced.
- `rule:crash:signal` dedupe hides same-signature bugs. This run: 22 closures. 8 of the 22 are the C1 family (`d3p_callables_self_call_attr` 2, `d3p_self_classmethods_self_call_union` 4, `d4v_callables_mutual_call_attr` 2), where the underlying issues (ty#4148, mypy#22361) are known. The other 14 are not explained by any Round-4 verification candidate: `d3p_generics_contravariant_recursive_base` 4 (mypy), `d3p_generics_typevar_default_refers_to_itself` 3 (mypy), `d3p_recursive_aliases_type_of_self_alias` 2 (mypy), `d3p_paramspec_identity_applied_to_itself` 3 (ty), `d3p_protocols_generic_protocol_stack_overflow` 2 (ty). Only the signature string is compared, so those 14 could hide a distinct bug (they were not read). In the same run 3 programs of the C1 family stayed live because they matched neither the rule nor an entry, while 4 programs of the same family were closed. That is inconsistent behaviour for one bug, and neither `TY-4148` nor `MYPY-22361` closed any finding.
- `rule:crash:panic` closed 2 salsa panics (the same signature as C3, which is fixed in ty 0.0.85) in an enum-parent program and a paramspec program. On the newest ty those two would not show up; on the pinned ty they hide whether these are separate triggers.
- Round-3 note still holds: the `rule:crash:signal` dedupe does not look at the program, only the signature.

Recommendations:
1. Pass `variant k of n` into the generation prompt and de-duplicate identical prompt bodies before asking for answers (saves up to 94 answers of 246).
2. Make `rule:crash:signal` require either a named entry or a first-seen record, and log the closing reference, so same-signature closures can be audited. Quantified need: 22 closures per run, 14 with no Round-4 verification explanation.
3. Re-check why the C1 shapes `mutual_call_attr` and `self_call_union__mut1` do not match `TY-4148` and `MYPY-22361` (loosen the `requires` condition or add a rule on the `__call__` self-reference).
4. Bump the ty pin (0.0.84 -> 0.0.97) before Round 5: C3 disappears, which removes 4 live crash findings and 2 `rule:crash:panic` closures.
5. Keep the saved-script protocol and write step scripts with the file tool, not shell heredocs.

Final checks at report time (real results, run by this step):

- `.venv/bin/python -m pytest tests -q`: **373 passed in 59.72s**, exit 0 (single full run; no flaky failure seen in this run, `test_timeout_kills_grandchild` included).
- `.venv/bin/typediff --python-version 3.13 kb-selftest`: **21 PASS, 0 FAIL**, exit 0.

## 7. Not verified

- Every candidate in sections 3 to 5 is unverified: no verification checklist, no reduction, no run on newer tool releases, no duplicate search (`gh` was not run in this step).
- The already-filed issues ty#4898, #4899, #4900 and mypy#22360 were not read in this step; mapping to patterns is by the pipeline hints and the Round-4 verification files only. The `MYPY-22361` entry relation comes from the Round-4 verification.
- Family assignment in section 2 is by parent file name, not by reading each program; a mutant may show a different effect than its parent.
- Why the three C1-shaped programs stayed live (entry conditions), and whether the 14 non-Round-4 verification `rule:crash:signal` closures are true duplicates.
- Whether the intenum and paramspec salsa panics are the C3 trigger or a different one (same panic location only).
- Why the inbox holds 270 prompts and 271 answers for 246 programs.
- The 25 preflight rejections: their reasons were not collected; only the retry count is logged.
- The three Haiku answer branches and the retry step were not reviewed for answer quality beyond the preflight.
- The pyright RangeError and the TypeVarTuple concatenation were read from the report and the program only; not reduced, not rerun on newer releases.
- The counts of live findings per family come from a one-off script (not kept); the script reads the judge output, which is git-ignored.
- oomd count covers the last 10 h only and does not prove that no memory-pressure event happened earlier.
- Round-3 per-program rates use the Round-3 report figures (e.g. 18 tool crashes in 14 programs) without recomputation.
