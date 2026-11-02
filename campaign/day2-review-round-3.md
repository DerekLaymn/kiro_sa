# Stage 3 round 3: NameError policy, stale-alias guard, and REVEAL-ERROR-RECOVERY through a flagged binding

Round 3 (commits 10dd9b1, a4147b3, d924841, plus the 528bd1a log commit) resolves the three open reviewer items from round 2. NameError on a flagged name becomes strong evidence in both code paths and a hint-only `MYPY-UNBOUND-OPT-IN-CHECK` entry is added. `MYPY-13807-ALIASED-CONDITIONS` stops dismissing stale aliases. `REVEAL-ERROR-RECOVERY` now also fires when the same tool reported an error on an earlier statement that binds a name the revealed argument reads. Calibration reporting gains `must_stay_live` support. The only entry that closes more findings is `REVEAL-ERROR-RECOVERY` (76 newly dismissed, 54 tuning and 22 hold-out), and the audit below found none of them hides a real bug. The Plan target is far from met: against the Stage-2 baseline the queue is down 7.19% overall (7841 to 7277), 7.54% on tuning (6300 to 5825) and 5.78% on hold-out (1541 to 1452), and the target is more than 50% on both sets.

Watch for: (1) Plan target not met after three rounds, and the coder's own analysis says oracle-backed rules cannot reach it on this corpus, so the loop needs a user decision rather than another blind round (confirmed). (2) The new binding clause of `REVEAL-ERROR-RECOVERY` matches any earlier error on a statement that binds a name read by the reveal, without checking that the error caused the gradual type (possible, no false dismissal found in 76). (3) Some of the 76 chain through a binding error that is itself dismissed by `ANNOTATION-ONLY-READ` (likely).

**Verdict**: NEEDS_CHANGES

## High-level view

The NameError change aligns `rules.attach_runtime_evidence` with `kb.runtime_contradiction`: a CPython NameError or UnboundLocalError on the name the reporting tool flags is strong evidence, blamed on the silent tool. It moves no finding between live and dismissed. The new `MYPY-UNBOUND-OPT-IN-CHECK` entry is hint-only and is shown only when mypy reports the same name once `possibly-undefined` and `used-before-def` are enabled. Nothing is dismissed on the strength of it.

The stale-alias guard only narrows an existing dismissal: it re-opened 2 tuning findings and left hold-out unchanged, so it cannot introduce a new false dismissal.

The binding clause of `REVEAL-ERROR-RECOVERY` is the only new dismissal path. A gradual reveal (`Unknown` for ty, `Any` for mypy) is dismissed when the same tool reported an error on an earlier statement binding a name used in the reveal. The error itself stays a separate live finding. The runtime guard (any CPython exception on the reveal statement keeps it live) is intact, and none of the 76 has an exception on the reveal statement.

Calibration shows no newly dismissed real bug versus the round-2, round-1 and Stage-2 baselines (same 11 dismissed positives), 21 of 26 negatives close, and both `must_stay_live` programs stay live. Recorded evidence is 201 pytest passed and 15 of 15 `kb-selftest` PASS.

The queue did not move enough. After round 3 the remaining mass is reveal gradual (456 in tuning), uncomparable (444), different (403), `ty_more_precise` (299), and the `only_mypy` assignment and assert-type families. These need a per-construct oracle that does not exist, and Plan §7 forbids inventing dismissals.

<details>
<summary>Issues (7)</summary>

