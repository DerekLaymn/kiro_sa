"""Parse raw checker / runtime output into the common Diagnostic / Crash / RuntimeResult model.

Formats handled (calibrated against mypy 2.4, ty 0.0.84, pyright 1.1.414):

* mypy  text   ``f.py:12:5:12:9: error: Message  [code]``  (end position optional)
* mypy  json   ``-O json``: one JSON object per line, 0-based columns
* ty    concise ``f.py:12:5: error[rule] Message``
* ty    full    ``error[rule]: Message`` followed by `` --> f.py:12:5``
* ty    gitlab  JSON array (Code Quality report)
* pyright ``--outputjson`` (0-based lines/columns)
* runtime: JSON written by runtime_harness.py, *or* a raw CPython traceback / "Success" string
"""

from __future__ import annotations

import json
import os
import re

from .models import Crash, Diagnostic, RuntimeProbe, RuntimeResult, Severity, Tool

# --------------------------------------------------------------------------- helpers


def _same_file(reported: str, target: str) -> bool:
    if not target:
        return True
    rb, tb = os.path.basename(reported.strip()), os.path.basename(target)
    return rb == tb or reported.strip() in ("<string>", target)


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text or "")


# --------------------------------------------------------------------------- mypy

_MYPY_LINE = re.compile(
    r"^(?P<file>[^\n]+?):(?P<line>\d+):(?:(?P<col>\d+):)?(?:(?P<eline>\d+):(?P<ecol>\d+):)?\s*"
    r"(?P<sev>error|warning|note):\s(?P<msg>.*?)(?:\s\s\[(?P<code>[a-z0-9-]+)\])?$"
)
_MYPY_REVEAL = re.compile(r'^Revealed type is "(?P<t>.*)"$')
_PY_FRAME = re.compile(r'^\s*File "(?P<file>[^"]+)", line (?P<line>\d+), in (?P<func>.+)$')


def _mypy_crash(stdout: str, stderr: str, exit_code: int | None) -> list[Crash]:
    blob = f"{stdout}\n{stderr}"
    if "INTERNAL ERROR" not in blob and "Traceback (most recent call last)" not in stderr:
        return []
    frames = [m for m in (_PY_FRAME.match(ln) for ln in blob.splitlines()) if m]
    last = frames[-1] if frames else None
    exc_line = ""
    tail = [ln for ln in stderr.strip().splitlines() if ln.strip()]
    if tail:
        exc_line = tail[-1].strip()
    exc_type = exc_line.split(":", 1)[0] if exc_line else "INTERNAL ERROR"
    loc = f"{os.path.basename(last['file'])}:{last['func'].strip()}" if last else "unknown"
    return [
        Crash(
            tool=Tool.MYPY,
            kind="internal_error",
            signature=f"mypy:{exc_type}@{loc}",
            excerpt="\n".join(blob.strip().splitlines()[-25:]),
            exit_code=exit_code,
        )
    ]


def parse_mypy(stdout: str, stderr: str = "", exit_code: int | None = None, filename: str = "") -> tuple[list[Diagnostic], list[Crash]]:
    stdout, stderr = _strip_ansi(stdout), _strip_ansi(stderr)
    diags: list[Diagnostic] = []
    for raw in stdout.splitlines():
        line = raw.rstrip()
        if not line:
            continue
        if line.startswith("{"):
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                obj = None
            if isinstance(obj, dict) and "line" in obj:
                if not _same_file(obj.get("file", ""), filename):
                    continue
                msg = obj.get("message", "")
                sev = Severity(obj.get("severity", "error")) if obj.get("severity") in ("error", "note", "warning") else Severity.ERROR
                rev = _MYPY_REVEAL.match(msg)
                col = obj.get("column")
                ecol = obj.get("end_column")
                diags.append(
                    Diagnostic(
                        tool=Tool.MYPY,
                        line=int(obj["line"]),
                        col=(col + 1) if isinstance(col, int) and col >= 0 else None,
                        end_line=obj.get("end_line"),
                        end_col=(ecol + 1) if isinstance(ecol, int) else None,
                        severity=sev,
                        code=None if rev else obj.get("code"),
                        message=msg,
                        revealed_type=rev.group("t") if rev else None,
                        raw=line,
                    )
                )
                continue
        m = _MYPY_LINE.match(line)
        if not m or not _same_file(m["file"], filename):
            continue
        msg = m["msg"]
        rev = _MYPY_REVEAL.match(msg) if m["sev"] == "note" else None
        diags.append(
            Diagnostic(
                tool=Tool.MYPY,
                line=int(m["line"]),
                col=int(m["col"]) if m["col"] else None,
                end_line=int(m["eline"]) if m["eline"] else None,
                end_col=int(m["ecol"]) if m["ecol"] else None,
                severity=Severity(m["sev"]),
                code=m["code"],
                message=msg,
                revealed_type=rev.group("t") if rev else None,
                raw=line,
            )
        )
    return diags, _mypy_crash(stdout, stderr, exit_code)


