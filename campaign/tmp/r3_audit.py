"""Round 3 audit: findings that went live->dismissed (REVEAL-ERROR-RECOVERY via binding) or dismissed->live (alias) between two runs."""
import json
import random
import sys
from collections import Counter
from pathlib import Path

a_dir, b_dir, mode = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]  # mode: new | reopened
n = int(sys.argv[4]) if len(sys.argv) > 4 else 20
hold = {x for x in Path("runs/day2/split/holdout.txt").read_text().split("\n") if x}


def load(d):
    out = {}
    for f in d.glob("seed-*.json"):
        r = json.loads(f.read_text())
        o = next((x.split("=", 1)[1].removeprefix("seed ") for x in r["notes"] if x.startswith("origin=")), "")
        ds = {x["id"]: x for x in r["discrepancies"]}
        for fi in r["findings"]:
            x = ds.get(fi["discrepancy_id"])
            if x is not None:
                out[(r["case_id"], fi["discrepancy_id"])] = (r, x, fi, o)
    return out


A, B = load(a_dir), load(b_dir)
hits = []
for k, (rb, xb, fb, o) in B.items():
    if k not in A:
        continue
    ra, xa, fa, _ = A[k]
    if mode == "new" and fa["tier"] != "dismissed" and fb["tier"] == "dismissed" and fb["decided_by"] == "kb:REVEAL-ERROR-RECOVERY":
        hits.append((o, rb, xb, fb))
    if mode == "reopened" and fa["tier"] == "dismissed" and fb["tier"] != "dismissed":
        hits.append((o, rb, xb, fb))
fam = Counter((("holdout" if o in hold else "tuning"), o.split("/")[-1].split("__")[0]) for o, *_ in hits)
print(len(hits), dict(fam))
random.Random(11).shuffle(hits)
for o, r, d, f in hits[:n]:
    rt = r["runtime"]
    raised = [ln for ln, _ in rt.get("frames", [])] if rt["status"] == "exception" else []
    print(f"--- {o} {d['id']} L{d['anchor']} runtime={rt['status']} {rt.get('exc_type')} frames={raised} split={'holdout' if o in hold else 'tuning'}")
    lines = r["source"].split("\n")
    for t in ("mypy", "ty"):
        for y in d[t]:
            print(f"    {t}: [{y.get('code')}] {(y.get('revealed_type') or y['message'])[:90]}")
    side = "ty" if (d["ty"] and (d["ty"][0].get("revealed_type") or "").strip() == "Unknown") else "mypy"
    errs = [y for y in r["diagnostics"][side] if y["severity"] == "error" and y.get("revealed_type") is None and y["line"] < d["anchor"]]
    for y in errs[:3]:
        print(f"    {side} error L{y['line']} [{y.get('code')}] {y['message'][:80]} :: {lines[y['line'] - 1].strip()[:70]}")
    print(f"    reveal L{d['anchor']}: {lines[d['anchor'] - 1].strip()[:90]}")
