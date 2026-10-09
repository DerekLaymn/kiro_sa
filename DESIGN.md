# typediff — design

Adjudication pipeline for **mypy vs ty** differential testing (pyright is an optional, weak
tie-breaker). Its input is a Python program, mypy stdout/stderr, ty stdout/stderr and the CPython
result. For every disagreement it decides: **real bug (and in which tool)**, **expected
difference** (with an auditable reason), or **undecided → human queue**. It then advises what to
generate next.

Calibrated against **ty 0.0.84, mypy 2.4.0, pyright 1.1.414, CPython 3.12** (Oct 2026).

---

## 1. Cost model: the one rule everything follows

- A false report costs maintainer time and your credibility.
- A dismissed real bug is gone for good.

So the pipeline is **asymmetric**:

| action | requirement |
|---|---|
| send to human review | nothing (the default) |
| **dismiss** | a citation that can be checked: KB entry with a precise matcher, a *verbatim* doc/spec quote that matches the local corpus, or a deterministic experiment result. CPython must not contradict it. |
| **report** | ≥1 *verified strong* evidence item (stack trace, runtime proof, verified spec quote, self-contradiction, conformance), confidence ≥ threshold, and a skeptic pass that did not argue it is intended behaviour |

Nothing is ever silently dropped. Every dismissal records `decided_by` and its evidence. A sampled
audit (`--audit-rate`, default 5 %) sends KB auto-dismissals back through the LLM judge and the
advocate, so you can measure how often the KB wrongly dismisses something.

---

## 2. Taxonomy: are your four categories enough?

Your four categories mix two separate questions: **what went wrong** and **how we know**.

- *Soundness Failure* and *Spurious Rejection* describe **what went wrong**.
- *Spec Violation* describes **how we know**. Every soundness failure or spurious rejection is
  either a spec violation or it isn't. Used as a peer category, it overlaps with the other two, and
  the classifier has to pick one at random.
- *Engine Crash* is fine but too narrow. Hangs and non-deterministic output are the same kind of
  bug (no oracle needed).

The fix is three orthogonal axes:

**Axis A — Symptom (only for BUG):**

| symptom | replaces / adds | why it is needed |
|---|---|---|
| `CRASH` | Engine Crash + hang/timeout + non-determinism | Always a bug, even on invalid input; dedup by panic location |
| `FALSE_NEGATIVE` | Soundness Failure | Accepts code it must reject |
| `FALSE_POSITIVE` | Spurious Rejection | Rejects code the spec allows |
| `INCORRECT_INFERENCE` | **new** | Wrong `reveal_type` with no accept/reject difference (yet). Very common in ty; fixes go in inference code, not checking code |
| `DIAGNOSTIC_DEFECT` | **new** | Right decision, but wrong line/message/rule, duplicate diagnostics, or a mishandled `type: ignore`. Real but low priority, so it must not get mixed in with soundness bugs |

**Axis B — Evidence (drives the gate):** `STACKTRACE`, `RUNTIME`, `SPEC` (verbatim, verified),
`CONFORMANCE`, `SELF_CONTRADICTION`, `DOC`, `KB`, `EXPERIMENT`, `CONSENSUS` (pyright, weak),
`HEURISTIC`. *Spec Violation* lives here now: it is a `SPEC` evidence item attached to a
FALSE_NEGATIVE / FALSE_POSITIVE / INCORRECT_INFERENCE finding.

**Axis C — Dismissal (only for NOT_BUG). This is what you need to remove false positives:**
`DESIGN_DIVERGENCE`, `SPEC_AMBIGUITY`, `KNOWN_LIMITATION` (ty `@Todo`, "None yet" checks),
`CONFIG_ARTIFACT` (flags, python-version, optional checks, environment, typeshed skew),
`INVALID_TEST`, `NOISE`, `DUPLICATE`.

Plus a `faulty_tool` field (`ty | mypy | both | none`). "Both accept code that crashes at runtime"
is a real outcome that a pure differential setup never shows (it appears as `RUNTIME_MISS`).

**Do you need fewer?** No. Merging INCORRECT_INFERENCE into the others loses the most common ty
bug class. **More?** Not at the top level. Finer splits (e.g. narrowing vs. overload) belong in
the *feature tags* stored with each finding.