# --------------------------------------------------------------------------- ty

_TY_CONCISE = re.compile(
    r"^(?P<file>[^\n]+?):(?P<line>\d+):(?P<col>\d+):\s(?P<sev>error|warning|warn|info|fatal)\[(?P<code>[\w-]+)\]\s(?P<msg>.*)$"
)
_TY_FULL_HEAD = re.compile(r"^(?P<sev>error|warning|warn|info|fatal)\[(?P<code>[\w-]+)\]:\s(?P<msg>.*)$")
_TY_FULL_LOC = re.compile(r"^\s*-->\s(?P<file>[^\n]+?):(?P<line>\d+):(?P<col>\d+)")
_TY_REVEAL = re.compile(r"^Revealed type: `(?P<t>.*)`\s*$")
_TY_PANIC = re.compile(r"[Pp]anicked at (?P<loc>[^\s:]+(?::\d+){1,2})(?::?\s*(?P<msg>.*))?")
_TY_SEV = {"error": Severity.ERROR, "fatal": Severity.ERROR, "warning": Severity.WARNING, "warn": Severity.WARNING, "info": Severity.NOTE}


def _ty_diag(file: str, line: int, col: int | None, sev: str, code: str, msg: str, raw: str, end=None) -> Diagnostic:
    rev = _TY_REVEAL.match(msg) if code == "revealed-type" else None
    return Diagnostic(
        tool=Tool.TY,
        line=line,
        col=col,
        end_line=end[0] if end else None,
        end_col=end[1] if end else None,
        severity=_TY_SEV.get(sev, Severity.ERROR),
        code=code,
        message=msg,
        revealed_type=rev.group("t") if rev else None,
        raw=raw,
    )


def _ty_crash(stdout: str, stderr: str, exit_code: int | None, diags: list[Diagnostic]) -> list[Crash]:
    blob = f"{stdout}\n{stderr}"
    panic = _TY_PANIC.search(blob)
    hit = (
        exit_code == 101
        or panic is not None
        or any(d.code == "panic" for d in diags)
        or "This indicates a bug in ty" in blob
        or "internal error" in stderr.lower()
    )
    if not hit:
        return []
    if panic:
        loc = re.sub(r"^.*?(crates/)", r"\1", panic["loc"])  # strip absolute build paths
        sig = f"ty:panic@{loc}"
    else:
        sig = f"ty:exit{exit_code}"
    lines = [ln for ln in blob.strip().splitlines() if ln.strip()]
    return [Crash(tool=Tool.TY, kind="panic", signature=sig, excerpt="\n".join(lines[-25:]), exit_code=exit_code)]


def parse_ty(stdout: str, stderr: str = "", exit_code: int | None = None, filename: str = "") -> tuple[list[Diagnostic], list[Crash]]:
    stdout, stderr = _strip_ansi(stdout), _strip_ansi(stderr)
    diags: list[Diagnostic] = []
    text = stdout.strip()
    if text.startswith("["):
        try:
            items = json.loads(text)
        except json.JSONDecodeError:
            items = []
        for it in items:
            loc = it.get("location", {})
            if not _same_file(loc.get("path", ""), filename):
                continue
            pos = loc.get("positions", {})
            begin = pos.get("begin", {}) or {"line": loc.get("lines", {}).get("begin", 0)}
            end = pos.get("end")
            code = it.get("check_name", "")
            msg = it.get("description", "")
            if msg.startswith(code + ": "):
                msg = msg[len(code) + 2 :]
            sev = {"info": "info", "minor": "warning", "major": "error", "critical": "error", "blocker": "error"}.get(it.get("severity", "major"), "error")
            diags.append(
                _ty_diag(
                    loc.get("path", ""), int(begin.get("line", 0)), begin.get("column"), sev, code, msg, json.dumps(it),
                    end=(end.get("line"), end.get("column")) if end else None,
                )
            )
        return diags, _ty_crash(stdout, stderr, exit_code, diags)

    lines = stdout.splitlines()
    pending: tuple[str, str, str, str] | None = None
    for raw in lines:
        line = raw.rstrip()
        m = _TY_CONCISE.match(line)
        if m:
            if _same_file(m["file"], filename):
                diags.append(_ty_diag(m["file"], int(m["line"]), int(m["col"]), m["sev"], m["code"], m["msg"], line))
            pending = None
            continue
        h = _TY_FULL_HEAD.match(line)
        if h:
            pending = (h["sev"], h["code"], h["msg"], line)
            continue
        loc = _TY_FULL_LOC.match(line)
        if loc and pending:
            if _same_file(loc["file"], filename):
                sev, code, msg, head = pending
                diags.append(_ty_diag(loc["file"], int(loc["line"]), int(loc["col"]), sev, code, msg, head))
            pending = None
    return diags, _ty_crash(stdout, stderr, exit_code, diags)


# --------------------------------------------------------------------------- pyright

_PYRIGHT_REVEAL = re.compile(r'^Type of ".*" is "(?P<t>.*)"$', re.S)


