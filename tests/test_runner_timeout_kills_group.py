"""A checker timeout must kill the whole process group (pyright's launcher spawns a node child that used to be orphaned)."""

from __future__ import annotations

import os
import time

from typediff.runners import Runners


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    with open(f"/proc/{pid}/stat") as f:  # a zombie still answers kill(0)
        return f.read().rsplit(")", 1)[1].split()[0] != "Z"


def test_timeout_kills_grandchild(tmp_path):
    pidfile = tmp_path / "child.pid"
    out, err, code, _ = Runners()._exec(["bash", "-c", f"sleep 300 & echo $! > {pidfile}; wait"], str(tmp_path), 1)
    assert code is None and err.startswith("TIMEOUT after 1s")
    pid = int(pidfile.read_text())
    for _ in range(50):
        if not _alive(pid):
            break
        time.sleep(0.1)
    assert not _alive(pid)


def test_normal_exit_unchanged(tmp_path):
    out, err, code, _ = Runners()._exec(["bash", "-c", "echo hi; echo oops >&2; exit 3"], str(tmp_path), 5)
    assert (out.strip(), err.strip(), code) == ("hi", "oops", 3)


def test_missing_binary(tmp_path):
    out, err, code, _ = Runners()._exec(["definitely-not-installed-xyz"], str(tmp_path), 5)
    assert code == 127 and "NOT INSTALLED" in err
