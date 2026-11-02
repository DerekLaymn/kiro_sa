"""Merge chunked calibration rows: Stage-2 baseline code (calib-before-*), round-1 end (calib-after-*), round-2 end (calib2-after-*)."""
import json
from collections import Counter
from pathlib import Path

R = Path("/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/runs/day2")


def load(prefix):
    rows = {}
    for k in range(4):
        p = R / f"{prefix}-{k}" / "calibration_rows.jsonl"
        if p.exists():
            for line in p.read_text().splitlines():
                r = json.loads(line)
                rows[r["id"]] = r
    return rows


S2, R1, R2 = load("calib-before"), load("calib-after"), load("calib2-after")
print("rows stage2-baseline / round1-end / round2-end:", len(S2), len(R1), len(R2))
for name, rows in (("STAGE-2 BASELINE CODE (b4bf9e8)", S2), ("ROUND-1 END (d479c03)", R1), ("ROUND-2 END (working tree)", R2)):
    pos = [r for r in rows.values() if r["kind"] == "positive"]
    neg = [r for r in rows.values() if r["kind"] == "negative"]
    print(f"== {name}: positives={len(pos)} negatives={len(neg)}")
    print("   positive outcomes:", dict(Counter(r["outcome"] for r in pos)))
    for tool in ("ty", "mypy"):
        t = [r for r in pos if r["id"].startswith(tool)]
        print(f"   {tool}: n={len(t)} {dict(Counter(r['outcome'] for r in t))}")
    print("   dismissed positives:", sorted(r["id"] for r in pos if r["outcome"] == "dismissed"))
    print("   negatives dismissed (closed automatically):", sum(r["outcome"] == "dismissed" for r in neg), "of", len(neg))
    print("   dismissed rows total (positives+negatives):", sum(r["outcome"] == "dismissed" for r in rows.values()), "of", len(rows))
print("== changes per id, round-1 end -> round-2 end (outcome / decided_by)")
for i in sorted(set(R1) | set(R2)):
    b, a = R1.get(i), R2.get(i)
    bo, ao = (b or {}).get("outcome"), (a or {}).get("outcome")
    bf = sorted({f[2] for f in (b or {}).get("findings", []) if isinstance(f, (list, tuple))})
    af = sorted({f[2] for f in (a or {}).get("findings", []) if isinstance(f, (list, tuple))})
    if bo != ao or bf != af:
        print(f"  {i}: {bo} -> {ao}   before={bf} after={af}")
for label, base in (("round-1 end", R1), ("stage-2 baseline", S2)):
    newly = [i for i in R2 if R2[i]["kind"] == "positive" and R2[i]["outcome"] == "dismissed" and base.get(i, {}).get("outcome") != "dismissed"]
    print(f"NEWLY DISMISSED POSITIVES (real bugs) vs {label}:", sorted(newly))
neg_open = sorted(r["id"] for r in R2.values() if r["kind"] == "negative" and r["outcome"] != "dismissed")
print("negatives NOT closed at round-2 end:", neg_open)
