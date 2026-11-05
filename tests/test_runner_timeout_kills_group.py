"""A checker timeout must kill the whole process group (pyright's launcher spawns a node child that used to be orphaned)."""

from __future__ import annotations

import os
import signal
import time

from typediff.runners import Runners


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    try:
        with open(f"/proc/{pid}/stat") as f:  # a zombie still answers kill(0)
            return f.read().rsplit(")", 1)[1].split()[0] != "Z"
    except (FileNotFoundError, ProcessLookupError):  # exited/reaped between kill(0) and open/read of /proc/<pid>/stat
        return False


def _wait_for(predicate, deadline_s: float) -> bool:
    end = time.monotonic() + deadline_s
    while time.monotonic() < end:
        if predicate():
            return True
        time.sleep(0.05)
    return predicate()


def _read_pid(pidfile) -> int | None:
    try:
        return int(pidfile.read_text().strip())
    except (FileNotFoundError, ValueError):  # not written yet, or caught mid-write
        return None


def test_timeout_kills_grandchild(tmp_path):
    # A 1s timeout flaked under load: bash was killed before it wrote its pidfile. Use a longer timeout, write the pidfile
    # atomically (tmp + mv), poll for it with a generous deadline, and always kill the grandchild if the test fails.
    pidfile = tmp_path / "child.pid"
    script = f"sleep 300 & echo $! > {pidfile}.tmp && mv {pidfile}.tmp {pidfile}; wait"
    pid = None
    try:
        out, err, code, _ = Runners()._exec(["bash", "-c", script], str(tmp_path), 5)
        assert code is None and err.startswith("TIMEOUT after 5s")
        assert _wait_for(lambda: _read_pid(pidfile) is not None, 30), "bash never wrote its pidfile"
        pid = _read_pid(pidfile)
        assert _wait_for(lambda: not _alive(pid), 30), f"grandchild {pid} survived the timeout"
    finally:
        pid = pid or _read_pid(pidfile)
        if pid is not None and _alive(pid):
            os.kill(pid, signal.SIGKILL)


def test_normal_exit_unchanged(tmp_path):
    out, err, code, _ = Runners()._exec(["bash", "-c", "echo hi; echo oops >&2; exit 3"], str(tmp_path), 5)
    assert (out.strip(), err.strip(), code) == ("hi", "oops", 3)


def test_missing_binary(tmp_path):
    out, err, code, _ = Runners()._exec(["definitely-not-installed-xyz"], str(tmp_path), 5)
    assert code == 127 and "NOT INSTALLED" in err