**Pyright as a tie-breaker: yes, but weak.** pyright shares design choices with *both* sides:
unions instead of joins and assignment narrowing (like ty), and long-standing defaults (like mypy).
Consensus never decides alone. It runs once per case (~1 s) and appears as `CONSENSUS/weak`
evidence plus "pyright sides with X".

---

## 3. Architecture

```
            ┌──────────── inputs (offline contract) ─────────────┐
 program.py │ mypy stdout/stderr │ ty stdout/stderr │ CPython result │ (+pyright json)
            └──────────────┬──────────────────────────────────────┘   or `typediff run` produces
                           ▼                                             them itself (isolated,
 S0 crash detector ──► CRASH findings (confirmed, dedup by signature)    pinned flags, harness)
 S1 validity gate  ──► INVALID_TEST if the program is broken
 S2 parse + normalise (mypy text/json, ty concise/full/gitlab, pyright json, traceback/harness json)
    statement anchors (AST)   type-string canonicaliser   rule/concern map (ty's official table)
 S3 discrepancy extraction  ONLY_MYPY | ONLY_TY | CONCERN_MISMATCH | SEVERITY_ONLY |
                            REVEAL_MISMATCH | REVEAL_UNPAIRED | RUNTIME_MISS
 S4 deterministic stage (no LLM)
    • runtime evidence: exception-on-stack, value-inhabits-type, coverage
    • auto operand reveal-probes   • call/assignability self-consistency oracle
    • opt-in-check rerun for RUNTIME_MISS   • KB matchers (+ verify-by-experiment)
    • cascade closer (consequence of an already-dismissed discrepancy)
 S5 LLM adjudicator (batched per case, ≤3 rounds)  ◄──► experiment executor (allow-listed)
 S6 citation verifier → skeptic (vs BUG) / advocate (vs weak NOT_BUG) → asymmetric gate
 S7 dedup signature → delta-debugging reducer → issue draft
 S8 dataset (JSONL) → strategy (UCB1 bandit + hard rules + LLM strategist) → generator brief
```

Code map: `parsers.py` S0/S2, `rules.py` S1/S4, `anchors.py`, `typenorm.py`, `concerns.py`,
`discrepancy.py` S3, `kb.py`, `experiments.py`, `adjudicator.py` S5/S6, `reducer.py`,
`dataset.py`, `report.py` S7, `strategy.py`, `generator.py` S8, `pipeline.py` orchestration,
`prompts.py` all LLM prompts.

---

## 4. The algorithm

```text
ADJUDICATE(src, mypy_out, ty_out, runtime, [pyright]):
  crashes ← detect(ty exit 101 | "panicked at" | error[panic];  mypy INTERNAL ERROR | traceback;
                   timeout; ty re-run diff ≠ ∅)
  emit CRASH(confirmed) for each; if mypy or ty crashed: stop (its diagnostics are incomplete)
  if src does not parse: every discrepancy → INVALID_TEST

  D ← per-statement diff:
      problems(tool, stmt) paired by same_concern (ty rule-map table, then families)
      reveal_type pairs per line → relation ∈ {equal, cosmetic, gradual, todo,
                                               x_more_precise, different, uncomparable}
      RUNTIME_MISS if a strong type exception has no flagged frame statement

  for d in D by priority:                              # S4: deterministic, auditable
      attach runtime evidence
      if online: auto reveal-probe of d's operands; call/assignability oracle; opt-in rerun
      for e in KB entries matching d (auto ones first, verify-required last):
          if e.runtime_override and CPython contradicts e here: keep e as a hint only
          if e.verify: run the documented toggle/experiment; continue unless it confirms
          DISMISS(d, e.dismissal, KB:e) unless sampled for audit; break
  close cascades of already-dismissed discrepancies (same tool, rejected binding)

  for undecided batch (≤8), rounds 1..3:              # S5
      J ← LLM_JUDGE(case file, KB hints, retrieved spec/doc chunks, experiment results)
      verify J's evidence: SPEC/DOC quotes must match the corpus; KB ids must have matched;
                           EXPERIMENT ids must exist; RUNTIME must match harness facts
      if J = NEEDS_EXPERIMENT: run its (allow-listed) experiments, add results, re-judge

  for each final judgment:                            # S6
      BUG     → SKEPTIC (maintainer role). "Intended" only counts with a verified citation
      NOT_BUG → ADVOCATE if confidence < 0.95 or audited. REOPEN → review
      optional self-consistency votes (k samples, disagreement → NEEDS_HUMAN)
      GATE:
        BUG  & strong verified evidence & conf ≥ .85 & skeptic not opposed → CONFIRMED
        BUG  & strong verified evidence & conf ≥ .60 & skeptic not opposed → CANDIDATE
        NOT_BUG & verified dismissal evidence & conf ≥ .85 & advocate upholds → DISMISSED
        otherwise → REVIEW (human queue, ranked by priority)

  for CONFIRMED/CANDIDATE: signature → DUPLICATE?  else reduce (ddmin over AST statement lists,
      keeping the discrepancy, the runtime class, and no new errors elsewhere) → issue draft
  STRATEGIZE(area stats, findings) → CONTINUE | MUTATE | PIVOT | ABANDON | REPAIR_GENERATOR
```

