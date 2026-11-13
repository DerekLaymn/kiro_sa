"""Reproducibility plumbing: .env loading, API-key errors, tool-version pins, repository data for replays."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import pytest

from typediff import cli, llm
from typediff.envfile import load_dotenv, parse_env_text
from typediff.pins import PINNED_PYTHON, PINNED_TOOLS, check_pins, parse_version, warnings

ROOT = Path(__file__).resolve().parent.parent


# ----------------------------------------------------------------------------------------------- .env


def test_parse_env_text_handles_comments_quotes_export_and_empty_values():
    text = "\n".join([
        "# a comment", "A=1", "export B = two words  # trailing", 'C="quoted # not a comment"', "D='single'",
        "E=", "  F=x", "bad line", "G=a=b",
    ])
    assert parse_env_text(text) == {"A": "1", "B": "two words", "C": "quoted # not a comment", "D": "single", "F": "x", "G": "a=b"}


def test_load_dotenv_never_overrides_existing_variables(tmp_path, monkeypatch):
    f = tmp_path / ".env"
    f.write_text("TD_T_KEEP=from-file\nTD_T_NEW=from-file\nTD_T_EMPTY=\n")
    monkeypatch.setenv("TD_T_KEEP", "from-shell")
    monkeypatch.delenv("TD_T_NEW", raising=False)
    monkeypatch.delenv("TD_T_EMPTY", raising=False)
    assert load_dotenv(f) == ["TD_T_NEW"]
    assert os.environ["TD_T_KEEP"] == "from-shell"
    assert os.environ["TD_T_NEW"] == "from-file"
    assert "TD_T_EMPTY" not in os.environ
    monkeypatch.delenv("TD_T_NEW")


def test_load_dotenv_missing_file_is_not_an_error(tmp_path):
    assert load_dotenv(tmp_path / "nope.env") == []


# ----------------------------------------------------------------------------------------------- API keys


def test_anthropic_without_key_names_the_variable(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(llm.LLMConfigError, match="ANTHROPIC_API_KEY"):
        llm.from_env("anthropic:some-model")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "  ")  # blank (e.g. the empty line of .env.example) counts as missing
    with pytest.raises(llm.LLMConfigError, match="ANTHROPIC_API_KEY"):
        llm.from_env("anthropic:some-model")


def test_openai_requires_key_for_api_openai_com_only(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    with pytest.raises(llm.LLMConfigError, match="OPENAI_API_KEY"):
        llm.from_env("openai:gpt-x")
    assert llm.from_env("openai:m@http://localhost:8000/v1").inner.key == "none"  # self-hosted server, no key needed
    monkeypatch.setenv("OPENAI_BASE_URL", "http://localhost:1/v1")
    assert llm.from_env("openai:m").inner.key == "none"
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    assert llm.from_env("openai:m").inner.key == "sk-test"


def test_keys_are_read_from_the_environment(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    assert llm.from_env("anthropic:m").inner.key == "k"


def test_unknown_provider_is_an_error_not_a_silent_null(monkeypatch):
    with pytest.raises(llm.LLMConfigError, match="antropic"):
        llm.from_env("antropic:m")
    assert isinstance(llm.from_env("null").inner, llm.NullLLM)
    assert isinstance(llm.from_env("").inner, llm.NullLLM)


def test_cli_reports_missing_key_without_traceback(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    src = tmp_path / "a.py"
    src.write_text("x = 1\n")
    rc = cli.main(["--llm", "anthropic:m", "--out", str(tmp_path / "o"), "run", str(src)])
    err = capsys.readouterr().err
    assert rc == 2 and err.startswith("error: ANTHROPIC_API_KEY is not set")


def test_env_example_names_the_variables_the_code_reads():
    example = (ROOT / ".env.example").read_text()
    source = (ROOT / "typediff" / "llm.py").read_text()
    for var in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "OPENAI_BASE_URL", "TYPEDIFF_LLM", "TYPEDIFF_LLM_MIN_INTERVAL"):
        assert var in source and re.search(rf"^{var}=", example, re.M), var


# ----------------------------------------------------------------------------------------------- pins


def test_parse_version():
    assert parse_version("mypy 2.4.0 (compiled: yes)") == "2.4.0"
    assert parse_version("ty 0.0.97 (abc123 2026-11-01)") == "0.0.97"
    assert parse_version("pyright 1.1.414") == "1.1.414"
    assert parse_version("3.13.16") == "3.13.16"
    assert parse_version(None) is None and parse_version("no version") is None


def _installed(**over):
    base = {"mypy": "mypy 2.4.0 (compiled: yes)", "ty": "ty 0.0.97 (x)", "pyright": "pyright 1.1.414", "python": "3.13.16"}
    return base | over


def test_check_pins_all_match():
    rows = check_pins(_installed())
    assert all(r.ok for r in rows) and warnings(rows) == []


def test_check_pins_reports_differences_and_missing_tools():
    rows = check_pins(_installed(ty="ty 0.0.99 (y)", pyright=None, python="3.12.3"))
    msgs = warnings(rows)
    assert len(msgs) == 3
    assert any("ty 0.0.99" in m and "0.0.97" in m for m in msgs)
    assert any(m.startswith("pyright is not installed") for m in msgs)
    assert any("python 3.12" in m for m in msgs)


def test_pins_match_constraints_and_pyproject():
    constraints = (ROOT / "constraints.txt").read_text()
    pyproject = (ROOT / "pyproject.toml").read_text()
    for tool, version in PINNED_TOOLS.items():
        assert re.search(rf"^{tool}=={re.escape(version)}$", constraints, re.M), tool
        assert f'"{tool}=={version}"' in pyproject, tool
    assert f"CPython {PINNED_PYTHON}" in constraints


class _FakeRunners:
    versions: dict = {}

    def __init__(self, cfg=None):
        self.cfg = cfg

    def version(self, tool):
        return self.versions.get(tool.value if hasattr(tool, "value") else tool)


def _doctor(monkeypatch, capsys, versions, *argv):
    _FakeRunners.versions = versions
    monkeypatch.setattr(cli, "Runners", _FakeRunners)
    rc = cli.main(["--python-version", "3.13", "doctor", *argv])
    return rc, capsys.readouterr().out


def test_doctor_ok(monkeypatch, capsys):
    rc, out = _doctor(monkeypatch, capsys, {"mypy": "mypy 2.4.0", "ty": "ty 0.0.97", "pyright": "pyright 1.1.414",
                                           "runtime": "3.13.16"}, "--strict")
    assert rc == 0 and "WARNING" not in out


def test_doctor_warns_and_strict_fails(monkeypatch, capsys):
    v = {"mypy": "mypy 2.5.0", "ty": "ty 0.0.97", "pyright": None, "runtime": "3.13.16"}
    rc, out = _doctor(monkeypatch, capsys, v)
    assert rc == 0 and "WARNING: mypy 2.5.0 is installed, results were produced with 2.4.0" in out and "MISSING" in out
    rc, _ = _doctor(monkeypatch, capsys, v, "--strict")
    assert rc == 1


# ----------------------------------------------------------------------------------------------- repository data


def test_harvest_default_output_is_independent_of_cwd():
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import harvest_seeds
    finally:
        sys.path.pop(0)
    assert harvest_seeds.REPO_ROOT == ROOT


def test_reproduce_script_is_strict_bash_and_relative():
    script = ROOT / "scripts" / "reproduce.sh"
    text = script.read_text()
    assert text.startswith("#!/usr/bin/env bash") and "set -euo pipefail" in text
    assert "/home/" not in text and os.access(script, os.X_OK)


def test_parent_seeds_are_tracked_and_have_headers():
    parents = sorted((ROOT / "seeds" / "parents").glob("*.py"))
    assert len(parents) >= 30
    assert all(p.read_text().startswith("# area:") for p in parents)


def test_bug_reproducers_cover_all_twelve_drafts():
    readme = (ROOT / "examples" / "bugs" / "README.md").read_text()
    files = sorted((ROOT / "examples" / "bugs").glob("*.py"))
    assert [f.name[:2] for f in files] == [f"{i:02d}" for i in range(1, 13)]
    for f in files:
        if sys.version_info >= (3, 13):  # drafts 1 and 5 use PEP 695/696 syntax
            compile(f.read_text(), str(f), "exec")
        assert f.name in readme


def test_day10_replay_data_is_complete():
    base = ROOT / "examples" / "replay" / "day10"
    answers = list((base / "answers").glob("*.answer.json"))
    assert len(answers) == 250 and all(re.fullmatch(r"[0-9a-f]{16}", a.name.split(".")[0]) for a in answers)
    assert len(list((base / "parents").rglob("*.py"))) == 45
    assert sum(f.stat().st_size for f in base.rglob("*") if f.is_file()) < 5_000_000
    script = (ROOT / "scripts" / "replay_day10.sh").read_text()
    assert "set -euo pipefail" in script and "/home/" not in script


def test_no_absolute_home_paths_in_new_artifacts():
    for sub in ("examples/bugs", "seeds/parents", "examples/replay"):
        for f in (ROOT / sub).rglob("*"):
            if f.is_file() and f.suffix in {".py", ".md", ".json", ".txt"}:
                assert "/home/" not in f.read_text(errors="replace"), f
