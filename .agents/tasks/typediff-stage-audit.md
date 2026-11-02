# typediff stage audit (quick, moderate depth)

Env: ty 0.0.84, mypy 2.4.0, host Python 3.14.7, target 3.12, no LLM, pyright not run. No source files were changed.
"Exec" = verified by running code. "Static" = read only.

## Per-stage status

| Stage | Files | Status |
|---|---|---|
| S0 crash detection | parsers.py, pipeline.py | BUGS (1 low-medium) |
| S2 parse / anchors / typenorm / concerns | parsers.py, anchors.py, typenorm.py, concerns.py | BUGS (3 low) |
| S1 validity gate | rules.py | OK (exec: syntax error, undefined-name paths not deeply probed) |
| S3 discrepancy extraction | discrepancy.py | OK, 1 gap (see 6). All 7 kinds reproduced (REVEAL_UNPAIRED, RUNTIME_MISS, REVEAL_MISMATCH, ONLY_* on real tools; CONCERN_MISMATCH, SEVERITY_ONLY on synthetic input) |
| S4 deterministic / KB / experiments / inhabit | rules.py, kb.py, experiments.py, inhabit.py | BUGS (2 medium) |
| S6 gate + citation check | adjudicator.py, corpus.py | UNVERIFIED (static only, as requested); 3 suspected issues |
| S7 reducer / report / dedup signature | reducer.py, report.py, dataset.py | OK, 1 low bug (apostrophe template) |
| S8 strategy / preflight / dataset | strategy.py, generator.py, dataset.py | BUGS (deviations from DESIGN section 6, low; preflight over-rejects) |
| S5 | adjudicator loop, llm.py, prompts.py | NOT TESTED (excluded) |

Existing checks: there is no tests/ dir or pytest config. `typediff kb-selftest`: 3/3 PASS (only 3 entries have examples). `typediff run examples/*.py`: all 3 ran. The first two closed as the README says, and self_param_unsound gives SELF_CONTRADICTION + RUNTIME_MISS in review. `typediff seeds seeds/`: 27 programs ran, 0 crashes, 0 LLM calls (one seed rejected by preflight for 3.13 syntax, which is expected for target 3.12).

## Confirmed bugs

1. **experiments.py:243 (used via kb.py `_toggle`), false-dismissal path. Severity: medium-high. Exec.**
   `config_toggle` never checks the tool's exit code or `crashed`. If the toggle run fails (unknown option after a ty upgrade, exit 2, zero diagnostics), the ty diagnostic "disappears" and the result is strong `not_bug` evidence.
   Repro: wrap ty so it exits 2 when it sees `strict-equality-semantics`, then run config_toggle on the TY-CALLABLE-DUNDER example (ONLY_TY). Normal run: persists=True, supports neutral. Failing run: persists=False, supports not_bug.
   Any ONLY_TY under eq/in/match narrowing would then be dismissed by TY-STRICT-EQUALITY. `kb-selftest` would not catch it, because that example is ONLY_MYPY.
   Fix: in config_toggle, treat exit code not in (0, 1) or any crash as `ok=False`, or require the toggled run to produce a parseable result.

2. **rules.py:128 and kb.py:109, probes mixed across reveals on the same statement line. Severity: medium. Exec.**
   `a = 1; b = 'x'` then `print(reveal_type(a), reveal_type(b))` on one line gives two runtime probes on one anchor. rules.py uses only the first probe (`break`) for every reveal and emits STRONG "bug" RUNTIME evidence: "value '1' does NOT inhabit mypy's revealed type str". That is false. kb.py `runtime_contradiction` loops over all probes at the anchor, so it wrongly blocks the LITERAL-WIDENING dismissal. Loop bodies or functions called more than once give several probes per line too.
   Fix: match a probe to a reveal by (line, column or order index) and check each tool's k-th reveal only against the k-th probe.

