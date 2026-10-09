"""Deterministic stage: crashes, validity, runtime evidence, auto-probes and KB auto-dismissal.

Invariant (the reason this stage can run without an LLM and still not lose bugs):
    a discrepancy is closed here ONLY by (a) a crash signature, (b) an exact cosmetic rule,
    (c) a KB entry with a precise matcher that is not contradicted by CPython, optionally
    confirmed by a deterministic experiment. Everything else is passed on, with evidence attached.
"""

from __future__ import annotations

import ast
import hashlib
import re

from .causes import dependency_constructs
from .experiments import ExperimentRunner, call_assignability_oracle, default_probe_exprs, self_call_plan
from .inhabit import inhabits
from .concerns import same_concern
from .kb import entry_demotion, matched_probe, matching_entries, runtime_contradiction
from .models import (
    Crash, Discrepancy, DiscrepancyKind, Dismissal, Evidence, EvidenceType, Finding, Symptom, Tier, Tool, Verdict,
)
from .parsers import classify_exception
from .state import CaseState
from .typenorm import normalize

K = DiscrepancyKind
_NONDETERMINISTIC = re.compile(r"\b(random|time\.time|datetime\.now|input\(|open\(|os\.environ|sys\.argv|threading|uuid)\b")


def crash_findings(crashes: list[Crash]) -> list[Finding]:
    out = []
    for i, c in enumerate(crashes, 1):
        if c.kind == "abnormal_exit":
            # exit code outside the normal set with no diagnostics: the run is INVALID, not "no errors".
            # Could be a config/usage problem rather than a checker bug -> human review, never dismissed or confirmed
            # (same cap for mypy, ty and pyright).
            out.append(Finding(
                discrepancy_id=f"C{i}", verdict=Verdict.NEEDS_HUMAN, tier=Tier.REVIEW, faulty_tool="unknown",
                symptom=None, dismissal=None, confidence=0.0, decided_by=f"rule:crash:{c.kind}",
                reasoning=f"{c.tool.value} exited abnormally ({c.signature}) without diagnostics: the run is invalid, "
                          "its empty output is NOT evidence of 'no errors'",
                evidence=[Evidence(EvidenceType.STACKTRACE, "neutral", c.excerpt[-1500:], c.signature, verified=True,
                                   strength="weak", blame=c.tool.value)],
                signature=c.signature,
            ))
            continue
        out.append(Finding(
            discrepancy_id=f"C{i}", verdict=Verdict.BUG, tier=Tier.CONFIRMED, faulty_tool=c.tool.value,
            symptom=Symptom.CRASH, dismissal=None, confidence=0.99, decided_by=f"rule:crash:{c.kind}",
            reasoning=f"{c.tool.value} {c.kind}: {c.signature}",
            correct_behavior="A type checker must never panic/crash/hang; it should report diagnostics (or none).",
            evidence=[Evidence(EvidenceType.STACKTRACE, "bug", c.excerpt[-1500:], c.signature, verified=True,
                               strength="strong", blame=c.tool.value)],
            signature=c.signature,
        ))
    return out


def validity(state: CaseState) -> dict:
    v: dict = {"valid": True, "problems": [], "runtime_usable": True}
    import sys

    try:
        target = tuple(int(x) for x in state.target_python.split("."))
    except ValueError:
        target = sys.version_info[:2]
    if state.amap.syntax_error and target > sys.version_info[:2]:
        raise RuntimeError(f"typediff runs on Python {sys.version_info[0]}.{sys.version_info[1]} but the target is "
                           f"{state.target_python}: its AST parser cannot read the program. Use a Python >= target venv.")
    if state.amap.syntax_error:
        v["valid"] = False
        v["problems"].append(f"syntax error: {state.amap.syntax_error}")
    rt = state.runtime
    if rt.status in ("not_run", "harness_error"):
        v["runtime_usable"] = False
        v["problems"].append(f"runtime {rt.status}")
    if rt.status == "exception" and rt.exc_type in ("ModuleNotFoundError", "ImportError"):
        v["problems"].append(f"runtime import failure: {rt.exc_message}")
    if rt.status == "exception" and rt.exc_type == "NameError" and "reveal_type" in (rt.exc_message or ""):
        v["runtime_usable"] = False
        v["problems"].append("reveal_type not available at runtime (run via runtime_harness.py)")
    if rt.status == "timeout":
        v["problems"].append("program timed out at runtime (runtime evidence partial)")
    if _NONDETERMINISTIC.search(state.source):
        v["problems"].append("program may be nondeterministic (random/time/io) - runtime evidence is weaker")
    return v