### 4.1 Oracles (where "ground truth" comes from)

| oracle | catches | strength |
|---|---|---|
| crash / timeout / re-run diff | engine failures | strong, no interpretation |
| exception with the statement on the stack | FALSE_NEGATIVE (silent tool), validates the reporting tool | strong (but check the cause, Any paths) |
| runtime value ∉ revealed type (`inhabit.py`) | INCORRECT_INFERENCE | strong, only definite `False` is used |
| coverage: executed line has no reveal in tool X | checker treats reachable code as unreachable | medium |
| **call/assignability self-consistency** | tool reveals `f: (c: Leaf) -> …`, rejects `_: Leaf = Node()`, accepts `f(Node())` | strong, the tool contradicts itself |
| metamorphic `pep604` / `pep585` (vs. an unparsed baseline) | spelling-dependent behaviour | strong |
| gradual guarantee (`any_substitution`) | new errors after replacing a type with `Any` | strong |
| config toggle (strict-equality, strict-generic-narrowing, optional mypy codes) | confirms a KB "design" explanation | strong for dismissal |
| opt-in soundness rerun (mypy `mutable-override`…, ty `unsound-*`…) | tells a *deliberate default* apart from *no mode catches it* | medium |
| witness (LLM-written appended code that must crash) | turns a spec argument into a runtime proof | strong |
| pyright | consensus | weak |

### 4.2 Knowledge base (`kb.py`)

Every entry was checked against real tool output. `typediff kb-selftest` re-runs the canonical
examples after you upgrade.

