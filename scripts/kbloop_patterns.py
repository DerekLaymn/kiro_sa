#!/usr/bin/env python
"""Volume-ranked pattern table of the LIVE review queue (tuning set by default), with cheap discriminators.

    python scripts/kbloop_patterns.py runs/round1/out [--set tuning|holdout|all] [--top 40] [--md OUT.md]
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from typediff.dataset import message_template

EXPECT = re.compile(r"#\s*(?:E:|N:|error|revealed:|type:\s*ignore|TODO)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--set", default="tuning", choices=["tuning", "holdout", "all"])
    ap.add_argument("--split", default="docs/kb-loop-split")
    ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--md")
    a = ap.parse_args()
    hold = {x for x in Path(a.split, "holdout.txt").read_text().split("\n") if x}
    groups = defaultdict(list)
    for f in sorted(Path(a.run).glob("seed-*.json")):
        r = json.loads(f.read_text())
        o = next((n.split("=", 1)[1].removeprefix("seed ") for n in r["notes"] if n.startswith("origin=")), "")
        if (a.set == "tuning" and o in hold) or (a.set == "holdout" and o not in hold):
            continue
        ds = {d["id"]: d for d in r["discrepancies"]}
        lines = r["source"].split("\n")
        for x in r["findings"]:
            if x["tier"] == "dismissed":
                continue
            d = ds.get(x["discrepancy_id"])
            if d is None:
                key = ("crash", x.get("signature") or x["reasoning"][:60], "")
            else:
                diags = d["mypy"] or d["ty"] or d["pyright"]
                if d["kind"] == "reveal_mismatch":
                    key = (d["kind"], d.get("reveal_relation"), "")
                elif d["kind"].startswith("reveal"):
                    key = (d["kind"], "", "")
                else:
                    key = (d["kind"], ",".join(sorted({y.get("code") or "" for y in diags})),
                           message_template(diags[0]["message"]) if diags else "")
            stmt = "\n".join(lines[d["anchor"] - 1:d["anchor_end"]]) if d else ""
            rt = r["runtime"]
            raised = rt["status"] == "exception" and any(ln == d["anchor"] for ln, _ in rt["frames"]) if d else False
            groups[key].append({"origin": o, "expect": bool(EXPECT.search(stmt)), "raised": raised, "ev": [e["summary"][:90] for e in x["evidence"] if e["strength"] == "strong" and e["supports"] == "bug"][:1],
                                "hints": d["kb_hits"] if d else []})
    rows = sorted(groups.items(), key=lambda kv: -len(kv[1]))
    total = sum(len(v) for v in groups.values())
    out = [f"live findings in {a.set}: {total} in {len(groups)} patterns\n", "| # | n | kind | key | has expectation comment | CPython raised | example |", "|---|---|---|---|---|---|---|"]
    for i, (k, items) in enumerate(rows[: a.top], 1):
        ex = items[0]["origin"].split("/")[-1]
        out.append(f"| {i} | {len(items)} | {k[0]} | {k[1]} {k[2]} | {sum(it['expect'] for it in items)} | {sum(it['raised'] for it in items)} | {ex} |")
    text = "\n".join(out)
    print(text)
    if a.md:
        Path(a.md).write_text(text + "\n")


if __name__ == "__main__":
    main()