1. **Plan target not met (blocking, confirmed)** — queue shrank 7.19% overall, 7.54% tuning, 5.78% hold-out against a required more than 50% on both (tuning <= 3149, hold-out <= 770). Do not approve to end the loop.
2. **Loop cannot converge on the current approach (blocking, confirmed)** — rounds 1 and 2 together removed 6.25% of the queue and round 3 removed 1.01% more, and the coder's Plan §7 note states the remaining patterns have no deterministic oracle. Ask the user whether to keep the >50% target, restate it, or stop the loop with the current numbers and the documented pivot options.
3. **Binding clause does not check causality (possible)** — `_error_at_binding_of_reveal_arg` accepts any ERROR-severity diagnostic on an earlier statement that binds a name read in the reveal argument. A tool could report an unrelated error there (for example an argument error on a call whose return type is unannotated) while its gradual reveal comes from inference. No such row in the 76; add a negative test where the earlier error is unrelated to the binding's type, or require the reported error code to be one that yields a recovery type.
4. **Chained dismissal through a dismissed binding error (likely, minor)** — rows such as `mypy__check_optional__testNarrowingFromObjectToOptional` (D2) and `mypy__check_selftype__testSelfTypeGenericClassNoClashInstanceMethod` (D3) are closed by `REVEAL-ERROR-RECOVERY` because ty flagged the binding, and that binding error is itself dismissed by `ANNOTATION-ONLY-READ`. The mypy false negative stays tracked, but both rows are auto-closed, so no live finding remains for that program. Consider recording the chain in the finding notes.
5. **Sampler cannot list dismissed findings (confirmed, tooling)** — `scripts/kbloop_sample.py` skips `tier == dismissed`, so auditing a dismissal rule needs a custom script (the coder wrote `campaign/tmp/r3_*`, the reviewer wrote `campaign/tmp/review3-*`). Add a `--dismissed-by ENTRY` option so the Plan's audit step is reproducible.
6. **Strong bug evidence with no blamed tool (possible, minor)** — the NameError branch in `attach_runtime_evidence` emits `blame="unknown"` when both tools have diagnostics on the row. Add a test for that branch or avoid strong bug evidence without a blamed tool.
7. **Biggest remaining tuning patterns (informational for next round)** — reveal gradual 456, uncomparable 444, different 403, `ty_more_precise` 299, `only_mypy` [assignment] 197, `only_mypy` [assert-type] 197, `only_ty` [type-assertion-failure] 157, `only_ty` [unresolved-reference] 129 (145 of 163 mypy-silent rows are true mypy false negatives), `only_mypy` [arg-type] 118, `concern_mismatch` [assignment] 114. Ranked next options from the log: per-construct reasons for the 'clean' gradual rows, hint-only ORIGIN-MISMATCH for assert_type rows, filing the 145 mypy unbound false negatives and the ty class-before-def silence as candidates after a playground check.

</details>

<details>
<summary>Details</summary>

## Audit of REVEAL-ERROR-RECOVERY dismissals

I recomputed the transitions between `runs/day2/out2` and `runs/day2/out3` from the report JSON: 76 findings go live to dismissed, all by `kb:REVEAL-ERROR-RECOVERY` (ty side 49, mypy side 27), and 2 go dismissed to live. The count matches the log. I read a random sample of 20 with full context (seed 11, `campaign/tmp/review3-audit-new.txt`), then a one-line table of all 76 (`campaign/tmp/review3-all.txt`) and opened the programs whose pairing looked least obviously causal.

The sampled rows fall into three shapes. In the first, one tool rejects an unpacking, class base, metaclass, `type()` call or overload call, and the next reveals of those names return the tool's gradual recovery type while the other tool reveals a concrete type (`ty__unpacking__*`, `testInvalidVariableAsMetaclass`, `ty__call__type__37`, `ty__bidirectional__90`, `ty__bidirectional__78` D10 and D15). In the second, the earlier error is a reference to an undefined name (`testNewAnalyzerMetaclass1`, `testProtocolClassValDescriptor`, `ty__class__slots__34`), and CPython's NameError occurs at the binding line, not at the reveal. In the third, the earlier error is a divergence that is itself live: `ty__assignment__augmented__3` D5 follows mypy's `no-redef` and `operator` errors (both live), and `ty__call__type__24` follows mypy's `arg-type` error on `super(...)` (live). In every sampled row the separate error finding remains in the queue.

`ty__assignment__unbound__0` was the one row where the binding error could have been a one-sided report. I ran mypy 2.4.0 and ty on the same three lines: mypy reports `used-before-def` and ty reports `unresolved-reference` at line 1, so the error is agreed and only the reveal differs. Dismissal is sound.

No sampled or tabulated row has a CPython exception on the reveal statement itself (`crash_at_reveal=[]` over all 76). Exceptions occur at the binding line, in an unrelated earlier line, or not at all. Hold-out carries 22 of the 76 (29%), above its 20% corpus share, so the rule is not tuning-only.

The causality gap (issue 3) is a property of the matcher, not of any observed row. The matcher requires the reveal to be exactly `Unknown` or `Any` on one side and a non-gradual type on the other, which narrows the risk a lot, but a tool with an unannotated callee could produce `Unknown` for an unrelated reason in a statement that also carries an unrelated error. The new tests check wrong name, warning severity, other tool's error and compound-statement headers, but not an unrelated error on the same statement.

## NameError policy and the hint-only entry