_MYPY_UNDEF = re.compile(r'Name "([\w.]+)" is not defined')
_TY_UNDEF = re.compile(r"Name `([\w.]+)` used when not defined")


def agreed_undefined_names(state: CaseState) -> set[str]:
    """Names BOTH checkers report as undefined: the program is incomplete (e.g. a repro missing its imports)."""
    m = {mm.group(1) for x in state.diags.get(Tool.MYPY, []) if (mm := _MYPY_UNDEF.search(x.message))}
    t = {mm.group(1) for x in state.diags.get(Tool.TY, []) if (mm := _TY_UNDEF.search(x.message))}
    return m & t


def _uses_names(state: CaseState, d: Discrepancy, names: set[str]) -> bool:
    st = state.amap.stmt(d.anchor)
    if st is None or st.node is None:
        return False
    node = st.node
    roots = [node] if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) else (
        list(node.decorator_list) + ([node.args, node.returns] if not isinstance(node, ast.ClassDef) else list(node.bases)))
    return any(isinstance(n, ast.Name) and n.id in names for r in roots if r is not None for n in ast.walk(r))


def _finding(d: Discrepancy, verdict: Verdict, tier: Tier, dismissal: Dismissal | None, by: str, reason: str,
             evidence: list[Evidence], conf: float = 0.95, faulty: str = "none", symptom: Symptom | None = None) -> Finding:
    return Finding(d.id, verdict, tier, faulty, symptom, dismissal, conf, by, reasoning=reason,
                   evidence=list(d.evidence) + evidence)


