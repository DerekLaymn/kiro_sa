"""Core data model shared by every pipeline stage.

Taxonomy (see DESIGN.md §2 for the argument behind it):

* ``Symptom``      - WHAT is wrong (only meaningful for verdict BUG)
* ``EvidenceType`` - HOW we know (drives confidence / gating)
* ``Dismissal``    - WHY it is not a reportable bug (only for verdict NOT_BUG)
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field, fields, is_dataclass
from typing import Any


class Tool(str, enum.Enum):
    MYPY = "mypy"
    TY = "ty"
    PYRIGHT = "pyright"


class Severity(str, enum.Enum):
    ERROR = "error"
    WARNING = "warning"
    NOTE = "note"  # mypy note / ty info / pyright information


class DiscrepancyKind(str, enum.Enum):
    ONLY_MYPY = "only_mypy"  # mypy reports a problem at a statement, ty is silent there
    ONLY_TY = "only_ty"  # ty reports a problem at a statement, mypy is silent there
    CONCERN_MISMATCH = "concern_mismatch"  # both report, but about unrelated things
    SEVERITY_ONLY = "severity_only"  # same concern, one says warning the other error
    REVEAL_MISMATCH = "reveal_mismatch"  # reveal_type() results disagree
    REVEAL_UNPAIRED = "reveal_unpaired"  # only one checker revealed (usually reachability)
    RUNTIME_MISS = "runtime_miss"  # CPython raised a type-related error nobody flagged


class Symptom(str, enum.Enum):
    CRASH = "CRASH"  # panic / internal error / traceback / hang / non-determinism
    FALSE_NEGATIVE = "FALSE_NEGATIVE"  # accepts code it must reject (soundness hole)
    FALSE_POSITIVE = "FALSE_POSITIVE"  # rejects code the spec permits (spurious rejection)
    INCORRECT_INFERENCE = "INCORRECT_INFERENCE"  # wrong inferred / revealed type
    DIAGNOSTIC_DEFECT = "DIAGNOSTIC_DEFECT"  # right decision, wrong location/message/code/suppression


class Dismissal(str, enum.Enum):
    DESIGN_DIVERGENCE = "DESIGN_DIVERGENCE"  # documented, intentional behaviour
    SPEC_AMBIGUITY = "SPEC_AMBIGUITY"  # spec leaves it to implementations
    KNOWN_LIMITATION = "KNOWN_LIMITATION"  # unimplemented feature / tracked check (@Todo, "None yet")
    CONFIG_ARTIFACT = "CONFIG_ARTIFACT"  # flags, python-version, optional checks, env, stubs
    INVALID_TEST = "INVALID_TEST"  # the generated program itself is broken
    NOISE = "NOISE"  # cosmetic: wording, column, severity, equivalent type spelling
    DUPLICATE = "DUPLICATE"  # same root cause already in the dataset / upstream


class EvidenceType(str, enum.Enum):
    STACKTRACE = "STACKTRACE"  # checker crashed
    RUNTIME = "RUNTIME"  # CPython behaviour (exception, probe value, coverage)
    SPEC = "SPEC"  # verbatim normative typing-spec text
    CONFORMANCE = "CONFORMANCE"  # typing conformance-suite precedent
    SELF_CONTRADICTION = "SELF_CONTRADICTION"  # same tool, equivalent programs, different result
    DOC = "DOC"  # tool's own documentation (verbatim)
    KB = "KB"  # curated knowledge-base entry
    EXPERIMENT = "EXPERIMENT"  # result of a harness experiment (config toggle, probe, ...)
    CONSENSUS = "CONSENSUS"  # pyright tie-break (weak)
    HEURISTIC = "HEURISTIC"  # anything else (weak)


STRONG_BUG_EVIDENCE = {
    EvidenceType.STACKTRACE,
    EvidenceType.RUNTIME,
    EvidenceType.SPEC,
    EvidenceType.CONFORMANCE,
    EvidenceType.SELF_CONTRADICTION,
}
DISMISSAL_EVIDENCE = {
    EvidenceType.KB,
    EvidenceType.DOC,
    EvidenceType.SPEC,
    EvidenceType.EXPERIMENT,
    EvidenceType.CONFORMANCE,
}


class Verdict(str, enum.Enum):
    BUG = "BUG"
    NOT_BUG = "NOT_BUG"
    NEEDS_EXPERIMENT = "NEEDS_EXPERIMENT"
    NEEDS_HUMAN = "NEEDS_HUMAN"


class Tier(str, enum.Enum):
    CONFIRMED = "confirmed"  # report-ready (after reduction + dedup)
    CANDIDATE = "candidate"  # probably a bug; a human should glance before filing
    REVIEW = "review"  # undecided -> human queue (never silently dropped)
    DISMISSED = "dismissed"  # not a bug, with an auditable reason


# --------------------------------------------------------------------------- records


@dataclass
class Diagnostic:
    tool: Tool
    line: int
    col: int | None
    severity: Severity
    code: str | None
    message: str
    end_line: int | None = None
    end_col: int | None = None
    revealed_type: str | None = None  # set when this is a reveal_type() result
    anchor: int | None = None  # start line of enclosing statement (filled by anchors.py)
    raw: str = ""

    @property
    def is_problem(self) -> bool:
        return self.severity in (Severity.ERROR, Severity.WARNING) and self.revealed_type is None

    def short(self) -> str:
        col = f":{self.col}" if self.col else ""
        code = f"[{self.code}]" if self.code else ""
        if self.revealed_type is not None:
            return f"L{self.line}{col} reveal -> {self.revealed_type}"
        return f"L{self.line}{col} {self.severity.value}{code} {self.message}"


@dataclass
class Crash:
    tool: Tool
    kind: str  # panic | internal_error | timeout | nondeterminism | abnormal_exit
    signature: str  # stable dedup key (panic location / last traceback frame + exc type)
    excerpt: str
    exit_code: int | None = None


@dataclass
class ToolRun:
    tool: Tool
    stdout: str
    stderr: str
    exit_code: int | None
    version: str | None = None
    flags: list[str] = field(default_factory=list)
    duration_s: float | None = None


@dataclass
class RuntimeProbe:
    line: int
    shape: dict[str, Any]  # see runtime_harness.describe()


@dataclass
class RuntimeResult:
    status: str  # success | exception | timeout | not_run | harness_error
    exc_type: str | None = None
    exc_message: str | None = None
    exc_line: int | None = None  # innermost frame inside the target file
    frames: list[tuple[int, str]] = field(default_factory=list)  # (line, function) in target file
    executed_lines: list[int] | None = None  # None = coverage unknown
    probes: list[RuntimeProbe] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    python_version: str | None = None

    @property
    def coverage_known(self) -> bool:
        return self.executed_lines is not None


@dataclass
class Evidence:
    type: EvidenceType
    supports: str  # "bug" | "not_bug" | "neutral"
    summary: str
    citation: str = ""  # KB id, doc id, URL, line number or experiment id
    quote: str = ""  # verbatim text (machine-verified for SPEC/DOC)
    verified: bool = False  # True when deterministic or quote-checked
    strength: str = "medium"  # strong | medium | weak
    blame: str | None = None  # which tool this evidence incriminates/exonerates


@dataclass
class Discrepancy:
    id: str
    kind: DiscrepancyKind
    anchor: int  # statement start line
    anchor_end: int
    statement: str  # first line of the statement (for humans + reducer)
    scope: str  # enclosing function/class qualname
    mypy: list[Diagnostic] = field(default_factory=list)
    ty: list[Diagnostic] = field(default_factory=list)
    pyright: list[Diagnostic] = field(default_factory=list)
    reveal_relation: str | None = None  # typenorm.Relation value for REVEAL_* kinds
    evidence: list[Evidence] = field(default_factory=list)
    kb_hits: list[str] = field(default_factory=list)  # KB ids that matched (hint or auto)
    features: list[str] = field(default_factory=list)  # typing constructs in the statement
    priority: float = 0.0

    def accused(self) -> str:
        """The checker whose behaviour is 'unusual' at this statement (heuristic)."""
        if self.kind == DiscrepancyKind.ONLY_MYPY:
            return "ty?mypy"  # either ty missed it or mypy is spurious
        if self.kind == DiscrepancyKind.ONLY_TY:
            return "mypy?ty"
        return "unknown"


@dataclass
class Finding:
    discrepancy_id: str
    verdict: Verdict
    tier: Tier
    faulty_tool: str  # ty | mypy | both | none | unknown
    symptom: Symptom | None
    dismissal: Dismissal | None
    confidence: float
    decided_by: str  # rule:<id> | kb:<id> | llm | llm+experiments | gate
    reasoning: str = ""
    correct_behavior: str = ""
    counter_hypothesis: str = ""
    evidence: list[Evidence] = field(default_factory=list)
    experiments: list[dict[str, Any]] = field(default_factory=list)
    review_notes: list[str] = field(default_factory=list)  # skeptic / advocate output
    reduced_source: str | None = None
    signature: str | None = None


@dataclass
class StrategyAdvice:
    decision: str  # CONTINUE | MUTATE | PIVOT | ABANDON | REPAIR_GENERATOR
    rationale: str
    feature_area: str | None = None
    next_area: str | None = None
    mutations: list[dict[str, Any]] = field(default_factory=list)
    next_program_brief: str = ""
    avoid_patterns: list[str] = field(default_factory=list)
    decided_by: str = "rules"


@dataclass
class CaseReport:
    case_id: str
    source: str
    target_python: str
    tool_versions: dict[str, str | None]
    flags: dict[str, list[str]]
    diagnostics: dict[str, list[Diagnostic]]
    runtime: RuntimeResult
    crashes: list[Crash]
    discrepancies: list[Discrepancy]
    findings: list[Finding]
    validity: dict[str, Any]
    strategy: StrategyAdvice | None = None
    llm_calls: int = 0
    notes: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------- json helpers


def to_jsonable(obj: Any) -> Any:
    """Recursively convert dataclasses/enums/tuples into JSON-compatible values."""
    if isinstance(obj, enum.Enum):
        return obj.value
    if is_dataclass(obj) and not isinstance(obj, type):
        return {f.name: to_jsonable(getattr(obj, f.name)) for f in fields(obj)}
    if isinstance(obj, dict):
        return {str(to_jsonable(k)): to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [to_jsonable(v) for v in obj]
    return obj
