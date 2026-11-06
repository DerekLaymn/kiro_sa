cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
R=campaign/day9/phase1/results
D=runs/day9/day8replay
rm -rf "$D"
mkdir -p runs/day9
TYPEDIFF_LLM=null .venv/bin/python scripts/kbloop_replay.py runs/day8/out "$D" --jobs 8 --verify-sample 30 --pyright-only --rerun-runtime > $R/replay-day8.out 2>&1
echo "replay rc=$?" >> $R/replay-day8.out
cat > /tmp/d9/diff8.py <<'EOF'
import json, sys, glob, os
a_dir, b_dir = sys.argv[1], sys.argv[2]
changed = total = 0
live_a = live_b = 0
for fa in sorted(glob.glob(a_dir + "/seed-*.json")):
    fb = os.path.join(b_dir, os.path.basename(fa))
    if not os.path.exists(fb):
        continue
    ra, rb = json.load(open(fa)), json.load(open(fb))
    A = {x["discrepancy_id"]: x for x in ra["findings"]}
    B = {x["discrepancy_id"]: x for x in rb["findings"]}
    origin = next((n for n in ra.get("notes", []) if n.startswith("origin=")), "")
    for k in sorted(set(A) | set(B)):
        a, b = A.get(k), B.get(k)
        total += 1
        ta = (a["tier"], a.get("decided_by")) if a else None
        tb = (b["tier"], b.get("decided_by")) if b else None
        live_a += bool(a and a["tier"] != "dismissed")
        live_b += bool(b and b["tier"] != "dismissed")
        if ta != tb:
            changed += 1
            print(os.path.basename(fa), k, origin[-90:], "\n   ", ta, "->", tb)
print("compared", total, "changed", changed, "live before", live_a, "live after", live_b)
EOF
.venv/bin/python /tmp/d9/diff8.py runs/day8/out "$D" > $R/replay-day8-diff.txt 2>&1
