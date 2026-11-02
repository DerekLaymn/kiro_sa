#!/usr/bin/env python
"""Re-run selected calibration cases (by id) with the current KB: python scripts/kbloop_calib_subset.py OUT ID [ID ...]

Same pipeline settings as `typediff --no-pyright calibrate` (reduce off, audit off, no dataset, 30 s checker timeout)."""

import argparse
import json
import sys
from pathlib import Path

from typediff.calibration import negatives, run_calibration
from typediff.cli import _pipeline


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("ids", nargs="+")
    ap.add_argument("--negatives", action="store_true")
    a = ap.parse_args()
    args = argparse.Namespace(python_version="3.13", typeshed=None, no_pyright=True, no_reduce=True, audit_rate=0.0,
                              out=a.out, docs="/tmp/kbloop/docs", llm="null")
    p = _pipeline(args)
    p.cfg.tools.timeout_s = 30
    p.cfg.reduce = False
    p.cfg.audit_rate = 0.0
    p.dataset = None
    cases = [c for c in json.loads(Path("calibration/positives.json").read_text()) if c["id"] in set(a.ids)]
    if a.negatives:
        cases += negatives(Path("calibration/negatives"))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "calibration_rows.jsonl").unlink(missing_ok=True)
    run_calibration(p, cases, out)
    for line in (out / "calibration_rows.jsonl").read_text().splitlines():
        r = json.loads(line)
        print(r["id"], r["outcome"], [f[2] for f in r["findings"]])
    return 0


if __name__ == "__main__":
    sys.exit(main())