3. **parsers.py:48, false mypy crash. Severity: low-medium. Exec.**
   `"INTERNAL ERROR" in blob` matches user text echoed in a message. `x: Literal['INTERNAL ERROR']` with `reveal_type(x)` produced a CONFIRMED mypy crash (conf 0.99, `mypy:INTERNAL ERROR@unknown`) and skipped the rest of analysis.
   Fix: anchor the match to a line that starts with `<file>: error: INTERNAL ERROR` or require a traceback or exit code 2.

4. **typenorm.py:230, enum literal qualifier dropped. Severity: low. Exec.**
   `_canon` strips the module qualifier of every dotted name, so `Literal[A.X]` and `Literal[B.X]` both become `Literal[X]` and compare EQUAL. A real reveal discrepancy is hidden. `Literal[A.X]` vs `A` is "different" rather than "more precise", so enum literal widening is never recognised.
   Fix: do not strip dots inside Literal arguments.

5. **concerns.py:29, `"misc": "*"` wildcard. Severity: low. Exec (synthetic).**
   mypy `misc` pairs with any ty rule, so mypy [misc] vs ty `unresolved-attribute` on one statement yields no discrepancy at all. Same for pyright `reportGeneralTypeIssues`. It hides mismatches but never dismisses.

6. **S3 gap (discrepancy.py), duplicate diagnostics. Severity: low. Exec (synthetic).**
   Two identical mypy diagnostics vs one ty diagnostic give no discrepancy. DESIGN lists duplicate diagnostics as a DIAGNOSTIC_DEFECT symptom but S3 cannot extract them.

7. **strategy.py:144, PIVOT condition. Severity: low. Exec.**
   DESIGN says PIVOT when the last 5 cases "had no disagreement at all". Code uses `no_disc >= 4`. 4 no-disagreement + 1 review case pivots. `(kb_ids and len(kb_ids) <= 2)` also pivots on 4 unresolved-review cases + 1 case with a KB hit. Other thresholds match DESIGN: REPAIR at 2 of last 4 invalid, requires 4 cases; ABANDON at 6 or more cases and KNOWN_LIMITATION at 60% or more of dismissals with no confirmed (DESIGN gives no numbers); CONTINUE on confirmed or candidate.

8. **strategy.py:183, CONTINUE can be overridden. Severity: low. Static.**
   DESIGN section 6 lists CONTINUE among the hard rules the LLM can't override. Code's `hard` covers only PIVOT, ABANDON and REPAIR_GENERATOR. This only matters on the LLM path, which I did not run.

9. **parsers.py:331, "timeout" in plain text. Severity: low. Exec.**
   `parse_runtime("ok: done, no timeout here")` returns status=timeout. Only affects the raw-text runtime path, not the harness JSON.
   Related: a multi-line exception message makes exc_type `UnknownException`, so the exception is not classified as "strong". That is a safe direction (evidence is lost).

10. **dataset.py:15, `message_template`. Severity: low. Exec.**
    The quote regex `'[^']*'` mis-pairs apostrophes. "Can't find `x`; it's 'a'" becomes "can_s _ isn't ..." and leaks message text into the signature, so dedup can miss.

11. **generator.py `preflight` substring lint. Severity: low. Exec.**
    `"open("` matches `reopen(` and `my_open(`, and `input(` matches inside strings and comments, which gives blocking ERRORs on valid programs. `"threading"` matches any identifier that contains it. It misses `datetime.now`, `uuid` and `os.urandom`, which `rules._NONDETERMINISTIC` partly covers.

## Suspected, not confirmed