def attach_runtime_evidence(state: CaseState, d: Discrepancy) -> None:
    rt = state.runtime
    if rt.status in ("not_run", "harness_error"):
        return
    frame_anchors = {state.amap.anchor(ln) for ln, _ in rt.frames}
    strong_exc = rt.status == "exception" and classify_exception(rt.exc_type, rt.exc_message) == "strong"
    if strong_exc and d.anchor in frame_anchors:
        blame = {K.ONLY_MYPY: "ty", K.ONLY_TY: "mypy", K.RUNTIME_MISS: "both"}.get(d.kind, "unknown")
        reported = "; ".join(x.short() for x in d.mypy + d.ty) or "nothing"
        st = state.amap.stmt(rt.exc_line) if rt.exc_line else None
        causes = dependency_constructs(state.amap.tree, st.node if st else None, state.amap.lines)
        cause_txt = (f" Constructs in the raising statement's dependency set that could be responsible: {'; '.join(causes)}."
                     " A reduced repro must keep them." if causes else "")
        d.evidence.append(Evidence(
            EvidenceType.RUNTIME, "bug",
            f"CPython raised {rt.exc_type}: {rt.exc_message} with this statement on the stack "
            f"(frames {rt.frames}). Checker output here: {reported}. Check the exception is caused by the reported issue."
            f"{cause_txt}",
            citation=f"line {rt.exc_line}", verified=True, strength="strong", blame=blame,
        ))
    elif rt.coverage_known:
        executed = set(rt.executed_lines or [])
        if any(ln in executed for ln in range(d.anchor, d.anchor_end + 1)):
            d.evidence.append(Evidence(EvidenceType.RUNTIME, "neutral",
                                       "statement executed under CPython without a type-related exception (does NOT "
                                       "prove a rejection spurious)", citation=f"line {d.anchor}", verified=True,
                                       strength="weak"))
        else:
            d.evidence.append(Evidence(EvidenceType.RUNTIME, "neutral",
                                       "statement was never executed under CPython - no runtime oracle for it",
                                       citation=f"line {d.anchor}", verified=True, strength="weak"))
    if d.kind == K.REVEAL_MISMATCH:
        at_anchor = [p for p in rt.probes if state.amap.anchor(p.line) == d.anchor]
        for tool, lst in (("mypy", d.mypy), ("ty", d.ty)):
            if not lst:
                continue
            p = matched_probe(state, d, tool)  # k-th reveal <-> k-th probe, or None when ambiguous
            if p is None:
                if at_anchor:
                    d.evidence.append(Evidence(
                        EvidenceType.RUNTIME, "neutral",
                        f"{len(at_anchor)} runtime probe(s) at this statement cannot be paired with {tool}'s reveal_type "
                        "call unambiguously (several reveals on one statement, loop/repeated call, or nesting): "
                        "runtime probe values not used", citation=f"line {d.anchor}", verified=True, strength="weak"))
                continue
            t = normalize(lst[0].revealed_type, state.module)
            if inhabits(p.shape, t, state.nominal_classes) is False:
                d.evidence.append(Evidence(
                    EvidenceType.RUNTIME, "bug",
                    f"runtime value {p.shape.get('repr')!r} of type {p.shape.get('type')} does NOT inhabit {tool}'s "
                    f"revealed type {t.text if t else lst[0].revealed_type}",
                    citation=f"probe line {p.line}", verified=True, strength="strong", blame=tool))
    if d.kind == K.REVEAL_UNPAIRED and rt.coverage_known:
        line = (d.ty or d.mypy)[0].line
        if line in (rt.executed_lines or []):
            silent = "mypy" if not d.mypy else "ty"
            d.evidence.append(Evidence(
                EvidenceType.RUNTIME, "bug",
                f"{silent} produced no reveal_type output at line {line}, which CPython executed: {silent} treats "
                f"reachable code as unreachable (checking is disabled there)", citation=f"line {line}", verified=True,
                strength="medium", blame=silent))


def attach_pyright_evidence(state: CaseState, d: Discrepancy) -> None:
    if not state.pyright_ran:
        return
    from .experiments import _pyright_side

    side = _pyright_side(d, state.diags.get(Tool.PYRIGHT, []), state.amap)
    if side in ("mypy", "ty"):
        d.evidence.append(Evidence(EvidenceType.CONSENSUS, "neutral",
                                   f"pyright behaves like {side} at this statement (weak evidence)", verified=True,
                                   strength="weak", blame="ty" if side == "mypy" else "mypy"))


