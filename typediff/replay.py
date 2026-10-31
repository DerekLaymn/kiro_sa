"""Re-adjudicate a saved case report without re-running the checkers.

KB entries, matchers, evidence rules and normalisation only affect the deterministic adjudication, not the raw
tool output. A saved report already holds the parsed diagnostics, the CPython runtime result, crashes, flags and tool
versions, so the judgement stage can be replayed from it. Experiments that need a live toggle (config-toggle verify
entries, probes) still run the checkers when a ``Runners`` is passed, exactly as in a full run.

A report is only replayable while the parsers, the runtime harness, the tool versions and the flags are unchanged;
``stale()`` compares the report's recorded versions/flags with the current ones.
"""

from __future__ import annotations

from .models import Crash, Diagnostic, RuntimeProbe, RuntimeResult, Severity, Tool
from .state import CaseState


def _diag(o: dict) -> Diagnostic:
    return Diagnostic(Tool(o["tool"]), o["line"], o["col"], Severity(o["severity"]), o["code"], o["message"],
                      o.get("end_line"), o.get("end_col"), o.get("revealed_type"), o.get("anchor"), o.get("raw", ""))


def _runtime(o: dict) -> RuntimeResult:
    return RuntimeResult(
        status=o["status"], exc_type=o.get("exc_type"), exc_message=o.get("exc_message"), exc_line=o.get("exc_line"),
        frames=[(int(a), b) for a, b in o.get("frames", [])], executed_lines=o.get("executed_lines"),
        probes=[RuntimeProbe(p["line"], p["shape"]) for p in o.get("probes", [])], stdout=o.get("stdout", ""),
        stderr=o.get("stderr", ""), python_version=o.get("python_version"))


def state_from_report(r: dict, runners=None) -> CaseState:
    diags = {Tool(t): [_diag(x) for x in lst] for t, lst in r["diagnostics"].items()}
    for t in (Tool.MYPY, Tool.TY):
        diags.setdefault(t, [])
    crashes = [Crash(Tool(c["tool"]), c["kind"], c["signature"], c["excerpt"], c.get("exit_code")) for c in r["crashes"]]
    pyright_ran = Tool.PYRIGHT in diags
    return CaseState(r["case_id"], r["source"], r["target_python"], diags, _runtime(r["runtime"]), crashes, r["flags"],
                     r["tool_versions"], runners=runners, use_pyright=pyright_ran, pyright_ran=pyright_ran)


def readjudicate(pipeline, r: dict):
    """Return a fresh CaseReport for the saved report ``r`` (a dict loaded from <case>.json)."""
    from .pipeline import Pipeline

    assert isinstance(pipeline, Pipeline)
    state = state_from_report(r, pipeline.runners)
    return pipeline._judge(state)


def stale(r: dict, current_versions: dict[str, str | None], current_flags: dict[str, list[str]]) -> bool:
    return r["tool_versions"] != current_versions or r["flags"] != current_flags
