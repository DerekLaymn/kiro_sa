"""TYPEDIFF_TOOL_MEM_MB kills a mypy or ty process that uses too much memory (one corpus program makes mypy use many GB)."""

from __future__ import annotations

import sys
import time

import pytest

from typediff.models import Tool
from typediff.runners import MEM_ENV, Runners, ToolConfig

pytestmark = pytest.mark.skipif(not sys.platform.startswith("linux"), reason="the limit reads /proc")

# extra mypy-style flags land in sys.argv and are ignored; the bytes are written, so they count as resident memory
HUNGRY = (
    "import sys, time\n"
    "if sys.argv[1:2] in (['--version'], ['version']):  # Runners.version() calls the tool first\n"
    "    print('9.9')\n"
    "    sys.exit(0)\n"
    "b = bytearray(b'x') * (700 << 20)\n"
    "print('allocated', flush=True)\n"
    "time.sleep(60)\n"
)
SMALL = "print('fine')"


def _cfg(tool: Tool, script: str) -> ToolConfig:
    cmd = [sys.executable, "-c", script]
    return ToolConfig(mypy_cmd=cmd) if tool == Tool.MYPY else ToolConfig(ty_cmd=cmd)


@pytest.mark.parametrize("tool", [Tool.MYPY, Tool.TY])
def test_limit_kills_a_memory_hungry_checker(monkeypatch, tool):
    monkeypatch.setenv(MEM_ENV, "300")
    t0 = time.monotonic()
    res = Runners(_cfg(tool, HUNGRY)).check(tool, "x = 1\n")
    assert res.run.exit_code == -9
    assert time.monotonic() - t0 < 30  # killed by the watchdog, not by the 60 s sleep ending
    assert [c.signature for c in res.crashes] == [f"{tool.value}:signal-SIGKILL"]


def test_limit_leaves_a_normal_run_alone(monkeypatch):
    monkeypatch.setenv(MEM_ENV, "300")
    res = Runners(_cfg(Tool.MYPY, SMALL)).check(Tool.MYPY, "x = 1\n")
    assert res.run.exit_code == 0 and "fine" in res.run.stdout


def test_run_below_the_limit_is_not_killed(monkeypatch):
    monkeypatch.setenv(MEM_ENV, "4000")
    script = "b = bytearray(b'x') * (100 << 20); print('allocated')"
    res = Runners(_cfg(Tool.MYPY, script)).check(Tool.MYPY, "x = 1\n")
    assert res.run.exit_code == 0 and "allocated" in res.run.stdout


def test_missing_binary_is_still_not_installed(monkeypatch):
    monkeypatch.setenv(MEM_ENV, "300")
    res = Runners(ToolConfig(ty_cmd=["definitely-not-installed-xyz"])).check(Tool.TY, "x = 1\n")
    assert res.run.exit_code == 127 and "NOT INSTALLED" in res.run.stderr and res.crashes == []


@pytest.mark.parametrize("value", [None, "", "abc", "-5", "0"])
def test_unset_bad_or_zero_value_means_unlimited(monkeypatch, value):
    if value is None:
        monkeypatch.delenv(MEM_ENV, raising=False)
    else:
        monkeypatch.setenv(MEM_ENV, value)
    script = "b = bytearray(b'x') * (400 << 20); print('allocated')"
    res = Runners(_cfg(Tool.MYPY, script)).check(Tool.MYPY, "x = 1\n")
    assert res.run.exit_code == 0 and "allocated" in res.run.stdout


def test_timeout_still_applies_with_a_limit(monkeypatch, tmp_path):
    monkeypatch.setenv(MEM_ENV, "4000")
    out, err, code, _ = Runners()._exec([sys.executable, "-c", "import time; time.sleep(30)"], str(tmp_path), 2, 4000)
    assert code is None and err.startswith("TIMEOUT after 2s")