- **adjudicator.py:355, skeptic fails open (static).** If the skeptic LLM call is unavailable or invalid, the note is `SKEPTIC:UNAVAILABLE` and `opposed` is False, so a BUG with strong evidence and conf >= .85 can reach CONFIRMED with no skeptic pass. DESIGN requires a skeptic pass that did not argue it is intended. The same applies to the advocate (unavailable gives no REOPEN, so DISMISSED proceeds).
- **adjudicator.py `_verify_evidence` (static).** For KB evidence, "verified" is `kid in d.kb_hits`, and that includes hint-only (non-auto) entries. EXPERIMENT evidence is verified if the cited id exists, without checking what the experiment showed. An LLM can therefore cite a hint-only KB entry or any experiment id with supports=not_bug to meet the dismissal rule. This conflicts with "a dismissal needs a verifiable citation".
- **rules.py SEVERITY_ONLY (static and exec on synthetic).** `rule:severity-only` dismisses as NOISE with no evidence item, so it has no citation. The pairing is also loose (see bug 5).
- **kb.py `m_todo` (static).** With `runtime_override=False`, an ONLY_TY whose message contains `@Todo` is dismissed even when CPython raises a type exception at that statement, where mypy would then have a false negative.
- **RUNTIME_MISS masking (discrepancy.py, synthetic).** If any frame in the traceback is flagged (for example an outer call site flagged for an unrelated reason), RUNTIME_MISS is suppressed even though the innermost raising statement is unflagged. This matches the DESIGN wording but is likely too lenient.
- **Abnormal exit codes.** A ty or mypy exit code 2 with no panic text and no diagnostics is treated as "no errors", not a crash. With empty ty output, every mypy error would become ONLY_MYPY. Only ty exit 101 and panic text are handled. Not reproduced.
- **typenorm.py module stripping.** `a.Foo` vs `b.Foo` compare equal (Exec), so same-named classes from different modules are indistinguishable. By design, but it can hide a difference.
- **anchors.py.** Two statements joined by `;` on one line share one line mapping (the last wins). Multi-line calls, decorators and elif/except/case headers behaved correctly in the probes.
- **Reducer.** It terminates, preserves the discrepancy and respects max_tests. self_param_unsound reduced in about 38 s to 9 statements and the reduced program still shows ONLY_MYPY at `x.add(Node())`. Always-true, always-false and nested-block predicates also behaved. It keeps an unused `reveal_type` import.

## Checked and OK (exec)

- mypy text and JSON lines, ty concise and full, pyright JSON, traceback, ty panic (exit 101 or panic text) and mypy traceback or INTERNAL ERROR all parse. Line and column handling is correct (JSON columns 0-based +1).
- typenorm: Union/Optional/| ordering, Literal quoting and ordering, builtins. prefix, List/Dict aliases, Any vs Unknown gives gradual, invariant containers (list[int] vs list[bool]) give different, float/int promotion gives cosmetic, callable canonicalisation. No false EQUAL found besides bug 4.
- KB auto-dismissals observed are sensible: var-annotated, JOIN-VS-UNION, LITERAL-WIDENING, MYPY-SKIPS-UNREACHABLE, SUPPRESSION-SEMANTICS, STRICT-EQUALITY (toggle-verified), and the cascade rule.
- The dedup signature is stable across line numbers, names, digits and feature order, differs on feature change, and uses sha256 so it is stable across processes.
- Strategy thresholds other than those above match DESIGN (see 7). UCB1 picks an unplayed area first; there are 22 areas.

## Not checked

- S5 (LLM loop, llm.py, prompts.py) and any LLM path, including skeptic, advocate, strategist and generator.
- S6 gate and citation verification dynamically (static only). corpus.py BM25 was not read.
- pyright paths (not installed or run), `--experiments` paths such as metamorphic, witness, variant and assignability beyond the examples, `calibrate`, `fetch-docs`, and `triage`.
- experiments.py in depth (739 lines): only config_toggle and the paths the examples use.
- inhabit.py only exercised indirectly. Column handling for unicode (columns are used only for ordering reveals). ty full and gitlab formats on real output. Python 3.12/3.13 as host (host was 3.14).
- Only 3 KB entries have selftest examples; the other matchers were read, not run against positive and negative cases.
