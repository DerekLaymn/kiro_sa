"""End-to-end orchestration.

    judge_logs(...)  - the user-facing contract: source + mypy out/err + ty out/err + CPython result
                       (+ optional pyright JSON). Works offline; experiments only if tools are installed.
    run_source(...)  - runs every tool itself with pinned, isolated settings, then judges (full power).

Stage order (see DESIGN.md §3):
  S0 crash detection -> S1 validity -> S2 normalise + anchor -> S3 discrepancy extraction ->
  S4 deterministic evidence + auto-probes + KB -> S5 LLM adjudication with experiments ->
  S6 adversarial review + asymmetric gate -> S7 dedup + reduction -> S8 dataset + strategy
"""

from __future__ import annotations

import ast
import hashlib
import os
import re
import time
from dataclasses import dataclass, field

from .adjudicator import Adjudicator, GateConfig
from .causes import dependency_constructs
from .corpus import Corpus
from .dataset import Dataset, signature
from .discrepancy import find_discrepancies
from .experiments import ExperimentRunner
from .llm import CachedLLM, from_env
from .models import CaseReport, Crash, Dismissal, RuntimeResult, Tier, Tool, Verdict
from .parsers import classify_exception, parse_mypy, parse_pyright, parse_runtime, parse_ty
from .priors import apply_prior_cap, find_priors
from .reducer import Reducer, _norm_msg
from .rules import crash_findings, deterministic_stage, validity
from .runners import FILENAME, Runners, ToolConfig
from .state import CaseState


@dataclass
class PipelineConfig:
    tools: ToolConfig = field(default_factory=ToolConfig)
    gate: GateConfig = field(default_factory=GateConfig)
    use_pyright: bool = True
    check_nondeterminism: bool = True  # re-run ty once and compare (cheap; catches salsa/cycle flakiness)
    auto_probe: bool = True
    reduce: bool = True
    audit_rate: float = 0.05  # fraction of KB auto-dismissals re-checked by the advocate
    reducer_max_tests: int = 200


