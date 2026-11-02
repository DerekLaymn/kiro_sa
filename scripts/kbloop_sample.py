#!/usr/bin/env python
"""Print examples of one live pattern (tuning set): python scripts/kbloop_sample.py RUN KIND CODE [--n 6] [--tpl SUBSTR]"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("kind")
    ap.add_argument("code", help="comma-joined codes, or the relation for reveal_mismatch")
    ap.add_argument("--n", type=int, default=6)
    ap.add_argument("--tpl", default="")
    ap.add_argument("--ctx", type=int, default=0, help="lines of context above the statement")
    ap.add_argument("--split", default="docs/kb-loop-split")
    a = ap.parse_args()
    hold = {x for x in Path(a.split, "holdout.txt").read_text().split("\n") if x}
    hits = []
    for f in sorted(Path(a.run).glob("seed-*.json")):
        r = json.loads(f.read_text())
        o = next((n.split("=", 1)[1].removeprefix("seed ") for n in r["notes"] if n.startswith("origin=")), "")
        if o in hold:
            continue
        ds = {d["id"]: d for d in r["discrepancies"]}
        for x in r["findings"]:
            d = ds.get(x["discrepancy_id"])
            if x["tier"] == "dismissed" or d is None or d["kind"] != a.kind:
                continue
            diags = d["mypy"] or d["ty"] or d["pyright"]
            key = d.get("reveal_relation") if a.kind == "reveal_mismatch" else ",".join(sorted({y.get("code") or "" for y in diags}))
            if key != a.code:
                continue
            msg = " ".join(y["message"] for y in d["mypy"] + d["ty"])
            if a.tpl and a.tpl not in msg:
                continue
            hits.append((o, r, d, x))
    random.Random(5).shuffle(hits)
    print(f"{len(hits)} matches")
    for o, r, d, x in hits[: a.n]:
        lines = r["source"].split("\n")
        print(f"--- {o} {d['id']} L{d['anchor']}  runtime={r['runtime']['status']} {r['runtime'].get('exc_type')}")
        print("\n".join(f"    {i + 1}: {l}" for i, l in enumerate(lines) if d["anchor"] - 1 - a.ctx <= i <= d["anchor_end"] - 1))
        for t in ("mypy", "ty", "pyright"):
            for y in d[t]:
                print(f"    {t}: L{y['line']} [{y.get('code')}] {y.get('revealed_type') or y['message']}"[:230])
        print(f"    hints={d['kb_hits']}")


if __name__ == "__main__":
    main()
