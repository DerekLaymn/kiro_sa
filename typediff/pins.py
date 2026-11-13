"""The tool versions every result in results/ was produced with. This is the one place that defines them;
``constraints.txt`` and the ``tools`` extra of ``pyproject.toml`` must agree (tests/test_reproducibility.py checks it)."""

from __future__ import annotations

import re
from dataclasses import dataclass

PINNED_TOOLS = {"mypy": "2.4.0", "ty": "0.0.97", "pyright": "1.1.414"}
PINNED_PYTHON = "3.13"  # major.minor of the CPython runtime oracle and of the --python-version of every run


@dataclass
class PinCheck:
    name: str
    pinned: str
    installed: str | None  # None: not installed / not runnable

    @property
    def ok(self) -> bool:
        return self.installed is not None and self.installed == self.pinned


def parse_version(output: str | None) -> str | None:
    """First dotted version number in a ``--version`` line ("mypy 2.4.0 (compiled: yes)" -> "2.4.0")."""
    m = re.search(r"\d+(?:\.\d+)+", output or "")
    return m.group(0) if m else None


def check_pins(installed: dict[str, str | None]) -> list[PinCheck]:
    """``installed`` maps mypy/ty/pyright to a raw version line and ``python`` to the runtime's version string."""
    rows = [PinCheck(t, v, parse_version(installed.get(t))) for t, v in PINNED_TOOLS.items()]
    py = parse_version(installed.get("python"))
    rows.append(PinCheck("python", PINNED_PYTHON, ".".join(py.split(".")[:2]) if py else None))
    return rows


def warnings(rows: list[PinCheck]) -> list[str]:
    out = []
    for r in rows:
        if r.installed is None:
            out.append(f"{r.name} is not installed or not runnable (pinned {r.pinned})")
        elif not r.ok:
            out.append(f"{r.name} {r.installed} is installed, results were produced with {r.pinned}")
    return out
