"""Run mypy / ty / pyright / CPython on a source string with pinned, isolated settings.

Isolation matters for false-positive control: a stray ``~/.config/ty/ty.toml``, a
``pyproject.toml`` in a parent directory, a warm mypy cache or a different ``--python-version``
all create discrepancies that are pure CONFIG_ARTIFACTs.
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from .models import Crash, Diagnostic, RuntimeResult, Tool, ToolRun
from .parsers import parse_mypy, parse_pyright, parse_runtime, parse_ty, runtime_from_json

HARNESS = Path(__file__).with_name("runtime_harness.py")
FILENAME = "case.py"


def _default_cmd(env_var: str, exe: str) -> list[str]:
    if os.environ.get(env_var):
        return shlex.split(os.environ[env_var])
    local = Path(sys.executable).with_name(exe)
    if local.exists():
        return [str(local)]
    found = shutil.which(exe)
    return [found] if found else [exe]


@dataclass
class ToolConfig:
    python_version: str = "3.12"
    runtime_python: str = field(default_factory=lambda: os.environ.get("TYPEDIFF_RUNTIME_PYTHON", sys.executable))
    mypy_cmd: list[str] = field(default_factory=lambda: _default_cmd("TYPEDIFF_MYPY", "mypy"))
    ty_cmd: list[str] = field(default_factory=lambda: _default_cmd("TYPEDIFF_TY", "ty"))
    pyright_cmd: list[str] = field(default_factory=lambda: _default_cmd("TYPEDIFF_PYRIGHT", "pyright"))
    timeout_s: int = 120
    runtime_timeout_s: int = 10
    use_pyright: bool = True
    shared_typeshed: str | None = None  # path to a typeshed checkout used by BOTH checkers (removes stub skew)
    # Baseline flags. mypy gets --check-untyped-defs because ty always checks unannotated bodies
    # (docs/coming-from-mypy-or-pyright.md); everything else stays at each tool's defaults.
    mypy_flags: list[str] = field(default_factory=lambda: [
        "--check-untyped-defs", "--show-column-numbers", "--show-error-codes", "--show-error-end",
        "--no-error-summary", "--no-color-output", "--hide-error-context", "--no-incremental",
    ])
    ty_flags: list[str] = field(default_factory=lambda: ["--output-format", "concise", "--no-progress", "--color", "never"])
    pyright_flags: list[str] = field(default_factory=lambda: ["--outputjson"])

    def flags_for(self, tool: Tool) -> list[str]:
        if tool == Tool.MYPY:
            extra = ["--custom-typeshed-dir", self.shared_typeshed] if self.shared_typeshed else []
            return ["--python-version", self.python_version, *self.mypy_flags, *extra]
        if tool == Tool.TY:
            extra = ["--typeshed", self.shared_typeshed] if self.shared_typeshed else []
            return ["--python-version", self.python_version, *self.ty_flags, *extra]
        return ["--pythonversion", self.python_version, *self.pyright_flags]


@dataclass
class CheckResult:
    run: ToolRun
    diagnostics: list[Diagnostic]
    crashes: list[Crash]


class Runners:
    def __init__(self, cfg: ToolConfig | None = None):
        self.cfg = cfg or ToolConfig()
        self._versions: dict[str, str | None] = {}

    # ------------------------------------------------------------------ infra
    def _workdir(self) -> tempfile.TemporaryDirectory:
        return tempfile.TemporaryDirectory(prefix="typediff-")

    def _env(self, workdir: str) -> dict[str, str]:
        env = {k: v for k, v in os.environ.items() if k not in (
            "VIRTUAL_ENV", "CONDA_PREFIX", "PYTHONPATH", "TY_CONFIG_FILE", "TY_LOG", "TY_OUTPUT_FORMAT", "MYPYPATH",
            "MYPY_CONFIG_FILE_DIR",
        )}
        env["XDG_CONFIG_HOME"] = os.path.join(workdir, ".xdg")  # ignore user-level ty.toml
        env["MYPY_CACHE_DIR"] = os.path.join(workdir, ".mypy_cache")
        env["NO_COLOR"] = "1"
        return env

    def _exec(self, cmd: list[str], workdir: str, timeout: int) -> tuple[str, str, int | None, float]:
        t0 = time.monotonic()
        try:
            p = subprocess.run(cmd, cwd=workdir, env=self._env(workdir), capture_output=True, text=True, timeout=timeout)
            return p.stdout, p.stderr, p.returncode, time.monotonic() - t0
        except subprocess.TimeoutExpired as exc:
            out = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            return out, f"TIMEOUT after {timeout}s", None, time.monotonic() - t0
        except FileNotFoundError as exc:
            return "", f"NOT INSTALLED: {exc}", 127, 0.0

    def available(self, tool: Tool) -> bool:
        return self.version(tool) is not None

    def version(self, tool: Tool | str) -> str | None:
        key = tool.value if isinstance(tool, Tool) else tool
        if key in self._versions:
            return self._versions[key]
        cmds = {
            "mypy": [*self.cfg.mypy_cmd, "--version"],
            "ty": [*self.cfg.ty_cmd, "version"],
            "pyright": [*self.cfg.pyright_cmd, "--version"],
            "runtime": [self.cfg.runtime_python, "-c", "import sys; print(sys.version.split()[0])"],
        }
        with self._workdir() as wd:
            out, err, code, _ = self._exec(cmds[key], wd, 180)
        self._versions[key] = out.strip().splitlines()[-1] if code == 0 and out.strip() else None
        return self._versions[key]

    # ------------------------------------------------------------------ checkers
    def check(self, tool: Tool, source: str, extra_flags: list[str] | None = None) -> CheckResult:
        flags = self.cfg.flags_for(tool) + list(extra_flags or [])
        base = {Tool.MYPY: self.cfg.mypy_cmd, Tool.TY: [*self.cfg.ty_cmd, "check"], Tool.PYRIGHT: self.cfg.pyright_cmd}[tool]
        with self._workdir() as wd:
            Path(wd, FILENAME).write_text(source, encoding="utf-8")
            if tool == Tool.MYPY:
                flags = [*flags, "--cache-dir", os.path.join(wd, ".mypy_cache")]
            out, err, code, dur = self._exec([*base, *flags, FILENAME], wd, self.cfg.timeout_s)
        run = ToolRun(tool, out, err, code, self.version(tool), flags, dur)
        parser = {Tool.MYPY: parse_mypy, Tool.TY: parse_ty, Tool.PYRIGHT: parse_pyright}[tool]
        diags, crashes = parser(out, err, code, FILENAME)
        if code is None:
            crashes.append(Crash(tool, "timeout", f"{tool.value}:timeout", err, None))
        if code == 127 and "NOT INSTALLED" in err:
            crashes = []  # missing tool is an environment problem, not a checker bug
        return CheckResult(run, diags, crashes)

    def check_nondeterminism(self, tool: Tool, source: str, first: CheckResult, extra_flags=None) -> Crash | None:
        second = self.check(tool, source, extra_flags)
        a = sorted(d.raw for d in first.diagnostics)
        b = sorted(d.raw for d in second.diagnostics)
        if a != b:
            diff = "\n".join(sorted(set(a) ^ set(b)))[:2000]
            return Crash(tool, "nondeterminism", f"{tool.value}:nondeterministic-output", diff, second.run.exit_code)
        return None

    # ------------------------------------------------------------------ runtime
    def run_runtime(self, source: str) -> RuntimeResult:
        with self._workdir() as wd:
            prog = Path(wd, FILENAME)
            prog.write_text(source, encoding="utf-8")
            out_json = Path(wd, "runtime.json")
            cmd = [self.cfg.runtime_python, "-I", str(HARNESS), str(prog), str(out_json), str(self.cfg.runtime_timeout_s)]
            out, err, code, _ = self._exec(cmd, wd, self.cfg.runtime_timeout_s + 5)
            if out_json.exists():
                try:
                    res = runtime_from_json(json.loads(out_json.read_text()))
                    res.stdout, res.stderr = out[-4000:], err[-4000:]
                    return res
                except (json.JSONDecodeError, KeyError):
                    pass
            if code is None:
                return RuntimeResult(status="timeout", stderr=err)
            res = parse_runtime(err or out, FILENAME)
            if res.status == "success":
                res.status = "harness_error"
            return res
