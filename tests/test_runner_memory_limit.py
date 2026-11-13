"""TYPEDIFF_TOOL_MEM_MB caps the memory of mypy and ty (one corpus program makes mypy use many GB before it crashes)."""

from __future__ import annotations

import sys

import pytest

from typediff.models import Tool
from typediff.runners import MEM_ENV, Runners, ToolConfig

pytestmark = pytest.mark.skipif(not sys.platform.startswith("linux"), reason="RLIMIT_AS is enforced on Linux")

ALLOCATE = "import sys; b = bytearray(1 << 30); print('allocated')"  # 1 GiB; extra mypy-style flags land in sys.argv


def _cfg(tool: Tool, cmd: list[str]) -> ToolConfig:
    return ToolConfig(mypy_cmd=cmd) if tool == Tool.MYPY else ToolConfig(ty_cmd=cmd)


def test_default_is_unlimited(monkeypatch):
    monkeypatch.delenv(MEM_ENV, raising=False)
    res = Runners(_cfg(Tool.MYPY, [sys.executable, "-c", ALLOCATE])).check(Tool.MYPY, "x = 1\n")
    assert res.run.exit_code == 0 and "allocated" in res.run.stdout


@pytest.mark.parametrize("tool", [Tool.MYPY, Tool.TY])
def test_limit_stops_a_memory_hungry_checker(monkeypatch, tool):
    monkeypatch.setenv(MEM_ENV, "512")
    cmd = [sys.executable, "-c", ALLOCATE]
    res = Runners(_cfg(tool, cmd)).check(tool, "x = 1\n")
    assert res.run.exit_code not in (0, None) and "allocated" not in res.run.stdout
    assert "MemoryError" in res.run.stderr


def test_limit_leaves_a_normal_run_alone(monkeypatch):
    monkeypatch.setenv(MEM_ENV, "512")
    res = Runners(_cfg(Tool.MYPY, [sys.executable, "-c", "print('fine')"])).check(Tool.MYPY, "x = 1\n")
    assert res.run.exit_code == 0 and "fine" in res.run.stdout


def test_missing_binary_is_still_not_installed(monkeypatch):
    monkeypatch.setenv(MEM_ENV, "512")
    res = Runners(_cfg(Tool.TY, ["definitely-not-installed-xyz"])).check(Tool.TY, "x = 1\n")
    assert res.run.exit_code == 127 and "NOT INSTALLED" in res.run.stderr and res.crashes == []


@pytest.mark.parametrize("value", ["", "abc", "-5", "0"])
def test_bad_or_zero_value_means_unlimited(monkeypatch, value):
    monkeypatch.setenv(MEM_ENV, value)
    res = Runners(_cfg(Tool.MYPY, [sys.executable, "-c", ALLOCATE])).check(Tool.MYPY, "x = 1\n")
    assert res.run.exit_code == 0