| id | kind | auto? |
|---|---|---|
| TY-REDECLARATION | ty allows re-*annotating* a name that already has a declaration in the same scope (mypy `no-redef`). Redefined `def`s/classes are excluded | yes |
| TY-CALLABLE-DUNDER | ty rejects `Callable.__name__` (FAQ) | yes |
| TY-STRICT-EQUALITY | `==`/`in`/match-value narrowing is unsound by default | only if the toggle removes the discrepancy |
| TY-GRADUAL-GENERIC-NARROWING | `isinstance(x, list)` → `list[Unknown]` | only if the toggle confirms |
| TY-UNKNOWN-UNION / TY-TODO | `Unknown \| T` for unannotated declarations / `@Todo` | yes |
| TY-CHECK-NOT-IMPLEMENTED | mypy code that ty lacks *and* whose mypy side is documented design (`var-annotated`, `import-untyped`, …) | yes |
| TY-CHECK-MISSING-JUDGE-MYPY | any other mypy code ty lacks (`overload-overlap`, `type-abstract`, …): ty's silence is expected, but mypy's diagnostic may be a false positive | hint only |
| MYPY-OPTIONAL-CHECK | ty rule ↔ mypy code that is off by default | only if enabling it in mypy confirms |
| MYPY-UNTYPED-DEFS | missing `--check-untyped-defs` | yes |
| BOTH-GRADUAL | every differing position is gradual on *both* sides. Not when the source spells `Any` and ty says `Unknown` (lost provenance, ty#4536) | yes |
| JOIN-VS-UNION | mypy `object`/base-class join vs. a non-gradual union, never a TypeVar. Classed as KNOWN_LIMITATION (mypy `topic-join-v-union`) | yes, reveal differences only |
| LITERAL-WIDENING, PRECISION-RUNTIME-CONSISTENT | implementation-defined inference | yes, *unless CPython contradicts the more precise type* |
| MYPY-SKIPS-UNREACHABLE | mypy is silent in code CPython never ran | yes |
| ENV-IMPORT, SUPPRESSION-SEMANTICS | environment / documented ignore semantics | yes |
| INFERENCE-DOWNSTREAM | the probe shows an unannotated operand inferred differently. Covers an error from the *more precise* side; a mypy false positive caused by its join is not covered | yes |
| TY-CHECK-PARTIAL, TY-ONLY-CHECK, REACHABILITY-VS-COVERAGE, GRADUAL-OPERAND, ERROR-CASCADE, STUB-SKEW, PARTIAL-TYPES, SUPPRESSION-LINE | leads for the LLM | hint only |

Two deterministic rules sit next to the KB:
- `rule:cascade-of:Dn`: a diagnostic downstream of an already-dismissed rejection by the same
  checker.
- `rule:undefined-name`: the statement depends on names *both* checkers report as undefined
  (incomplete repro → INVALID_TEST).

`runtime_override=True` is what keeps the KB from swallowing a real soundness bug that looks like
a known divergence. Every narrowing of a KB entry above came from the calibration run (§7).

---

## 5. LLM roles and prompts (`prompts.py`)

| role | when | key constraints |
|---|---|---|
| **ADJUDICATOR** | undecided discrepancies, batched, ≤3 rounds | cost model, ground-truth ranking, full taxonomy, quote-only-from-context, steelman (`counter_hypothesis`), calibrated confidence, experiment menu, strict JSON |
| **SKEPTIC** | every BUG verdict | plays the accused maintainer; "working as intended" must be cited |
| **ADVOCATE** | NOT_BUG with conf < 0.95, and audited KB dismissals | looks for the reason it *is* a bug; REOPEN → human |
| **STRATEGIST** | after every case | hard rules can't be overridden; picks mutation operators and writes the next brief |
| **GENERATOR** | next program | stdlib only, deterministic, *every function called*, `reveal_type` on the point of the test, avoid patterns from the KB |
| **REPORTER** | confirmed and reduced findings | tracker templates (ty: Summary/Version + playground; mypy: Bug Report/To Reproduce/Expected/Actual/Environment) |

Program text and tool output are labelled as *data* in the judge prompt (prompt-injection
defence). Experiment requests go through allow-lists: flags, side-effect-free probe expressions,
and size limits.

---

## 6. Search strategy (`strategy.py`)

- 22 feature areas (generics/variance, ParamSpec, TypedDict, overloads, narrowing, match, Self,
  descriptors, recursive aliases …). UCB1 picks areas. Reward = 10·confirmed + 4·candidate +
  1·review + 6·crash, scaled down when no new signature was found.
- **Hard rules** (the LLM can't override):
  - **CONTINUE** on a bug candidate: make close variants to generalise it.
  - **REPAIR_GENERATOR** when ≥ 50 % of the last 4 programs were invalid.
  - **ABANDON** an area dominated by KNOWN_LIMITATION (revisit after the next ty release).
  - **PIVOT** when the last 5 cases only reproduced ≤ 2 KB ids or had no disagreement at all.
  - Otherwise **MUTATE**.
- KB hits feed `avoid_patterns` back to the generator, so noise drops over time.
- Mutation operators: `variance_flip`, `bound_constraint_swap`, `generic_nesting`,
  `union_widen`, `literal_injection`, `gradual_injection`, `narrowing_construct_swap`,
  `annotation_spelling_swap`, `scope_relocation`, `protocol_vs_abc`, `qualifier_toggle`,
  `overload_reorder`, `recursion_deepening` / `invalid_type_form` / `feature_crossover`
  (crash hunting), `python_version_flip`, `runtime_witness`, `inheritance_diamond`,
  `descriptor_property`, `decorator_wrapping`, `async_generator_wrap`.

---

## 7. Measuring it (`typediff calibrate`)

1. **Positives:** `calibrate --fetch` downloads *open*, maintainer-labelled bug reports with a
   stdlib-only repro (ty `bug`; mypy `bug`+`false-positive` and `crash`).
2. **Negatives:** documented differences: `calibration/negatives/*.py` plus every KB example.
3. **Per-case outcome:**
   - `kept`: some finding is confirmed, candidate or review.
   - `dismissed`: everything was dismissed, so this is a candidate false dismissal.
   - `invisible`: mypy and ty agree, so differential testing can't see the bug.
   - `excluded`: not applicable (e.g. the repro uses `ty_extensions`).
4. **Current results**, deterministic stage only, ty 0.0.84 / mypy 2.4.0 (details in
   `calibration/RESULTS.md`):
   - 156 positives:
     - ty: 58 kept, 17 invisible, **0 dismissed**, 5 excluded.
     - mypy: 38 kept, 34 invisible, 4 dismissed.
     - The 4 mypy dismissals: 3 bugs no longer reproduce on mypy 2.4, and 1 is the deliberate
       join-vs-union policy.
     - 14 crashes were confirmed automatically (10 ty panics/hangs, 4 mypy).
   - 9 of 10 negatives were closed automatically. The other produced no discrepancy.
   - Seven false-dismissal bugs in typediff were found and fixed along the way.
5. **Still to do:** precision of CONFIRMED needs the LLM judge. Tune `GateConfig` against it; 168
   of 198 findings on positives are currently in review.
6. **In campaigns:** track the audit disagreement rate (an audited KB dismissal that the judge or
   advocate reopens). If it rises above ~2 %, fix or demote the KB entry.

---

## 8. Worked example (real, ty 0.0.84)

`examples/self_param_unsound.py`: ty reveals `x.add` as `bound method Leaf.add(c: Leaf) -> Leaf`
but accepts `x.add(Node())`. mypy and pyright reject it, and CPython later raises
`AttributeError`. With no LLM at all, the deterministic stage attaches:

- `SELF_CONTRADICTION/strong`: ty rejects `_td_probe: Leaf = Node()` but accepts the call.
- `RUNTIME/strong` on the downstream statement (RUNTIME_MISS).
- `CONSENSUS/weak`: pyright sides with mypy.

With an LLM judge this passes the gate as CONFIRMED. The reducer shrinks it in 32 checker runs
(about 20 s). Below is the reducer output with an unused import and blank lines removed:

```python
from typing import Self

class Node:
    def add(self, c: Self) -> Self:
        return self

class Leaf(Node):
    pass

x = Leaf()
x.add(Node())
```

**Outcome upstream (the lesson matters more than the bug).** The ty maintainers closed the report
as **intended behaviour**:

- The typing spec treats `Self` as a type variable whose upper bound is the defining class. ty
  solves it per call, so `Leaf().add(Node())` solves `Self = Node` and returns `Node`.
- mypy and pyright bind `Self` to the receiver instead. That makes `Self`-typed parameters break
  Liskov substitutability: `use_node(leaf)` can still call `node.add(Node())`.
- What *was* a bug is the **displayed** signature `bound method Leaf.add(c: Leaf)`. That display
  is now tracked as [ty#4673](https://github.com/astral-sh/ty/issues/4673). The self-consistency
  oracle had been reading exactly that display.

What changed in typediff:
- The case is recorded in `known_upstream.json` (`UPSTREAM-TY-SELF-PARAM-TYPEVAR`), so
  `Self`-parameter call disagreements are now closed as DESIGN_DIVERGENCE with the link.

Lessons for the pipeline:
1. **"mypy and pyright agree" is not evidence of a spec rule.** Two checkers can share an
   interpretation the spec leaves open. That is why CONSENSUS is weak.
2. **A self-contradiction is only as good as the probe.** A reveal of a *bound method* shows a
   display, not necessarily the signature used for call checking. The oracle found a real
   inconsistency, but the bug was in the display (DIAGNOSTIC_DEFECT/INCORRECT_INFERENCE), not in
   call checking (FALSE_NEGATIVE).
3. **Look for the counter-example before filing.** Ask "if the other checker is right, what else
   must be rejected?" The maintainer's `use_node(leaf)` argument is the counter-hypothesis the
   skeptic role is meant to find.
4. **The downstream runtime crash came from a mutable `list[Self]` attribute.** That is unsound
   under any interpretation once a `Leaf` is upcast to `Node`. So it didn't actually incriminate ty.

## 9. Limitations

- The runtime oracle only sees the executed path. Runtime success never proves a rejection is
  spurious.
- `inhabit.py` decides builtins, literals, enums, containers and nominal user classes. Protocols,
  TypeVars and callables return "unknown".
- KB entries are version-specific. Re-run `kb-selftest` and `fetch-docs --refresh-rule-map` after
  every ty or mypy upgrade (ty is `0.0.x` and changes weekly).
- Generated programs are untrusted code. Run the harness in a container without network access.