`attach_runtime_evidence` previously recorded a NameError on a flagged name as neutral; it now records it as strong evidence blaming the silent tool, matching `kb.runtime_contradiction`. The user chose this explicitly after the coder's warning, so I treat it as settled. When both tools have diagnostics on the discrepancy, the reporter is undetermined and the evidence carries `blame="unknown"` while still strength strong and `supports="bug"`. The same `"unknown"` fallback already exists in the generic runtime branch, so this is consistent, though a gate consuming it will see strong bug evidence with no tool to blame in that case.

`ANNOTATION-ONLY-READ` keeps `runtime_override=False`, so the stronger evidence does not demote its dismissals. That was checked by `test_nameerror_policy_does_not_stop_the_tracked_limitation_entries_from_dismissing`. `REVEAL-ERROR-RECOVERY` is still demoted by a NameError at its statement.

`MYPY-UNBOUND-OPT-IN-CHECK` is `auto=False`, and `_verified_hints` adds its experiment as neutral evidence, so it cannot close anything. In the replay it moved zero findings. Of the 163 mypy-silent `unresolved-reference` rows, mypy reports the name with the opt-in checks in 18 and stays silent in 145. Those 145 stay live and are the strongest candidate set for upstream reports.

## Stale-alias guard on MYPY-13807

`_target_changed_between` requires that no store, import, def or class rebinding of the aliased root occurs between the alias assignment and the `if`, and that no call mentioning the root occurs for attribute and subscript targets. It can only re-open findings. Two tuning rows re-opened (`ty__narrow__aliased_conditions__30` and `__34`), hold-out is unchanged, and the new `must_stay_live/mypy_stale_alias.py` program guards the reviewer's repro. The 11 test cases cover the unchanged form and eight stale forms.

## Calibration and must_stay_live

`calibration.classify` returns `violated` for a `must_stay_live` program when any finding is dismissed, and `summarize` reports it separately without touching the positive or negative metrics. Round-3 calibration: positives identical to the Stage-2 baseline (117 kept, 61 invisible, 11 dismissed, 5 excluded), the same 11 dismissed positives, no newly dismissed real bug, 21 of 26 negatives closed, 2 of 2 must-stay-live programs live. Five negatives remain open (`kb-ANNOTATION-ONLY-READ`, `kb-JOIN-VS-UNION-CALLABLE`, `kb-MDTEST-TODO`, `kb-MYPY-15182-NEW-RETURNS`, `neg-generic_isinstance`), unchanged since earlier rounds.

## Process checks

Log entries carry plan labels that match the work (§3 P1 decide, §6 triage checklist, §3 P1 re-measure). The NameError decision was gated on the user. Queue numbers in the log (7277, 5825, 1452) match my independent recount from the `out3` reports. `git ls-files` contains nothing under `runs/`, `seeds/harvested` or `findings/2026-10-27-llm-run/`, and `-l` is untracked. No remote branch contains HEAD, no push in the reflog. Committed `campaign/tmp/*` are helper scripts, not run outputs.

## Test coverage

Every code change has a test in `tests/test_stage3_round3.py` (288 lines, plus edits to `test_evidence_fixA.py` and `test_stage3_round2.py`), covering both-tool NameError policy, hint-only behaviour (including real-tool toggle), stale-alias forms, binding-based recovery with real tools, calibration loader and classification. Recorded results: 201 passed, 15 of 15 kb-selftest PASS. Not tested: a binding error unrelated to the type of the bound name (issue 3), and the `blame="unknown"` branch when both tools have diagnostics on the NameError row.

</details>

<details>
<summary>File map</summary>

Full diff: `git diff 13aae01 HEAD`

- `typediff/kb.py`: `_error_at_binding_of_reveal_arg`, `_target_changed_between`, `_expr_root`, `MYPY-UNBOUND-OPT-IN-CHECK`, new `REVEAL-ERROR-RECOVERY` example and text
- `typediff/rules.py`: NameError strong evidence with blame, `_verified_hints`
- `typediff/calibration.py`, `typediff/cli.py`, `scripts/kbloop_calib_subset.py`: `must_stay_live` loader, classification and `--must-stay-live`
- `calibration/must_stay_live/mypy_stale_alias.py`, `calibration/negatives/reveal_error_recovery.py`: new guard program, pyright-independent negative
- `tests/test_stage3_round3.py`, `tests/test_evidence_fixA.py`, `tests/test_stage3_round2.py`: round-3 tests
- `campaign/`: log, `s3-r3-*` outputs, `tmp/r3*` helper scripts

</details>
