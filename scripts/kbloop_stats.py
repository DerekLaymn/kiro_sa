#!/usr/bin/env python
"""Round statistics for the KB-loop: overall, tuning set and hold-out set.

    python scripts/kbloop_stats.py runs/round1/out [--split docs/kb-loop-split] [--json OUT.json]
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


def load(run: Path):
    for f in sorted(run.glob("seed-*.json")):
        try:
            yield json.loads(f.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue


def origin(r) -> str:
    return next((n.split("=", 1)[1].removeprefix("seed ") for n in r.get("notes", []) if n.startswith("origin=")), "")


def closing_ref(f) -> str:
    """Which known_upstream crash entry closed a dismissed crash finding (``closed_by``; older reports: the
    ``DUPLICATE of <url> (<ID>)`` review note). ``NO-REFERENCE`` marks a closure that cannot be audited."""
    if f.get("closed_by"):
        return f["closed_by"].split()[0]
    for n in f.get("review_notes", []):
        m = re.match(r"DUPLICATE of \S+ \(([^)]+)\)", n)
        if m:
            return m.group(1)
    return "NO-REFERENCE"


def summarize(reports) -> dict:
    s = {"programs": 0, "discrepancies": 0, "live": 0, "dismissed": 0, "crash_findings": 0,
         "dismissed_by_category": Counter(), "dismissed_by_entry": Counter(), "live_by_kind": Counter(),
         "programs_with_live": 0, "tool_crashes": 0, "crash_closed_by": Counter(),
         "live_wo_only_pyright": 0, "programs_with_live_wo_only_pyright": 0}
    for r in reports:
        s["programs"] += 1
        s["discrepancies"] += len(r["discrepancies"])
        s["tool_crashes"] += len(r.get("crashes", []))
        ds = {d["id"]: d for d in r["discrepancies"]}
        live = live_wo = 0
        for f in r["findings"]:
            d = ds.get(f["discrepancy_id"])
            if f["tier"] == "dismissed":
                s["dismissed"] += 1
                s["dismissed_by_category"][f.get("dismissal")] += 1
                s["dismissed_by_entry"][f["decided_by"]] += 1
                if f["decided_by"].startswith("rule:crash:"):
                    s["crash_closed_by"][closing_ref(f)] += 1
            else:
                s["live"] += 1
                live += 1
                if d is None:
                    s["crash_findings"] += 1
                s["live_by_kind"][d["kind"] if d else "crash"] += 1
                if not d or d["kind"] != "only_pyright":
                    live_wo += 1
        s["programs_with_live"] += bool(live)
        s["live_wo_only_pyright"] += live_wo
        s["programs_with_live_wo_only_pyright"] += bool(live_wo)
    return s


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--split", default="docs/kb-loop-split")
    ap.add_argument("--json")
    a = ap.parse_args()
    run = Path(a.run)
    hold = {x for x in Path(a.split, "holdout.txt").read_text().split("\n") if x}
    reports = list(load(run))
    rejected = list((run / "_rejected").glob("*.txt")) if (run / "_rejected").exists() else []
    out = {"all": summarize(reports), "tuning": summarize(r for r in reports if origin(r) not in hold),
           "holdout": summarize(r for r in reports if origin(r) in hold)}
    out["rejected_or_failed"] = Counter(("timeout" if "TIMEOUT" in p.read_text() else "error" if "\nERROR " in p.read_text()
                                         else "preflight") for p in rejected)
    for name in ("all", "tuning", "holdout"):
        s = out[name]
        print(f"[{name}] programs={s['programs']} discrepancies={s['discrepancies']} live={s['live']} "
              f"(programs with live={s['programs_with_live']}, crash findings={s['crash_findings']}) dismissed={s['dismissed']} "
              f"tool_crashes={s['tool_crashes']}")
        print(f"   dismissed by category: {dict(s['dismissed_by_category'])}")
        print(f"   dismissed by entry: {dict(s['dismissed_by_entry'].most_common())}")
        print(f"   crash closures by closing reference: {dict(s['crash_closed_by'].most_common())}")
        print(f"   live by kind: {dict(s['live_by_kind'])}")
        if s["live_by_kind"].get("only_pyright"):  # runs judged with --pyright-only: the number comparable with Days 1 to 6
            print(f"   live without only_pyright: {s['live_wo_only_pyright']} "
                  f"(programs with such live={s['programs_with_live_wo_only_pyright']})")
    print(f"rejected/failed: {dict(out['rejected_or_failed'])}")
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1, default=dict))


if __name__ == "__main__":
    main()
