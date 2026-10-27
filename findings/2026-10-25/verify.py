"""Replay the findings and controls; run from the repository root.

    PYTHONPATH=. /path/to/venv/bin/python findings/2026-10-25/verify.py --out runs/verification

Uses typediff's isolated checker runners, then executes each program directly with
CPython, independently of runtime_harness.py. No LLM or external API is used.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from typediff.models import Tool
from typediff.runners import Runners, ToolConfig


HERE = Path(__file__).resolve().parent


def cases() -> dict[str, str]:
    variadic = (HERE / "variadic_callback.py").read_text()
    closure = (HERE / "lambda_rebinding.py").read_text()
    return {
        "variadic_bad_type": variadic,
        "variadic_good_type": variadic.replace('"bad"', "1"),
        "variadic_extra_argument": variadic.replace('"bad"', "1, 2"),
        "variadic_missing_argument": variadic.replace(', "bad"', ""),
        "direct_bad_type": variadic.replace('invoke(increment, "bad")', 'increment("bad")'),
        "paramspec_bad_type": variadic.replace("[*Ts, R]", "[**P, R]").replace(
            "Callable[[*Ts], R], *args: *Ts", "Callable[P, R], *args: P.args, **kwargs: P.kwargs"
        ).replace("fn(*args)", "fn(*args, **kwargs)"),
        "tuple_bad_type": variadic.replace("*args: *Ts", "args: tuple[*Ts]").replace(
            'invoke(increment, "bad")', 'invoke(increment, ("bad",))'
        ),
        "legacy_variadic_bad_type": variadic.replace(
            "from collections.abc import Callable",
            'from collections.abc import Callable\nfrom typing import TypeVar, TypeVarTuple, Unpack\n'
            'Ts = TypeVarTuple("Ts")\nR = TypeVar("R")',
        ).replace("invoke[*Ts, R]", "invoke").replace(
            "Callable[[*Ts], R]", "Callable[[Unpack[Ts]], R]"
        ).replace("*args: *Ts", "*args: Unpack[Ts]"),
        "lambda_rebinding": closure,
        "lambda_annotated": closure.replace("callback =", "callback: Callable[[], int] ="),
        "lambda_no_rebinding": closure.replace("    value = None\n", ""),
        "nested_def_rebinding": closure.replace(
            "    callback = lambda: value + 1",
            "    def callback() -> int:\n        return value + 1",
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    runners = Runners(ToolConfig(python_version="3.13", timeout_s=30))
    versions = {tool: runners.version(tool) for tool in ("mypy", "ty", "pyright", "runtime")}
    results = []
    for name, source in cases().items():
        (args.out / f"{name}.py").write_text(source)
        row = {"name": name, "tools": {}}
        for tool in (Tool.MYPY, Tool.TY, Tool.PYRIGHT):
            checked = runners.check(tool, source)
            row["tools"][tool.value] = {
                "exit_code": checked.run.exit_code,
                "flags": checked.run.flags,
                "stdout": checked.run.stdout,
                "stderr": checked.run.stderr,
                "crash_kinds": [crash.kind for crash in checked.crashes],
            }
        strict = runners.check(Tool.MYPY, source, ["--strict"])
        row["mypy_strict"] = {
            "exit_code": strict.run.exit_code,
            "stdout": strict.run.stdout,
            "stderr": strict.run.stderr,
        }
        with tempfile.TemporaryDirectory(prefix="typediff-direct-") as workdir:
            program = Path(workdir) / "case.py"
            program.write_text(source)
            runtime = subprocess.run(
                [sys.executable, str(program)], cwd=workdir,
                capture_output=True, text=True, timeout=10,
            )
        row["runtime"] = {
            "exit_code": runtime.returncode, "stdout": runtime.stdout, "stderr": runtime.stderr,
        }
        results.append(row)
        print(name, {t: r["exit_code"] for t, r in row["tools"].items()},
              f"mypy_strict={strict.run.exit_code} runtime={runtime.returncode}", flush=True)
    (args.out / "results.json").write_text(json.dumps({"versions": versions, "cases": results}, indent=2) + "\n")


if __name__ == "__main__":
    main()
