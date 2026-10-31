#!/usr/bin/env python
"""Parallel, resumable seed-corpus runner for the KB-hardening loop (deterministic stage only).

    python scripts/kbloop_run.py OUT_DIR SEED_DIR [SEED_DIR ...] [--jobs N] [--timeout S] [--sample N]

Same per-program logic as ``typediff seeds`` (preflight, run_source, report json/md written flat into OUT_DIR so
``typediff triage OUT_DIR`` works), but: no shared dataset (so no order-dependent DUPLICATE dismissals), a stable
case id per seed path, a hard per-program timeout, and a process pool. Re-running skips seeds that already have a
report, so an interrupted run resumes. ``--sample N`` takes a deterministic stratified sample (proportional by
top-level source folder, at least one per folder).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
import os
import random
import signal
import sys
import time
from collections import defaultdict
from pathlib import Path

PYV = "3.13"


class _Timeout(Exception):
    pass


def _alarm(_sig, _frm):
    raise _Timeout()


def _cid(path: str) -> str:
    return "seed-" + hashlib.sha256(path.encode()).hexdigest()[:12]


def _work(args):
    path, out, timeout = args
    from typediff.cli import _save, _seed_area
    from typediff.corpus import Corpus
    from typediff.generator import blocking, preflight
    from typediff.llm import from_env
    from typediff.pipeline import Pipeline, PipelineConfig
    from typediff.runners import ToolConfig

    cid = _cid(path)
    out = Path(out)
    if (out / f"{cid}.json").exists() or (out / "_rejected" / f"{cid}.txt").exists():
        return path, "skip", 0.0
    t0 = time.time()
    p = Path(path)
    source = p.read_text(encoding="utf-8", errors="replace")
    area = _seed_area(p, source, "gradual_any")
    problems = preflight(source, PYV)
    if blocking(problems):
        (out / "_rejected").mkdir(exist_ok=True)
        (out / "_rejected" / f"{cid}.txt").write_text(f"{path}\n" + "\n".join(problems))
        return path, "rejected", time.time() - t0
    signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(timeout)
    try:
        pipe = Pipeline(PipelineConfig(tools=ToolConfig(python_version=PYV), reduce=False, audit_rate=0.0),
                        from_env("null"), Corpus(), None)
        report = pipe.run_source(source, case_id=cid)
        report.notes += [f"area={area}", f"origin=seed {path}", "depth=0"] + problems
        _save(report, out, None)
        status = "ok"
    except _Timeout:
        (out / "_rejected").mkdir(exist_ok=True)
        (out / "_rejected" / f"{cid}.txt").write_text(f"{path}\nPROGRAM TIMEOUT {timeout}s")
        status = "timeout"
    except Exception as exc:  # noqa: BLE001
        (out / "_rejected").mkdir(exist_ok=True)
        (out / "_rejected" / f"{cid}.txt").write_text(f"{path}\nERROR {type(exc).__name__}: {exc}")
        status = "error"
    finally:
        signal.alarm(0)
    return path, status, time.time() - t0


def collect(dirs, sample):
    files = sorted(str(f) for d in dirs for f in Path(d).rglob("*.py"))
    if sample and sample < len(files):
        groups = defaultdict(list)
        for f in files:
            parts = Path(f).parts
            key = parts[2] if len(parts) > 2 and parts[1] == "harvested" else parts[1] if len(parts) > 1 else "."
            if parts[1] != "harvested":
                key = "hand"
            groups[key].append(f)
        rng = random.Random(1234)
        files = []
        for k, v in sorted(groups.items()):
            n = max(1, round(sample * len(v) / sum(len(x) for x in groups.values())))
            files += sorted(rng.sample(v, min(n, len(v))))
        files.sort()
    return files


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("seed_dirs", nargs="+")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 4) - 2))
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--manifest", help="write/read the file list here (keeps the same sample across rounds)")
    ap.add_argument("--progress", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if a.manifest and Path(a.manifest).exists():
        files = Path(a.manifest).read_text().split("\n")
        files = [f for f in files if f]
    else:
        files = collect(a.seed_dirs, a.sample)
        if a.manifest:
            Path(a.manifest).write_text("\n".join(files))
    total = len(files)
    counts = defaultdict(int)
    done = 0
    t0 = time.time()
    with mp.Pool(a.jobs, maxtasksperchild=50) as pool, open(a.progress, "a") as log:
        log.write(f"start {time.ctime()} total={total} jobs={a.jobs}\n")
        for path, status, dur in pool.imap_unordered(_work, [(f, str(out), a.timeout) for f in files], chunksize=1):
            done += 1
            counts[status] += 1
            if status not in ("ok", "skip") or done % 50 == 0:
                log.write(f"{done}/{total} {dict(counts)} elapsed={time.time() - t0:.0f}s last={status} {path} {dur:.1f}s\n")
                log.flush()
        log.write(f"DONE {time.ctime()} total={total} {dict(counts)} elapsed={time.time() - t0:.0f}s\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