def parse_pyright(stdout: str, stderr: str = "", exit_code: int | None = None, filename: str = "") -> tuple[list[Diagnostic], list[Crash]]:
    crashes: list[Crash] = []
    try:
        start = stdout.index("{")
        data = json.loads(stdout[start:])
    except (ValueError, json.JSONDecodeError):
        data = None
    if data is None:
        if stdout.strip() or stderr.strip() or (exit_code or 0) > 1:
            crashes.append(
                Crash(Tool.PYRIGHT, "abnormal_exit", f"pyright:exit{exit_code}", (stderr or stdout)[-2000:], exit_code)
            )
        return [], crashes
    blob = stderr or ""
    if "internal error" in blob.lower() or "unhandled exception" in blob.lower():
        crashes.append(Crash(Tool.PYRIGHT, "internal_error", "pyright:internal", blob[-2000:], exit_code))
    diags = []
    for d in data.get("generalDiagnostics", []):
        if not _same_file(d.get("file", ""), filename):
            continue
        sev = {"error": Severity.ERROR, "warning": Severity.WARNING}.get(d.get("severity"), Severity.NOTE)
        msg = d.get("message", "")
        start = d.get("range", {}).get("start", {})
        end = d.get("range", {}).get("end", {})
        rev = _PYRIGHT_REVEAL.match(msg) if sev == Severity.NOTE else None
        diags.append(
            Diagnostic(
                tool=Tool.PYRIGHT,
                line=int(start.get("line", 0)) + 1,
                col=int(start.get("character", 0)) + 1,
                end_line=int(end.get("line", 0)) + 1 if end else None,
                end_col=int(end.get("character", 0)) + 1 if end else None,
                severity=sev,
                code=d.get("rule"),
                message=msg.split("\n", 1)[0],
                revealed_type=rev.group("t") if rev else None,
                raw=json.dumps(d),
            )
        )
    return diags, crashes


# --------------------------------------------------------------------------- runtime

STRONG_TYPE_EXC = {"TypeError", "AttributeError", "NameError", "UnboundLocalError"}
WEAK_TYPE_EXC = {"KeyError", "IndexError"}
_UNPACK = re.compile(r"(too many|not enough) values to unpack")


def classify_exception(exc_type: str | None, message: str | None) -> str:
    """'strong' = a sound static checker is expected to prevent it; 'weak' = sometimes; 'none'."""
    if not exc_type:
        return "none"
    base = exc_type.rsplit(".", 1)[-1]
    msg = message or ""
    if base in STRONG_TYPE_EXC:
        if base == "TypeError" and "reveal_type" in msg:
            return "none"
        if base == "NameError" and "'reveal_type'" in msg:
            return "none"  # test-harness artefact, not a typing fact
        return "strong"
    if base == "AssertionError" and "Expected code to be unreachable" in msg:
        return "strong"  # typing.assert_never
    if base == "ValueError" and _UNPACK.search(msg):
        return "strong"
    if base in WEAK_TYPE_EXC:
        return "weak"
    return "none"


def parse_runtime(text: str, filename: str = "") -> RuntimeResult:
    """Accept harness JSON, a raw traceback, or a free-form success marker."""
    t = (text or "").strip()
    if not t:
        return RuntimeResult(status="not_run")
    if t.startswith("{"):
        try:
            obj = json.loads(t)
            return runtime_from_json(obj)
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
    if "Traceback (most recent call last)" in t:
        frames: list[tuple[int, str]] = []
        for ln in t.splitlines():
            m = _PY_FRAME.match(ln)
            if m and (not filename or _same_file(m["file"], filename) or m["file"] == "<string>"):
                frames.append((int(m["line"]), m["func"].strip()))
        tail = [ln for ln in t.splitlines() if ln.strip() and not ln.startswith(" ")]
        last = tail[-1] if tail else ""
        mexc = re.match(r"^(?P<type>[A-Za-z_][\w.]*)(?::\s?(?P<msg>.*))?$", last.strip())
        return RuntimeResult(
            status="exception",
            exc_type=mexc["type"] if mexc else "UnknownException",
            exc_message=(mexc["msg"] or "") if mexc else last,
            exc_line=frames[-1][0] if frames else None,
            frames=frames,
            stderr=t,
        )
    low = t.lower()
    if "timeout" in low or "timed out" in low:
        return RuntimeResult(status="timeout", stderr=t)
    return RuntimeResult(status="success", stdout=t)


def runtime_from_json(obj: dict) -> RuntimeResult:
    return RuntimeResult(
        status=obj["status"],
        exc_type=obj.get("exc_type"),
        exc_message=obj.get("exc_message"),
        exc_line=obj.get("exc_line"),
        frames=[tuple(f) for f in obj.get("frames", [])],
        executed_lines=obj.get("executed_lines"),
        probes=[RuntimeProbe(line=p["line"], shape=p["shape"]) for p in obj.get("probes", [])],
        stdout=obj.get("stdout", ""),
        stderr=obj.get("stderr", ""),
        python_version=obj.get("python_version"),
    )
