"""LLM adjudication loop: judge -> verify citations -> experiments -> re-judge -> adversarial review -> gate."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from . import prompts
from .corpus import Corpus
from .experiments import ExperimentRunner
from .kb import BY_ID, kb_prompt_block, runtime_contradiction
from .llm import complete_json
from .models import (
    DISMISSAL_EVIDENCE, STRONG_BUG_EVIDENCE, Discrepancy, Dismissal, Evidence, EvidenceType, Finding, Symptom, Tier,
    Tool, Verdict,
)
from .state import CaseState


@dataclass
class GateConfig:
    confirm_bug: float = 0.85  # BUG + verified strong evidence + skeptic not opposed -> CONFIRMED
    candidate_bug: float = 0.6  # BUG + verified strong evidence -> CANDIDATE
    dismiss: float = 0.85  # NOT_BUG + verified dismissal evidence + advocate upholds -> DISMISSED
    advocate_below: float = 0.95  # run the advocate on LLM dismissals below this confidence
    max_rounds: int = 3
    max_batch: int = 8
    max_experiments_per_round: int = 3
    votes: int = 1  # >1: self-consistency voting on final verdicts (temperature 0.7)
    context_chars: int = 14000


# --------------------------------------------------------------------------- rendering helpers


def numbered(source: str) -> str:
    return "\n".join(f"{i:>3} | {ln}" for i, ln in enumerate(source.splitlines(), 1))


def runtime_block(state: CaseState) -> str:
    rt = state.runtime
    parts = [f"status: {rt.status}"]
    if rt.status == "exception":
        parts.append(f"exception: {rt.exc_type}: {rt.exc_message}")
        parts.append(f"traceback frames in this file (line, function): {rt.frames}")
    if rt.coverage_known:
        executed = set(rt.executed_lines or [])
        code_lines = [s.anchor for s in state.amap.statements]
        never = sorted({ln for ln in code_lines if ln not in executed})
        parts.append(f"statements never executed (by start line): {never or 'none'}")
    else:
        parts.append("coverage: unknown")
    if rt.probes:
        seen: dict[int, list[str]] = {}
        for p in rt.probes:
            seen.setdefault(p.line, [])
            if len(seen[p.line]) < 3:
                seen[p.line].append(f"{p.shape.get('type')} = {p.shape.get('repr')}")
        parts.append("runtime reveal_type probes: " + "; ".join(f"L{k}: {', '.join(v)}" for k, v in sorted(seen.items())))
    if rt.stdout.strip():
        parts.append(f"stdout (tail): {rt.stdout.strip()[-300:]}")
    return "\n".join(parts)


def diags_block(state: CaseState, tool: Tool) -> str:
    lst = state.diags.get(tool)
    if lst is None:
        return "(not run)"
    return "\n".join(f"  {d.short()}" for d in lst) or "  (no diagnostics)"


def evidence_lines(evs: list[Evidence]) -> str:
    return "\n".join(
        f"    - [{e.type.value}/{e.strength}{'/verified' if e.verified else ''}] supports={e.supports}"
        f"{' blame=' + e.blame if e.blame else ''}: {e.summary}" + (f" ({e.citation})" if e.citation else "")
        for e in evs
    ) or "    (none)"


def discrepancy_block(state: CaseState, ds: list[Discrepancy]) -> str:
    out = []
    for d in ds:
        out.append(
            f"### {d.id}  kind={d.kind.value}  statement lines {d.anchor}-{d.anchor_end}  scope={d.scope}\n"
            f"  statement: {d.statement}\n"
            f"  mypy: {'; '.join(x.short() for x in d.mypy) or '(nothing at this statement)'}\n"
            f"  ty:   {'; '.join(x.short() for x in d.ty) or '(nothing at this statement)'}\n"
            f"  pyright: {'; '.join(x.short() for x in d.pyright) or '(nothing / not run)'}\n"
            + (f"  reveal relation (mypy vs ty): {d.reveal_relation}\n" if d.reveal_relation else "")
            + f"  typing features: {', '.join(d.features) or '-'}\n"
            f"  KB matches: {', '.join('KB:' + k for k in d.kb_hits) or 'none'}\n"
            f"  deterministic evidence:\n{evidence_lines(d.evidence)}"
        )
    return "\n\n".join(out)


def _query_for(state: CaseState, d: Discrepancy) -> str:
    bits = [d.statement, " ".join(d.features), " ".join(x.code or "" for x in d.mypy + d.ty),
            " ".join(x.message for x in d.mypy + d.ty)[:400]]
    bits += [BY_ID[k].title for k in d.kb_hits if k in BY_ID]
    return " ".join(bits)


def context_block(corpus: Corpus, state: CaseState, ds: list[Discrepancy], extra_queries: list[str], limit: int) -> str:
    if corpus.empty:
        return "(no local corpus - run `typediff fetch-docs`; you cannot quote SPEC/DOC text this time)"
    seen, parts, total = set(), [], 0
    queries = [_query_for(state, d) for d in ds] + extra_queries
    for q in queries:
        for c in corpus.search(q, k=4, prefer=("spec/", "ty/", "ty-rules/")):
            if c.id in seen:
                continue
            block = f"[{c.id}] ({c.url})\n{c.text}"
            if total + len(block) > limit:
                break
            seen.add(c.id)
            parts.append(block)
            total += len(block)
    return "\n\n---\n\n".join(parts) or "(no relevant documents found)"


# --------------------------------------------------------------------------- validation


_VERDICTS = {v.value for v in Verdict}
_SYMPTOMS = {s.value for s in Symptom}
_DISMISSALS = {d.value for d in Dismissal}
_EVIDENCE = {e.value for e in EvidenceType}


def make_validator(expected: set[str]):
    def validate(obj: Any) -> list[str]:
        errs = []
        if not isinstance(obj, dict) or not isinstance(obj.get("judgments"), list):
            return ["top-level object must have a 'judgments' list"]
        got = set()
        for j in obj["judgments"]:
            if not isinstance(j, dict):
                errs.append("each judgment must be an object")
                continue
            did = j.get("discrepancy_id")
            got.add(did)
            if j.get("verdict") not in _VERDICTS:
                errs.append(f"{did}: verdict must be one of {sorted(_VERDICTS)}")
            if j.get("verdict") == "BUG" and j.get("symptom") not in _SYMPTOMS:
                errs.append(f"{did}: BUG needs symptom in {sorted(_SYMPTOMS)}")
            if j.get("verdict") == "NOT_BUG" and j.get("dismissal") not in _DISMISSALS:
                errs.append(f"{did}: NOT_BUG needs dismissal in {sorted(_DISMISSALS)}")
            try:
                c = float(j.get("confidence", -1))
                if not 0 <= c <= 1:
                    raise ValueError
            except (TypeError, ValueError):
                errs.append(f"{did}: confidence must be a number in [0,1]")
        missing = expected - got
        if missing:
            errs.append(f"missing judgments for {sorted(missing)}")
        return errs
    return validate


def kb_entry_eligible(state: CaseState, d: Discrepancy, entry) -> bool:
    """A KB citation may back a dismissal only if the entry could have auto-dismissed this discrepancy:
    not hint-only, not demoted by a CPython contradiction, and (if it needs one) its experiment confirmed."""
    if not entry.auto:
        return False
    if runtime_contradiction(state, d) and (entry.runtime_override or d.kind in entry.runtime_override_kinds):
        return False
    if entry.verify is not None:
        return any(e.type == EvidenceType.EXPERIMENT and e.verified and e.supports == "not_bug" for e in d.evidence)
    return True


# --------------------------------------------------------------------------- adjudicator


class Adjudicator:
    def __init__(self, llm, corpus: Corpus, cfg: GateConfig | None = None):
        self.llm = llm
        self.corpus = corpus
        self.cfg = cfg or GateConfig()
        for e in BY_ID.values():
            corpus.add_verifiable_text(e.text)

    @property
    def enabled(self) -> bool:
        return getattr(self.llm, "name", "null") != "null"

    # .................................................................. main loop
    def adjudicate(self, state: CaseState, ds: list[Discrepancy], ex: ExperimentRunner, known: list[str]) -> dict[str, Finding]:
        results: dict[str, Finding] = {}
        ds = sorted(ds, key=lambda d: -d.priority)
        overflow, batch = ds[self.cfg.max_batch:], ds[: self.cfg.max_batch]
        for d in overflow:
            results[d.id] = self._undecided(d, "not adjudicated: batch limit reached (raise GateConfig.max_batch)")
        if not batch:
            return results
        if not self.enabled:
            for d in batch:
                results[d.id] = self._undecided(d, "no LLM configured (TYPEDIFF_LLM=null): needs a human")
            return results

        pending = {d.id: d for d in batch}
        last: dict[str, dict] = {}
        extra_queries: list[str] = []
        for rnd in range(1, self.cfg.max_rounds + 1):
            user = self._user_prompt(state, list(pending.values()), ex, known, extra_queries, rnd)
            obj = complete_json(self.llm, prompts.ADJUDICATOR_SYSTEM, user, make_validator(set(pending)))
            if obj.get("_null") or obj.get("_invalid"):
                for d in pending.values():
                    results[d.id] = self._undecided(d, f"LLM returned no usable answer: {obj.get('_errors', '')}")
                return results
            ran_any = False
            for j in obj["judgments"]:
                did = j.get("discrepancy_id")
                if did not in pending:
                    continue
                last[did] = j
                if j["verdict"] == "NEEDS_EXPERIMENT" and rnd < self.cfg.max_rounds:
                    for req in (j.get("experiments") or [])[: self.cfg.max_experiments_per_round]:
                        if not isinstance(req, dict):
                            continue
                        if req.get("kind") == "request_context":
                            extra_queries.append(str(req.get("query", ""))[:200])
                            ran_any = True
                            continue
                        r = ex.run(pending[did], req)
                        ran_any = True
                        if r.evidence is not None:
                            pending[did].evidence.append(r.evidence)
                    extra_queries += [str(q)[:200] for q in j.get("missing_context") or []]
            done = [did for did, j in last.items() if did in pending and (j["verdict"] != "NEEDS_EXPERIMENT" or not ran_any)]
            for did in done:
                results[did] = self._finalize(state, pending[did], last[did], ex)
                del pending[did]
            if not pending:
                break
        for did, d in pending.items():
            results[did] = self._finalize(state, d, last.get(did, {}), ex) if did in last else self._undecided(d, "no judgment")
        return results

    def _user_prompt(self, state, ds, ex, known, extra_queries, rnd) -> str:
        kb_ids = sorted({k for d in ds for k in d.kb_hits})
        ids = {d.id for d in ds}
        exp_lines = [f"{r.id} (for {r.discrepancy_id}) [{r.kind}] {'ok' if r.ok else 'FAILED'}: {r.summary}"
                     for r in ex.results if r.discrepancy_id in ids]
        return prompts.ADJUDICATOR_USER.format(
            case_id=state.case_id, target_python=state.target_python,
            mypy_version=state.versions.get("mypy"), mypy_flags=" ".join(state.flags.get("mypy", []) or ["(unknown)"]),
            ty_version=state.versions.get("ty"), ty_flags=" ".join(state.flags.get("ty", []) or ["(unknown)"]),
            pyright_version=state.versions.get("pyright") or "not run", runtime_version=state.runtime.python_version or "?",
            round=rnd, max_rounds=self.cfg.max_rounds, numbered_source=numbered(state.source),
            runtime_block=runtime_block(state), mypy_block=diags_block(state, Tool.MYPY), ty_block=diags_block(state, Tool.TY),
            pyright_block=diags_block(state, Tool.PYRIGHT) if state.pyright_ran else "(not run)",
            discrepancy_block=discrepancy_block(state, ds), experiment_block="\n".join(exp_lines) or "(none yet)",
            kb_block=kb_prompt_block(kb_ids) or "(no KB entries matched)",
            known_block="\n".join(known[-30:]) or "(none)",
            context_block=context_block(self.corpus, state, ds, extra_queries, self.cfg.context_chars),
        )

    # .................................................................. verification + gating
    def _verify_evidence(self, state: CaseState, d: Discrepancy, raw: list, ex: ExperimentRunner) -> list[Evidence]:
        out: list[Evidence] = []
        exp_ids = {r.id for r in ex.results}
        harness_runtime = [e for e in d.evidence if e.type == EvidenceType.RUNTIME and e.verified]
        for item in raw or []:
            if not isinstance(item, dict):
                continue
            etype = item.get("type") if item.get("type") in _EVIDENCE else "HEURISTIC"
            ev = Evidence(EvidenceType(etype), str(item.get("supports", "neutral")),
                          str(item.get("explanation", ""))[:600], citation=str(item.get("citation", ""))[:200],
                          quote=str(item.get("quote", ""))[:1200])
            cit = ev.citation
            if ev.type in (EvidenceType.SPEC, EvidenceType.DOC, EvidenceType.CONFORMANCE):
                ev.verified = bool(ev.quote) and self.corpus.verify_quote(ev.quote)
                ev.strength = "strong" if ev.verified else "weak"
                if not ev.verified:
                    ev.summary = "[UNVERIFIED QUOTE - ignored] " + ev.summary
            elif ev.type == EvidenceType.KB:
                kid = cit.removeprefix("KB:")
                ev.verified = kid in BY_ID and kid in d.kb_hits and kb_entry_eligible(state, d, BY_ID[kid])
                ev.strength = "medium" if ev.verified else "weak"
            elif ev.type in (EvidenceType.EXPERIMENT, EvidenceType.SELF_CONTRADICTION):
                cited = {tok.strip(" ,;()") for tok in cit.split()} & exp_ids
                det = [e for e in d.evidence if e.type == ev.type and e.verified and e.supports == ev.supports]
                if ev.type == EvidenceType.EXPERIMENT:
                    # the cited experiment must exist for THIS discrepancy and really record the claimed direction
                    ok = any(r.id in cited and r.ok and r.discrepancy_id == d.id and
                             (r.evidence.supports == ev.supports if r.evidence is not None else ev.supports == "neutral")
                             for r in ex.results)
                    ev.verified = bool(cited) and ok
                else:
                    ev.verified = bool(cited) and bool(det)
                ev.strength = "strong" if ev.verified and ev.type == EvidenceType.SELF_CONTRADICTION else (
                    "medium" if ev.verified else "weak")
            elif ev.type == EvidenceType.RUNTIME:
                ev.verified = any(h.supports == ev.supports for h in harness_runtime)
                ev.strength = "strong" if ev.verified else "weak"
            else:
                ev.strength = "weak"
            out.append(ev)
        return out

    def _finalize(self, state: CaseState, d: Discrepancy, j: dict, ex: ExperimentRunner) -> Finding:
        verdict = Verdict(j.get("verdict", "NEEDS_HUMAN"))
        evid = list(d.evidence) + self._verify_evidence(state, d, j.get("evidence"), ex)
        f = Finding(
            discrepancy_id=d.id, verdict=verdict, tier=Tier.REVIEW, faulty_tool=str(j.get("faulty_tool", "unknown")),
            symptom=Symptom(j["symptom"]) if j.get("symptom") in _SYMPTOMS else None,
            dismissal=Dismissal(j["dismissal"]) if j.get("dismissal") in _DISMISSALS else None,
            confidence=float(j.get("confidence", 0.0)), decided_by="llm" + ("+experiments" if ex.results else ""),
            reasoning=str(j.get("reasoning", ""))[:1200], correct_behavior=str(j.get("correct_behavior", ""))[:400],
            counter_hypothesis=str(j.get("counter_hypothesis", ""))[:800], evidence=evid,
            experiments=[{"id": r.id, "kind": r.kind, "ok": r.ok, "summary": r.summary} for r in ex.for_discrepancy(d.id)],
        )
        if self.cfg.votes > 1 and verdict in (Verdict.BUG, Verdict.NOT_BUG):
            self._vote(state, d, f, ex)
        if f.verdict == Verdict.BUG:
            self._skeptic(state, d, f)
        elif f.verdict == Verdict.NOT_BUG and (f.confidence < self.cfg.advocate_below or d.id in state.audited):
            self._advocate(state, d, f)
        if d.id in state.audited:
            f.review_notes.append("AUDIT: KB auto-dismissal re-examined; compare verdicts to estimate the KB false-dismissal rate")
        return self.gate(f)

    def gate(self, f: Finding) -> Finding:
        """Asymmetric gate: cheap to send to a human, expensive to auto-dismiss, more expensive to auto-report."""
        bug_ev = [e for e in f.evidence if e.supports == "bug" and e.verified and e.type in STRONG_BUG_EVIDENCE]
        dis_ev = [e for e in f.evidence if e.supports == "not_bug" and e.verified and e.type in DISMISSAL_EVIDENCE]
        opposed = any(n.startswith(("SKEPTIC:WORKING_AS_INTENDED", "SKEPTIC:KNOWN_LIMITATION", "SKEPTIC:INVALID_REPRO",
                                    "SKEPTIC:WRONG_TOOL")) for n in f.review_notes)
        reopened = any(n.startswith("ADVOCATE:REOPEN") for n in f.review_notes)
        # fail closed: a missing / invalid review pass can never help a finding reach CONFIRMED or DISMISSED
        skeptic_done = any(n.startswith("SKEPTIC:") and not n.startswith("SKEPTIC:UNAVAILABLE") for n in f.review_notes)
        advocate_done = any(n.startswith("ADVOCATE:") and not n.startswith("ADVOCATE:UNAVAILABLE") for n in f.review_notes)
        advocate_needed = f.confidence < self.cfg.advocate_below or any(n.startswith("AUDIT:") for n in f.review_notes)
        if f.verdict == Verdict.BUG:
            if bug_ev and f.confidence >= self.cfg.confirm_bug and not opposed and skeptic_done:
                f.tier = Tier.CONFIRMED
            elif bug_ev and f.confidence >= self.cfg.candidate_bug and not opposed:
                f.tier = Tier.CANDIDATE
                if not skeptic_done:
                    f.review_notes.append("GATE: skeptic pass unavailable/invalid - capped at CANDIDATE")
            else:
                f.tier = Tier.REVIEW
                f.review_notes.append("GATE: BUG verdict lacks verified strong evidence or was contested")
        elif f.verdict == Verdict.NOT_BUG:
            if dis_ev and f.confidence >= self.cfg.dismiss and not reopened and (advocate_done or not advocate_needed):
                f.tier = Tier.DISMISSED
            else:
                f.tier = Tier.REVIEW
                f.review_notes.append("GATE: dismissal lacks verified evidence, has low confidence, or was reopened")
        else:
            f.tier = Tier.REVIEW
        return f

    def _undecided(self, d: Discrepancy, why: str) -> Finding:
        return Finding(d.id, Verdict.NEEDS_HUMAN, Tier.REVIEW, "unknown", None, None, 0.0, "gate", reasoning=why,
                       evidence=list(d.evidence))

    # .................................................................. adversarial review
    def _review_user(self, state: CaseState, d: Discrepancy, f: Finding) -> str:
        claim = (f"{f.verdict.value}: faulty_tool={f.faulty_tool} symptom={f.symptom.value if f.symptom else None} "
                 f"dismissal={f.dismissal.value if f.dismissal else None}\nreasoning: {f.reasoning}\n"
                 f"correct behaviour claimed: {f.correct_behavior}")
        stmt = "\n".join(f"  {x.short()}" for x in d.mypy + d.ty + d.pyright) or "  (none)"
        return prompts.SKEPTIC_USER.format(
            claim=claim, numbered_source=numbered(state.source), runtime_block=runtime_block(state),
            statement_diags=stmt, evidence_block=evidence_lines(f.evidence),
            kb_block=kb_prompt_block(d.kb_hits) or "(none)",
            context_block=context_block(self.corpus, state, [d], [f.reasoning[:200]], self.cfg.context_chars // 2),
        )

    def _skeptic(self, state: CaseState, d: Discrepancy, f: Finding) -> None:
        tool = f.faulty_tool if f.faulty_tool in ("ty", "mypy") else "ty and mypy"
        obj = complete_json(self.llm, prompts.SKEPTIC_SYSTEM.format(tool=tool), self._review_user(state, d, f),
                            lambda o: [] if isinstance(o, dict) and "decision" in o else ["need 'decision'"])
        if obj.get("_null") or obj.get("_invalid"):
            f.review_notes.append("SKEPTIC:UNAVAILABLE")
            return
        decision = str(obj.get("decision", "UNSURE"))
        quote = str(obj.get("quote", ""))
        cited_kb = str(obj.get("citation", "")).removeprefix("KB:")
        backed = (quote and self.corpus.verify_quote(quote)) or (cited_kb in BY_ID and cited_kb in d.kb_hits)
        if decision in ("WORKING_AS_INTENDED", "KNOWN_LIMITATION") and not backed:
            decision = "UNSURE"  # unsupported "intended" claims do not block, but are recorded
        f.review_notes.append(f"SKEPTIC:{decision}: {str(obj.get('argument', ''))[:400]}"
                              + (f" | would accept if: {obj.get('would_accept_report_if')}" if obj.get("would_accept_report_if") else ""))
        if decision == "UNSURE":
            f.confidence = min(f.confidence, 0.84)  # cannot be CONFIRMED without a human

    def _advocate(self, state: CaseState, d: Discrepancy, f: Finding) -> None:
        system = prompts.ADVOCATE_SYSTEM.format(dismissal=f.dismissal.value if f.dismissal else "NOT_BUG")
        obj = complete_json(self.llm, system, self._review_user(state, d, f),
                            lambda o: [] if isinstance(o, dict) and "decision" in o else ["need 'decision'"])
        if obj.get("_null") or obj.get("_invalid"):
            f.review_notes.append("ADVOCATE:UNAVAILABLE")
            return
        decision = str(obj.get("decision", "UPHOLD_DISMISSAL"))
        f.review_notes.append(f"ADVOCATE:{decision}: {str(obj.get('argument', ''))[:400]}"
                              + (f" | suggested experiment: {json.dumps(obj.get('suggested_experiment'))}"
                                 if obj.get("suggested_experiment") else ""))

    def _vote(self, state: CaseState, d: Discrepancy, f: Finding, ex: ExperimentRunner) -> None:
        user = self._user_prompt(state, [d], ex, [], [], self.cfg.max_rounds)
        verdicts = [f.verdict.value]
        for seed in range(1, self.cfg.votes):
            obj = complete_json(self.llm, prompts.ADJUDICATOR_SYSTEM, user, make_validator({d.id}), temperature=0.7, seed=seed)
            for j in obj.get("judgments", []) if isinstance(obj, dict) else []:
                if j.get("discrepancy_id") == d.id:
                    verdicts.append(j.get("verdict"))
        decisive = [v for v in verdicts if v in ("BUG", "NOT_BUG")]
        if len(set(decisive)) > 1 or len(decisive) * 2 <= len(verdicts):
            f.review_notes.append(f"VOTE: inconsistent verdicts {verdicts}")
            f.verdict = Verdict.NEEDS_HUMAN
