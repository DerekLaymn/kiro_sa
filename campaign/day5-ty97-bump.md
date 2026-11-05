# Day 5: ty pin bump 0.0.84 -> 0.0.97

Branch `campaign/day5-p2`, local only, nothing pushed. mypy 2.4.0 and pyright 1.1.414 unchanged.

## Files changed

| file | change |
|---|---|
| `.venv` (not tracked) | `uv pip install ty==0.0.97`; the install replaced the memguard shim, so `ty.real` was deleted and `~/.config/kiro-hooks/install_guard.sh` re-run. `.venv/bin/ty --version` prints `ty 0.0.97`, `.venv/bin/ty` is the shim script again (`file` says Bourne-Again shell script), `ty.real` is the 0.0.97 binary. |
| `README.md`, `FUZZING_PLAN.md` | install commands now `ty==0.0.97`; the "pinned for the whole campaign" assumption names 0.0.97 and links this note; the playground hint says 0.0.97. |
| `typediff/data/known_upstream.json` | TY-4883, TY-4884, TY-4884-REVEAL, TY-4884-ASSERT: notes say FIXED in ty 0.0.97. TY-4884's `example` key was renamed `example_pre_0_0_97` so `kb-selftest` stops expecting it to fire. |
| `scripts/upstream_day3_check.py` | expectations for `ty_TA_depth24`, the three TY-4884 programs and `probe-bug05-typeddict-variants` now match 0.0.97 behavior (no finding, or no closing entry). |

There is no pin in `pyproject.toml` (it lists `ty` unpinned), and no requirements or lock file exists.
Not changed on purpose: historical measurement text that states results *on 0.0.84*
(`calibration/RESULTS.md`, `seeds/README.md`, `examples/.../FINDINGS.md`, `docs/kb-loop-*.md`, `campaign/day*` notes,
`typediff_out/`, `.agents/`, comments in `kb.py`/`parsers.py`, `ty_rule_map.json` "_derived_for", `seeds/harvested/PROVENANCE.json`).
These describe what was measured, not the current pin. Not regenerated: `ty_rule_map.json` (still derived for 0.0.84; unverified whether 0.0.97 changed rules).

## Tests

| check | baseline | after bump |
|---|---|---|
| `pytest tests -q` | 422 passed | 422 passed (run after the bump, and again after the KB edits) |
| `typediff kb-selftest` | 21 PASS | 20 PASS, 0 FAIL after the edit. Before the edit: 20 PASS, 1 FAIL (`UPSTREAM-TY-4884`, no longer fires because ty 0.0.97 solves the TypeVar). |
| `scripts/upstream_day3_check.py` (every file in `tests/data/upstream_day3`) | not run before | 12 violations on 0.0.97; 8 of them were 0.0.97-dependent (TY-4883/4884, fixed above). The other 4 (`A1` and `A4` ty crash closed by TY-4148, `probe-bug02-flag-operators` D5, `probe-bug06-flag-param-and-local` D2 closed by MYPY-21937-REVEAL) also occur on ty 0.0.84 (checked with a separate 0.0.84 venv, `TYPEDIFF_TY`), so they come from the Day-5 matcher broadening, not from this bump. Left as is; the script's comments for them are stale. |

## KB changes (known_upstream)

Each ty-specific entry was re-run on 0.0.97 (reproducers in `tests/data/upstream_day3|4|5`, plus the day3 check above).

| entry | 0.0.97 result | action |
|---|---|---|
| TY-4883 (nested tuple alias compare, timeout) | `ty_TA_depth24` finishes in 0.06 s, "All checks passed" (0.0.84: >120 s timeout) | marked fixed in 0.0.97, kept for stored <=0.0.84 runs |
| TY-4884, -REVEAL, -ASSERT (generic TypedDict TypeVar unknown) | `first(a)` is `int`, bad assignments reported | marked fixed in 0.0.97, kept for stored runs; example parked |
| TY-4882 (protocol stack overflow) | still SIGABRT stack overflow (`ty_TB`, `t20a`, `ty_20`) | unchanged (note says 0.0.84) |
| TY-4898 (ParamSpec `id(id)`) | still overflows (`C1`, `C3`) | unchanged |
| TY-4148 (`__call__` self attribute) | still overflows on all day4/day5 reproducers | unchanged (already says 0.0.84 and 0.0.97) |
| TY-4899 (`Callable[P, T]` OOM) | still SIGKILL under the 4 GB guard (`E1`, `E2`, `E6`, `E10`); `E8` still hits the salsa cycle panic | unchanged |
| TY-4900 (expanding base) | still overflows (`D1`, `D7`, `D10`, `D11`) | unchanged |
| TY-876, -ASSERT, -ARGTYPE (Flag expansion) | still dismissed by these entries | unchanged |
| TY-1090, TY-4212, TY-2255 (no `example`, no ty-version text) | not re-verified individually | unchanged, unverified |

The `partial | None` loop panic (salsa `too many cycle iterations`, `execute.rs:751`) is gone in the 250-program run: all 8 occurrences disappeared. It had no `known_upstream` entry (it was a live crash finding), so no KB edit.
The claim "fixed in 0.0.85" comes from `docs/kb-loop-candidates.md`; I did not bisect, I only observed it is gone on 0.0.97.

