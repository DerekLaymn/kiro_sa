"""Mutable per-case state shared by rules, KB matchers, experiments and the LLM stage."""

from __future__ import annotations

import ast
import builtins
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .anchors import AnchorMap
from .models import Crash, Diagnostic, RuntimeResult, Tool

if TYPE_CHECKING:
    from .runners import Runners


@dataclass
class CaseState:
    case_id: str
    source: str
    target_python: str
    diags: dict[Tool, list[Diagnostic]]
    runtime: RuntimeResult
    crashes: list[Crash]
    flags: dict[str, list[str]]
    versions: dict[str, str | None]
    runners: "Runners | None" = None  # None = offline (logs only, no experiments)
    use_pyright: bool = False
    pyright_ran: bool = False
    module: str = "case"
    amap: AnchorMap = field(init=False)
    probe_cache: dict[str, Any] = field(default_factory=dict)  # discrepancy id -> reveal_probe outcome
    audited: set[str] = field(default_factory=set)  # KB auto-dismissals sampled for LLM/advocate audit
    notes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.amap = AnchorMap(self.source)
        tree = self.amap.tree
        self.nominal_classes: set[str] = set()
        self.defined_callables: set[str] = set()
        self.unannotated_functions: set[str] = set()
        if tree:
            for n in ast.walk(tree):
                if isinstance(n, ast.ClassDef):
                    self.defined_callables.add(n.name)
                    bases = {getattr(b, "id", getattr(b, "attr", "")) for b in n.bases}
                    if not bases & {"Protocol", "TypedDict", "NamedTuple"}:
                        self.nominal_classes.add(n.name)
                elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self.defined_callables.add(n.name)
                    args = [*n.args.posonlyargs, *n.args.args, *n.args.kwonlyargs, n.args.vararg, n.args.kwarg]
                    if n.returns is None and all(a is None or a.annotation is None for a in args):
                        self.unannotated_functions.add(n.name)
        self.builtin_names = set(dir(builtins)) | {"reveal_type", "assert_type"}

    @property
    def online(self) -> bool:
        return self.runners is not None

    def mypy_checked_untyped_defs(self) -> bool | None:
        fl = self.flags.get("mypy")
        if fl is None:
            return None
        return "--check-untyped-defs" in fl or "--strict" in fl
