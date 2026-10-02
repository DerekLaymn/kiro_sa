"""Human-readable case summaries and upstream issue drafts."""

from __future__ import annotations

from . import prompts
from .llm import complete_json
from .models import CaseReport, Finding, Tier, Tool

_TIER_ORDER = {Tier.CONFIRMED: 0, Tier.CANDIDATE: 1, Tier.REVIEW: 2, Tier.DISMISSED: 3}


def render_summary(r: CaseReport) -> str:
    by_id = {d.id: d for d in r.discrepancies}
    lines = [
        f"# typediff case {r.case_id}",
        f"target Python {r.target_python} | versions: " + ", ".join(f"{k}={v}" for k, v in r.tool_versions.items()),
        f"runtime: {r.runtime.status}" + (f" ({r.runtime.exc_type}: {r.runtime.exc_message})" if r.runtime.exc_type else ""),
        f"discrepancies: {len(r.discrepancies)} | crashes: {len(r.crashes)} | LLM calls: {r.llm_calls}",
    ]
    if r.validity.get("problems"):
        lines.append("validity notes: " + "; ".join(r.validity["problems"]))
    lines.append("")
    lines.append("| id | tier | verdict | tool | class | conf | decided by | statement |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for f in sorted(r.findings, key=lambda f: (_TIER_ORDER[f.tier], f.discrepancy_id)):
        d = by_id.get(f.discrepancy_id)
        cls = (f.symptom or f.dismissal).value if (f.symptom or f.dismissal) else "-"
        stmt = (f"L{d.anchor}: `{d.statement[:60]}`" if d else f.reasoning[:60]).replace("|", "\\|")
        lines.append(f"| {f.discrepancy_id} | {f.tier.value} | {f.verdict.value} | {f.faulty_tool} | {cls} | "
                     f"{f.confidence:.2f} | {f.decided_by} | {stmt} |")
    for f in sorted(r.findings, key=lambda f: (_TIER_ORDER[f.tier], f.discrepancy_id)):
        if f.tier == Tier.DISMISSED:
            continue
        d = by_id.get(f.discrepancy_id)
        lines += ["", f"## {f.discrepancy_id} - {f.tier.value}"]
        if d:
            lines.append(f"- kind: {d.kind.value}; mypy: {'; '.join(x.short() for x in d.mypy) or '-'}; "
                         f"ty: {'; '.join(x.short() for x in d.ty) or '-'}")
            if d.kb_hits:
                lines.append(f"- KB matches: {', '.join(d.kb_hits)}")
        if f.reasoning:
            lines.append(f"- reasoning: {f.reasoning}")
        if f.correct_behavior:
            lines.append(f"- correct behaviour: {f.correct_behavior}")
        if f.counter_hypothesis:
            lines.append(f"- counter-hypothesis: {f.counter_hypothesis}")
        for e in f.evidence:
            lines.append(f"- evidence [{e.type.value}/{e.strength}{'/verified' if e.verified else ''}, "
                         f"supports {e.supports}]: {e.summary[:300]}")
        for x in f.experiments:
            lines.append(f"- experiment {x['id']} [{x['kind']}] {'ok' if x['ok'] else 'FAILED'}: {x['summary'][:300]}")
        for n in f.review_notes:
            lines.append(f"- review: {n}")
        if f.reduced_source:
            lines += ["- reduced repro:", "```python", f.reduced_source.rstrip(), "```"]
    if r.strategy:
        s = r.strategy
        lines += ["", "## Strategy", f"- decision: **{s.decision}** ({s.decided_by}) - {s.rationale}"]
        if s.next_area:
            lines.append(f"- next area: {s.next_area}")
        for m in s.mutations:
            lines.append(f"- mutation: {m}")
        if s.next_program_brief:
            lines.append(f"- next brief: {s.next_program_brief}")
        if s.avoid_patterns:
            lines.append(f"- avoid: {'; '.join(s.avoid_patterns)}")
    if r.notes:
        lines += ["", "## Notes"] + [f"- {n}" for n in r.notes]
    return "\n".join(lines) + "\n"


def draft_issue(r: CaseReport, f: Finding, llm=None) -> str:
    d = next((x for x in r.discrepancies if x.id == f.discrepancy_id), None)
    tool = f.faulty_tool if f.faulty_tool in ("ty", "mypy") else "ty"
    other = "mypy" if tool == "ty" else "ty"
    src = f.reduced_source or r.source
    at = (lambda x: d is None or x.anchor == d.anchor)
    mine = [x.short() for x in r.diagnostics.get(tool, []) if at(x)]
    theirs = [x.short() for x in r.diagnostics.get(other, []) if at(x)]
    if d is None:  # crash
        tool_out = next((e.summary for e in f.evidence if e.type.value == "STACKTRACE"), "(crash)")
    else:
        tool_out = (f"{tool}: " + ("; ".join(mine) if mine else "no diagnostic at this statement")
                    + f"\n(for comparison, {other}: " + ("; ".join(theirs) if theirs else "no diagnostic") + ")")
    ev = "\n".join(f"- [{e.type.value}] {e.summary[:400]}" + (f'\n  > "{e.quote}"' if e.quote and e.verified else "")
                   for e in f.evidence if e.verified and e.supports == "bug" and e.strength == "strong")
    versions = ", ".join(f"{k} {v}" for k, v in r.tool_versions.items() if v)
    if llm is not None and getattr(llm, "name", "null") != "null":
        obj = complete_json(llm, prompts.REPORTER_SYSTEM.format(tool=tool), prompts.REPORTER_USER.format(
            symptom=f.symptom.value if f.symptom else "", correct=f.correct_behavior, evidence_block=ev, source=src,
            tool_output=tool_out, versions=versions), lambda o: [] if isinstance(o, dict) and o.get("body") else ["need body"])
        if obj.get("body"):
            return f"# {obj.get('title', '')}\n\n{obj['body']}\n"
    flags = " ".join(r.flags.get(tool, []))
    cmd = f"ty check {flags} case.py" if tool == "ty" else f"mypy {flags} case.py"
    if tool == "ty":
        return (f"# {f.symptom.value if f.symptom else 'Bug'}: {d.statement[:60] if d else 'panic'}\n\n### Summary\n\n"
                f"```py\n{src.rstrip()}\n```\n\nCommand: `{cmd}`\n\nActual:\n```\n{tool_out}\n```\n\n"
                f"Expected: {f.correct_behavior}\n\nEvidence:\n{ev}\n\nPlayground: <paste https://play.ty.dev link>\n\n"
                f"### Version\n\n{r.tool_versions.get('ty')}\n")
    return (f"# {f.symptom.value if f.symptom else 'Bug'}: {d.statement[:60] if d else 'crash'}\n\n**Bug Report**\n\n"
            f"{f.reasoning}\n\n**To Reproduce**\n\n```python\n{src.rstrip()}\n```\n\n**Expected Behavior**\n\n"
            f"{f.correct_behavior}\n\n**Actual Behavior**\n\n```\n{tool_out}\n```\n\nEvidence:\n{ev}\n\n"
            f"**Your Environment**\n\n- Mypy version used: {r.tool_versions.get('mypy')}\n- Mypy command-line flags: "
            f"{flags}\n- Python version used: {r.target_python}\n\nPlayground: <paste https://mypy-play.net link>\n")


def tool_key(t: Tool) -> str:
    return t.value