## Re-judge of the Day-5 corpus (250 programs, ty 0.0.97)

Command: `TYPEDIFF_LLM=null .venv/bin/python scripts/kbloop_run.py runs/day5/out97 runs/day5/gen --jobs 14 ...` (63 s, 250 ok, `--jobs 14`). The comparison base is `runs/day5/replay` (the same KB, stored 0.0.84 outputs; 110 live), because `runs/day5/out` is the pre-morning-KB run (136 live).

| metric | Day 5 (0.0.84, morning KB) | 0.0.97 re-judge |
|---|---|---|
| programs | 250 | 250 |
| discrepancies | 154 | 155 |
| tool crashes | 42 | 34 |
| live findings | 110 | 110 |
| dismissed findings | 86 | 79 |
| programs with live findings | 87 | 84 |
| live crash findings | 18 (8 ty stack overflow, 8 ty salsa panic, 2 pyright) | 10 (8 ty stack overflow, 2 pyright) |
| ty crashes (any tier) | 29 (21 overflow, 8 panic) | 21 (all overflow) |
| mypy+pyright crashes | 13 | 13 |

14 of 250 programs changed. What disappeared (ty-involving):
- 8 findings closed by TY-4884 / -REVEAL (3 programs: 0aa9c678..., 74a014e8..., 83c0e90b...). All were already dismissed.
- 8 live ty salsa-panic crash findings, one in each of 8 programs (`16f87fbf`, `42e53ad8`, `456b0e25`, `6c63c46a`, `b289ab08`, `d13d9e4d`, `d53850b2`, `e0555707`). In `d13d9e4d` the program now gets a dismissed finding under `TY-CHECK-NOT-IMPLEMENTED`; in `42e53ad8` and `b289ab08` nothing remains.
- The total of 110 live is equal by coincidence: 8 crash findings left, 8 new live reveal findings appeared (below).

Still present and unchanged: 21 ty stack-overflow crashes (7 closed by TY-4148, 4 by TY-4898, 2 by TY-4882, 8 live). No new crash signature.

## New candidates (live findings that differ from Day 5)

1. 5 programs (`16f87fbf`, `456b0e25`, `6c63c46a`, `d53850b2`, `e0555707`), 8 `reveal_mismatch` findings on `reveal_type(value)` after `value = value | None` / `None | value` in a loop over a `partial` or `staticmethod` object. ty used to panic; now it reveals `partial[(x: int) -> int] | Unknown`. mypy reveals `partial[int]`, pyright reveals `partial[int] | Unknown`. ty and pyright agree and the statement itself is a runtime TypeError, so this reads as error-recovery noise, not a new bug. I did not add a KB entry for it (product decision for the triage owner).
2. `adbc14c6128a` (possible regression, needs a human check): `class Callback[*Ts, **P = [bool]]` raises `TypeError: Type parameter with a default follows TypeVarTuple` on CPython 3.13.16 (verified by running the program). ty 0.0.84 reported `invalid-type-variable-default` on it; ty 0.0.97 says "All checks passed". mypy only complains at the use site. Not searched upstream, so it may already be reported or intended.
3. `b526cf0d`, `e4a15621` (improvement, not a bug): `class Pack(Generic[*Ts, D])` with a defaulted `TypeVar` after a `TypeVarTuple` now gets `invalid-type-variable-default` from ty 0.0.97 (0.0.84 was silent). All three checkers now error, the finding becomes `concern_mismatch` (different codes).

No other new ty-related live findings.

## OOM

`journalctl --user` and `journalctl` from the run start (19:57) were grepped for `oomd`, `Marked`, `oom-kill`, `killed process`: no matching lines. I did not separately confirm the journal was readable. The run used `--jobs 14` and all ty calls went through the memguard shim. `E1`/`E2`/`E6`/`E10` (TY-4899) are still killed by the 4 GB per-call cap with exit 137, as designed.

## Recommendation

Proceed with Day 6, with these conditions:
- The bump is safe for the pipeline: tests 422 pass, selftest 20 PASS, 250-program re-judge is clean, no OOM, no new crash signature.
- Day 6 focus: (a) keep the crash lead families (TY-4148 variants, protocol-flatten overflow, TY-4899), since all still reproduce on 0.0.97; (b) look at candidate 2 (ParamSpec default after `*Ts` now accepted by ty) before filing anything, and check upstream first; (c) stop spending generation on TypedDict-TypeVar solving and `partial | None` loops, both are fixed on 0.0.97.
- Before filing any ty bug, re-verify it on 0.0.97 (several Day 3-5 notes still say "verified on 0.0.84"). The `ty_rule_map.json` and the 0.0.84 mentions in `kb.py`/`parsers.py` comments are stale but harmless.
- Day-6 seeds mutated from `runs/hits/` that depended on the TY-4884 or salsa-panic behavior will no longer produce those findings; this lowers the number of crash hits, it does not hide anything.

## Unverified

- Whether `ty_rule_map.json` rules changed in 0.0.97.
- Individual 0.0.97 behavior of TY-1090, TY-4212, TY-2255 and the `prior_stances`.
- Whether the Day-5 `docs/kb-loop-candidates.md` claim "fixed in 0.0.85" is accurate for each case; I only observed absence on 0.0.97.
- Whether candidate 2 is already reported upstream.
