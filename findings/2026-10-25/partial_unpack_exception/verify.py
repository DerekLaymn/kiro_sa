"""Generate controls and record checker outputs plus direct CPython execution.

Run from the repository root, using the interpreter next to the desired checkers:
    PYTHONPATH=. /path/to/python findings/2026-10-25/partial_unpack_exception/verify.py --out runs/unpack
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


def generate() -> dict[str, str]:
    source = Path(__file__).with_name("repro.py").read_text()
    return {
        "nested_tuple": source,
        "nested_list": source.replace('value, (a, b) = "bad", items', '[value, [a, b]] = ["bad", items]'),
        "nested_second_success": source.replace("run((1,))", "run((1, 2))"),
        "nested_fail_before_rebind": source.replace('value, (a, b) = "bad", items', '(a, b), value = items, "bad"'),
        "separate_assignments": source.replace('        value, (a, b) = "bad", items',
                                                '        value = "bad"\n        a, b = items'),
        "none_instead_of_str": source.replace("int | str", "int | None").replace('"bad"', "None"),
        "object_annotation": source.replace("int | str", "object"),
        "nested_three_targets": source.replace("(a, b)", "(a, b, c)"),
        "flat_subscript_failure": source.replace("    try:", "    target: list[int] = []\n    try:").replace(
            'value, (a, b) = "bad", items', 'value, target[0] = "bad", 2').replace("except ValueError:", "except IndexError:"),
        "chained_subscript_failure": source.replace("    try:", "    target: list[str] = []\n    try:").replace(
            'value, (a, b) = "bad", items', 'value = target[0] = "bad"').replace("except ValueError:", "except IndexError:"),
        "return_type": source.replace("-> None:", "-> int:").replace("print(value.bit_length())", "return value").replace(
            "\nrun((1,))", "\n    return 0\n\nprint(run((1,)).bit_length())"),
        "nested_guarded": source.replace("        print(value.bit_length())",
                                           "        if isinstance(value, int):\n            print(value.bit_length())"),
        "reveal_witness": "from typing import reveal_type\n\n" + source.replace(
            "        print(value.bit_length())", "        reveal_type(value)\n        print(value.bit_length())"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    runners = Runners(ToolConfig(python_version="3.13", timeout_s=20))
    results = []
    for name, source in generate().items():
        (args.out / f"{name}.py").write_text(source)
        row = {"name": name, "source": source, "tools": {}}
        for tool in (Tool.MYPY, Tool.TY, Tool.PYRIGHT):
            checked = runners.check(tool, source)
            row["tools"][tool.value] = {
                "exit_code": checked.run.exit_code, "flags": checked.run.flags,
                "stdout": checked.run.stdout, "stderr": checked.run.stderr,
                "crash_kinds": [crash.kind for crash in checked.crashes],
            }
        for label, tool, flags in (("mypy_strict", Tool.MYPY, ["--strict"]),
                                    ("ty_all_rules", Tool.TY, ["--error", "all"])):
            checked = runners.check(tool, source, flags)
            row[label] = {"exit_code": checked.run.exit_code, "stdout": checked.run.stdout,
                          "stderr": checked.run.stderr, "crash_kinds": [crash.kind for crash in checked.crashes]}
        with tempfile.TemporaryDirectory(prefix="typediff-unpack-") as workdir:
            path = Path(workdir) / "case.py"
            path.write_text(source)
            runtime = subprocess.run([sys.executable, str(path)], cwd=workdir,
                                     capture_output=True, text=True, timeout=10)
        row["runtime"] = {"exit_code": runtime.returncode, "stdout": runtime.stdout, "stderr": runtime.stderr}
        results.append(row)
        print(name, {tool: result["exit_code"] for tool, result in row["tools"].items()},
              f"runtime={runtime.returncode}", flush=True)
    versions = {tool: runners.version(tool) for tool in ("mypy", "ty", "pyright", "runtime")}
    (args.out / "results.json").write_text(json.dumps({"versions": versions, "cases": results}, indent=2) + "\n")


if __name__ == "__main__":
    main()
