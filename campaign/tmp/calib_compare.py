"""Merge the chunked calibration rows and compare baseline-code vs current-code."""
import json
import sys
from collections import Counter
from pathlib import Path

R = Path("/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/runs/day2")


def load(which):
    rows = {}
    for k in range(4):
        p = R / f"calib-{which}-{k}" / "calibration_rows.jsonl"
        if p.exists():
            for line in p.read_text().splitlines():
                r = json.loads(line)
                rows[r["id"]] = r
    return rows


B, A = load("before"), load("after")
print("rows before/after:", len(B), len(A))
for name, rows in (("BEFORE (HEAD code)", B), ("AFTER (current code)", A)):
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
print("== changes per id (before -> after outcome) / decided_by")
for i in sorted(set(B) | set(A)):
    b, a = B.get(i), A.get(i)
    bo, ao = (b or {}).get("outcome"), (a or {}).get("outcome")
    bf = sorted({f[2] for f in (b or {}).get("findings", []) if isinstance(f, (list, tuple))})
    af = sorted({f[2] for f in (a or {}).get("findings", []) if isinstance(f, (list, tuple))})
    if bo != ao or bf != af:
        print(f"  {i}: {bo} -> {ao}   before={bf} after={af}")
newly = [i for i in A if A[i]["kind"] == "positive" and A[i]["outcome"] == "dismissed" and B.get(i, {}).get("outcome") != "dismissed"]
print("NEWLY DISMISSED POSITIVES (real bugs):", sorted(newly))