class Pipeline:
    def __init__(self, cfg: PipelineConfig | None = None, llm: CachedLLM | None = None, corpus: Corpus | None = None,
                 dataset: Dataset | None = None, runners: Runners | None = None):
        self.cfg = cfg or PipelineConfig()
        self.llm = llm or from_env()
        self.corpus = corpus or Corpus()
        self.dataset = dataset
        self.runners = runners
        self.adjudicator = Adjudicator(self.llm, self.corpus, self.cfg.gate)

    # ------------------------------------------------------------------ entry points
    def run_source(self, source: str, case_id: str | None = None) -> CaseReport:
        runners = self.runners or Runners(self.cfg.tools)
        self.runners = runners
        case_id = case_id or _case_id(source)
        diags, crashes, flags = {}, [], {}
        for tool in (Tool.MYPY, Tool.TY):
            res = runners.check(tool, source)
            diags[tool], flags[tool.value] = res.diagnostics, res.run.flags
            crashes += res.crashes
            if res.run.exit_code == 127:
                raise RuntimeError(f"{tool.value} is not installed: {res.run.stderr}")
            if tool == Tool.TY and self.cfg.check_nondeterminism and not res.crashes:
                nd = runners.check_nondeterminism(tool, source, res)
                if nd:
                    crashes.append(nd)
        pyright_ran = False
        if self.cfg.use_pyright and runners.available(Tool.PYRIGHT):
            res = runners.check(Tool.PYRIGHT, source)
            if res.run.exit_code != 127:
                diags[Tool.PYRIGHT], flags["pyright"] = res.diagnostics, res.run.flags
                pyright_ran = True
                crashes += res.crashes
        runtime = runners.run_runtime(source)
        versions = {t: runners.version(t) for t in ("mypy", "ty", "pyright", "runtime")}
        state = CaseState(case_id, source, self.cfg.tools.python_version, diags, runtime, crashes, flags, versions,
                          runners=runners, use_pyright=pyright_ran, pyright_ran=pyright_ran)
        return self._judge(state)

    def judge_logs(self, source: str, mypy_stdout: str, ty_stdout: str, runtime_text: str, *, mypy_stderr: str = "",
                   ty_stderr: str = "", mypy_exit: int | None = None, ty_exit: int | None = None,
                   pyright_json: str | None = None, flags: dict[str, list[str]] | None = None,
                   versions: dict[str, str | None] | None = None, target_python: str | None = None,
                   case_id: str | None = None, allow_experiments: bool = False) -> CaseReport:
        md, mc = parse_mypy(mypy_stdout, mypy_stderr, mypy_exit, "")
        td, tc = parse_ty(ty_stdout, ty_stderr, ty_exit, "")
        diags = {Tool.MYPY: md, Tool.TY: td}
        crashes: list[Crash] = mc + tc
        pyright_ran = False
        if pyright_json:
            pd, pc = parse_pyright(pyright_json, "", None, "")
            diags[Tool.PYRIGHT] = pd
            crashes += pc
            pyright_ran = True
        runtime = parse_runtime(runtime_text, "")
        runners = None
        if allow_experiments:
            runners = self.runners or Runners(self.cfg.tools)
            self.runners = runners
        state = CaseState(case_id or _case_id(source), source, target_python or self.cfg.tools.python_version, diags,
                          runtime, crashes, flags or {}, versions or {}, runners=runners,
                          use_pyright=pyright_ran and runners is not None, pyright_ran=pyright_ran,
                          module=_detect_module(mypy_stdout + "\n" + ty_stdout))
        if runtime.status == "success" and not runtime.coverage_known:
            state.notes.append("runtime given as plain text: no coverage/probe data (use runtime_harness.py for full power)")
        return self._judge(state)

    # ------------------------------------------------------------------ core
    def _judge(self, state: CaseState) -> CaseReport:
        calls_before = getattr(self.llm, "calls", 0)
        findings = crash_findings(state.crashes)
        crashed = {c.tool for c in state.crashes if c.kind != "nondeterminism"}
        val = validity(state)
        ex = ExperimentRunner(state)
        discrepancies = []
        if crashed & {Tool.MYPY, Tool.TY}:
            state.notes.append(f"{', '.join(t.value for t in crashed)} crashed: diagnostics are incomplete, discrepancy "
                               "analysis skipped (the crash itself is the finding)")
        else:
            discrepancies = find_discrepancies(state.diags, state.amap, state.runtime, state.module)
            decided, remaining = deterministic_stage(
                state, discrepancies, ex, auto_probe=self.cfg.auto_probe,
                audit_rate=self.cfg.audit_rate if self.adjudicator.enabled else 0.0)
            known = self.dataset.known_summaries() if self.dataset else []
            decided.update(self.adjudicator.adjudicate(state, remaining, ex, known))
            findings += [decided[d.id] for d in discrepancies if d.id in decided]

        by_id = {d.id: d for d in discrepancies}
        for f in findings:
            if f.verdict == Verdict.BUG and f.tier in (Tier.CONFIRMED, Tier.CANDIDATE):
                d = by_id.get(f.discrepancy_id)
                sig = signature(f, d)
                f.signature = sig
                # before anything is reported: has the tracker already taken a stance on something like this?
                # (known_upstream.json; a near-match by signature or feature tags caps the finding at REVIEW)
                if apply_prior_cap(f, find_priors(state.source, d)):
                    continue
                dup = self.dataset.duplicate_of(sig) if self.dataset else None
                if dup:
                    f.tier, f.dismissal = Tier.DISMISSED, Dismissal.DUPLICATE
                    f.review_notes.append(f"DUPLICATE of {dup}")
                    continue
                if self.cfg.reduce and state.online:
                    f.reduced_source = self._reduce(state, f, d)
        return CaseReport(
            case_id=state.case_id, source=state.source, target_python=state.target_python, tool_versions=state.versions,
            flags=state.flags, diagnostics={t.value: v for t, v in state.diags.items()}, runtime=state.runtime,
            crashes=state.crashes, discrepancies=discrepancies, findings=findings, validity=val,
            llm_calls=getattr(self.llm, "calls", 0) - calls_before, notes=state.notes,
        )

    def _reduce(self, state: CaseState, f, d) -> str | None:
        red = Reducer(state.runners, state.module, self.cfg.reducer_max_tests)
        crash = next((c for c in state.crashes if c.signature == f.signature), None)
        try:
            if crash:
                pred = red.predicate_for(state.source, None, f, crash.signature, crash.tool)
                return red.reduce(state.source, pred)
            if d is None:
                return None
            pred = red.predicate_for(state.source, d, f, runtime=state.runtime)
            st = state.amap.stmt(d.anchor)
            from .anchors import statement_key

            key = statement_key(st.node) if st and st.node is not None else None
            reduced = red.reduce(state.source, pred, key)
            self._check_runtime_kept(state, f, reduced)
            return reduced
        except Exception as exc:  # noqa: BLE001 - reduction is best effort
            state.notes.append(f"reduction failed: {exc}")
            return None

    def _check_runtime_kept(self, state: CaseState, f, reduced: str) -> None:
        """Say so when the reduced repro no longer raises what the original program raised. Runtime evidence then
        applies to the original program only, and the issue draft must not claim a crash for the reduced one."""
        rt = state.runtime
        if rt.status != "exception" or classify_exception(rt.exc_type, rt.exc_message) != "strong" or reduced == state.source:
            return
        new = state.runners.run_runtime(reduced)
        if new.status == "exception" and (new.exc_type, _norm_msg(new.exc_message)) == (rt.exc_type, _norm_msg(rt.exc_message)):
            return
        st = state.amap.stmt(rt.exc_line) if rt.exc_line else None
        deps = dependency_constructs(state.amap.tree, st.node if st else None, state.amap.lines)
        kept = ast.unparse(ast.parse(reduced)) if reduced.strip() else ""
        lost = [x for x in deps if (m := re.search(r"`(\w+)", x)) and m.group(1) not in kept]
        f.review_notes.append(
            f"REDUCER:RUNTIME-LOST: the reduced repro does NOT raise {rt.exc_type}: {rt.exc_message} (it ends with "
            f"{new.status}{' ' + str(new.exc_type) if new.exc_type else ''}); the runtime evidence belongs to the original "
            "program only" + (f"; dependency constructs no longer present: {'; '.join(lost)}" if lost else ""))


def _case_id(source: str) -> str:
    return time.strftime("%Y%m%d-%H%M%S-") + hashlib.sha256(source.encode()).hexdigest()[:8]


def _detect_module(text: str) -> str:
    """Module name mypy uses in revealed types (``<stem>.Foo``) = stem of the checked file."""
    m = re.search(r"^(?:\s*-->\s)?([^\s:]+?)\.pyi?:\d+", text, re.M)
    return os.path.basename(m.group(1)) if m else "case"


__all__ = ["Pipeline", "PipelineConfig", "RuntimeResult", "FILENAME"]
