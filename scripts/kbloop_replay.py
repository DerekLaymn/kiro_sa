#!/usr/bin/env python
"""Re-adjudicate a finished corpus run from its saved reports (no checker re-runs except live experiments).

    python scripts/kbloop_replay.py runs/round1/out runs/round2/out [--jobs N] [--verify-sample 100]

Every <case>.json in the source run holds the parsed tool output, runtime result, flags and versions; the current
KB/rules/normalisation judge them again. ``--verify-sample K`` also fully re-runs K random programs (checkers and all)
and asserts that tier, dismissal and decided_by of every finding are identical to the replay.
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import random
import shutil
import sys
from pathlib import Path

KEEP = ("area=", "origin=", "depth=", "WARN")


def _pipeline():
    from typediff.corpus import Corpus
    from typediff.llm import from_env
    from typediff.pipeline import Pipeline, PipelineConfig
    from typediff.runners import Runners, ToolConfig

    cfg = PipelineConfig(tools=ToolConfig(python_version="3.13"), reduce=False, audit_rate=0.0)
    p = Pipeline(cfg, from_env("null"), Corpus(), None)
    p.runners = Runners(cfg.tools)
    return p


_P = None


def _work(args):
    global _P
    src, dst = args
    from typediff.cli import _save
    from typediff.replay import readjudicate

    _P = _P or _pipeline()
    r = json.loads(Path(src).read_text())
    new = readjudicate(_P, r)
    new.notes = new.notes + [n for n in r.get("notes", []) if n.startswith(KEEP)]
    _save(new, Path(dst), None)
    return src


def key(report: dict):
    ds = {d["id"]: d for d in report["discrepancies"]}
    return sorted((ds[f["discrepancy_id"]]["kind"] if f["discrepancy_id"] in ds else "crash", f["discrepancy_id"], f["tier"],
                  f.get("dismissal"), f["decided_by"]) for f in report["findings"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--jobs", type=int, default=12)
    ap.add_argument("--verify-sample", type=int, default=0)
    ap.add_argument("--only", help="file of seed paths: replay only these")
    a = ap.parse_args()
    src, dst = Path(a.src), Path(a.dst)
    dst.mkdir(parents=True, exist_ok=True)
    if (src / "_rejected").exists() and not (dst / "_rejected").exists():
        shutil.copytree(src / "_rejected", dst / "_rejected")
    only = {x for x in Path(a.only).read_text().split("\n") if x} if a.only else None
    files = []
    for f in sorted(src.glob("seed-*.json")):
        if only is not None:
            o = next((n.split("=", 1)[1].removeprefix("seed ") for n in json.loads(f.read_text()).get("notes", [])
                      if n.startswith("origin=")), "")
            if o not in only:
                continue
        files.append((str(f), str(dst)))
    with mp.Pool(a.jobs, maxtasksperchild=200) as pool:
        for i, _ in enumerate(pool.imap_unordered(_work, files, chunksize=8), 1):
            if i % 1000 == 0:
                print(f"replayed {i}/{len(files)}", flush=True)
    print(f"replayed {len(files)} reports into {dst}")
    if a.verify_sample:
        from typediff.cli import _save

        rng = random.Random(7)
        sample = rng.sample(files, min(a.verify_sample, len(files)))
        p = _pipeline()
        bad = 0
        for s, _d in sample:
            old = json.loads(Path(s).read_text())
            full = p.run_source(old["source"], case_id=old["case_id"])
            from typediff.models import to_jsonable

            full_j = json.loads(json.dumps(to_jsonable(full)))
            rep_j = json.loads((dst / Path(s).name).read_text())
            if key(full_j) != key(rep_j):
                bad += 1
                print("MISMATCH", old["case_id"], key(full_j), key(rep_j))
        print(f"verify-sample: {len(sample) - bad}/{len(sample)} identical to a full re-run (mismatches: {bad})")
        return 1 if bad else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