def flagged_bindings(state: CaseState, tool: Tool, names: set[str], before: int) -> list[tuple[str, int]]:
    """(name, line) for earlier statements that bind one of ``names`` and on which ``tool`` reported a problem.

    A checker's inferred type for a variable whose binding it already rejected is error *recovery*, not a
    soundness claim, so downstream consequences are cascades, not independent bugs.
    """
    out = []
    for x in state.diags.get(tool, []):
        if not x.is_problem or state.amap.anchor(x.line) >= before:
            continue
        st = state.amap.stmt(x.line)
        if st is None or st.node is None:
            continue
        bound = {n.id for n in ast.walk(st.node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
        if isinstance(getattr(st.node, "name", None), str):
            bound.add(st.node.name)
        for name in bound & names:
            out.append((name, st.anchor))
    return out


def cascade_stage(state: CaseState, decided: dict[str, Finding], remaining: list[Discrepancy],
                  all_ds: list[Discrepancy]) -> list[Discrepancy]:
    """Close ONLY_* discrepancies that merely propagate an already-dismissed discrepancy of the same checker."""
    by_anchor: dict[tuple[str, int], Discrepancy] = {}
    for d in all_ds:
        for t, lst in (("mypy", d.mypy), ("ty", d.ty)):
            if lst:
                by_anchor[(t, d.anchor)] = d
    keep = []
    for d in remaining:
        if d.kind not in (K.ONLY_MYPY, K.ONLY_TY) or runtime_contradiction(state, d):
            keep.append(d)
            continue
        tool = Tool.MYPY if d.kind == K.ONLY_MYPY else Tool.TY
        st = state.amap.stmt(d.anchor)
        used = {n.id for n in ast.walk(st.node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)} if st and st.node else set()
        parents = [by_anchor.get((tool.value, a)) for _, a in flagged_bindings(state, tool, used, d.anchor)]
        dismissed = [p for p in parents if p is not None and p.id in decided and decided[p.id].tier == Tier.DISMISSED
                     and decided[p.id].dismissal in (Dismissal.DESIGN_DIVERGENCE, Dismissal.KNOWN_LIMITATION,
                                                     Dismissal.CONFIG_ARTIFACT, Dismissal.SPEC_AMBIGUITY)]
        if dismissed:
            p = dismissed[0]
            decided[d.id] = _finding(
                d, Verdict.NOT_BUG, Tier.DISMISSED, Dismissal.NOISE, f"rule:cascade-of:{p.id}",
                f"error cascade: {tool.value} already rejected the binding at line {p.anchor} ({p.id}, dismissed as "
                f"{decided[p.id].dismissal.value} by {decided[p.id].decided_by}); this diagnostic follows from its error "
                "recovery", [Evidence(EvidenceType.HEURISTIC, "not_bug", f"cascade of {p.id}", citation=p.id, verified=True,
                                      strength="medium")], conf=0.85)
        else:
            keep.append(d)
    return keep


def _audit(case_id: str, d_id: str, rate: float) -> bool:
    if rate <= 0:
        return False
    h = int(hashlib.sha256(f"{case_id}:{d_id}".encode()).hexdigest()[:8], 16)
    return (h % 10_000) / 10_000 < rate


def deterministic_stage(state: CaseState, discrepancies: list[Discrepancy], ex: ExperimentRunner, *,
                        auto_probe: bool = True, audit_rate: float = 0.0, max_probes: int = 8) -> tuple[dict[str, Finding], list[Discrepancy]]:
    decided: dict[str, Finding] = {}
    remaining: list[Discrepancy] = []
    valid = validity(state)
    undefined = agreed_undefined_names(state)
    if undefined:
        state.notes.append(f"both checkers report undefined names {sorted(undefined)}: incomplete program")
    probes_done = 0
    for d in sorted(discrepancies, key=lambda x: -x.priority):
        if not valid["valid"]:
            decided[d.id] = _finding(d, Verdict.NOT_BUG, Tier.DISMISSED, Dismissal.INVALID_TEST, "rule:invalid-program",
                                     "; ".join(valid["problems"]), [])
            continue
        if undefined and _uses_names(state, d, undefined):
            decided[d.id] = _finding(d, Verdict.NOT_BUG, Tier.DISMISSED, Dismissal.INVALID_TEST, "rule:undefined-name",
                                     f"statement depends on names both checkers report as undefined: {sorted(undefined)}",
                                     [])
            continue
        attach_runtime_evidence(state, d)
        attach_pyright_evidence(state, d)
        if d.kind == K.SEVERITY_ONLY:
            pairs = "; ".join(f"mypy {x.severity.value}[{x.code}] <-> ty {y.severity.value}[{y.code}]"
                              for x in d.mypy for y in d.ty if same_concern(x, y))
            ev = Evidence(EvidenceType.HEURISTIC, "not_bug",
                          f"compared at L{d.anchor}: mypy {[f'{x.severity.value}[{x.code}]' for x in d.mypy]} vs ty "
                          f"{[f'{x.severity.value}[{x.code}]' for x in d.ty]}; same-concern pairing: {pairs or 'none'}. "
                          "Both checkers flag the same concern (no unmatched diagnostic on either side); "
                          "only error-vs-warning differs",
                          citation=f"rule:severity-only@L{d.anchor}", verified=True, strength="medium")
            decided[d.id] = _finding(d, Verdict.NOT_BUG, Tier.DISMISSED, Dismissal.NOISE, "rule:severity-only",
                                     "same concern reported by both checkers; only the severity differs", [ev])
            continue
        # cheap, deterministic operand probe -> explains most inference-driven ONLY_* discrepancies
        if (auto_probe and state.online and probes_done < max_probes
                and d.kind in (K.ONLY_MYPY, K.ONLY_TY, K.CONCERN_MISMATCH)):
            exprs = default_probe_exprs(state, d)
            if exprs:
                r = ex.run(d, {"kind": "reveal_probe", "line": d.anchor, "exprs": exprs})
                probes_done += 1
                if r.ok:
                    state.probe_cache[d.id] = r.outcome
                    d.evidence.append(Evidence(EvidenceType.EXPERIMENT, "neutral", f"{r.id} operand types: {r.summary}",
                                               citation=r.id, verified=True, strength="medium"))
                    for expr, o in r.outcome.items():
                        for tool in ("mypy", "ty"):
                            if o.get(f"runtime_in_{tool}_type") is False:
                                recov = flagged_bindings(state, Tool(tool), {expr.split(".")[0]}, d.anchor)
                                note = (f" - but {tool} already reported an error where `{expr.split('.')[0]}` is bound "
                                        f"(line {recov[0][1]}): error recovery, not an independent soundness claim") if recov else ""
                                d.evidence.append(Evidence(
                                    EvidenceType.RUNTIME, "bug" if not recov else "neutral",
                                    f"operand `{expr}`: runtime type {o.get('runtime')} is outside {tool}'s inferred type "
                                    f"{o.get(tool)}{note}", citation=r.id, verified=True,
                                    strength="strong" if not recov else "weak", blame=tool))
        if state.online and d.kind in (K.ONLY_MYPY, K.ONLY_TY):
            ev = call_assignability_oracle(state, d, ex)
            if ev is not None:
                d.evidence.append(ev)
        if state.online and d.kind == K.ONLY_MYPY and self_call_plan(state, d) is not None:
            r = ex.run(d, {"kind": "lsp_probe"})  # narrow: is mypy's own reading Liskov-safe? (hint-level evidence)
            if r.ok and r.evidence is not None:
                d.evidence.append(r.evidence)
        if state.online and d.kind == K.RUNTIME_MISS:
            r = ex.run(d, {"kind": "opt_in_checks"})
            if r.ok and r.evidence:
                d.evidence.append(r.evidence)
                for tool, items in r.outcome.items():
                    for item in items[:6]:
                        d.evidence.append(Evidence(EvidenceType.EXPERIMENT, "neutral", f"{tool} opt-in check: {item}",
                                                   citation=r.id, verified=True, strength="medium"))
        hits = matching_entries(state, d)
        d.kb_hits = [h.id for h in hits]
        closed = False
        for e in sorted(hits, key=lambda h: h.verify is not None):
            if not e.auto:
                continue
            demotion = entry_demotion(state, d, e)
            if demotion is not None:
                d.evidence.append(demotion)
                continue
            extra = [Evidence(EvidenceType.KB, "not_bug", e.title, citation=f"KB:{e.id}", quote="", verified=True,
                              strength="strong" if e.verify is None else "medium")]
            if e.verify is not None:
                ev = e.verify(state, d, ex)
                if ev is None or ev.supports != "not_bug":
                    if ev is not None:
                        d.evidence.append(ev)
                    continue
                extra.append(ev)
            f = _finding(d, Verdict.NOT_BUG, Tier.DISMISSED, e.dismissal, f"kb:{e.id}",
                         f"{e.title}. Source: {e.source}", extra, conf=0.9 if e.verify is None else 0.95)
            if _audit(state.case_id, d.id, audit_rate):
                # sampled audit: the KB verdict is re-examined by the LLM judge + advocate (measures false dismissals)
                state.audited.add(d.id)
                state.notes.append(f"{d.id}: KB:{e.id} auto-dismissal sampled for audit")
                remaining.append(d)
                d.evidence.extend(extra)
            else:
                decided[d.id] = f
            closed = True
            break
        if not closed:
            remaining.append(d)
    remaining = cascade_stage(state, decided, remaining, discrepancies)
    return decided, remaining
