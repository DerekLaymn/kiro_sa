cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
P=campaign/day8/phase1
rm -rf runs/day8/day6replay-rt
TYPEDIFF_LLM=null .venv/bin/python scripts/kbloop_replay.py runs/day7/day6replay-pyright runs/day8/day6replay-rt --jobs 14 --pyright-only --rerun-runtime --verify-sample 30 > $P/replay-day6-rt.out 2>&1
echo rc=$?; tail -2 $P/replay-day6-rt.out
.venv/bin/python - <<'EOF' > campaign/day8/phase1/only_pyright_relations.txt 2>&1
import json, glob
from collections import Counter
def rel(run):
    c = Counter(); rows = []
    for f in sorted(glob.glob(run + "/seed-*.json")):
        r = json.load(open(f))
        fs = {x["discrepancy_id"]: x for x in r["findings"]}
        for d in r["discrepancies"]:
            if d["kind"] == "only_pyright":
                c[d["reveal_relation"]] += 1
                rows.append((f.split("/")[-1], d["id"], d["reveal_relation"], d["priority"], fs[d["id"]]["tier"], fs[d["id"]]["decided_by"], d["statement"][:70]))
    return c, rows
for name, run in (("Day 7 before (runs/day7/out)", "runs/day7/out"), ("Day 7 after (Day-8 harness)", "runs/day8/day7replay"),
                  ("Day 6 before (runs/day7/day6replay-pyright)", "runs/day7/day6replay-pyright"), ("Day 6 after (Day-8 harness)", "runs/day8/day6replay-rt")):
    c, rows = rel(run)
    print(name, dict(c), "total", sum(c.values()))
    if "after" in name:
        for r in rows:
            if r[2] == "runtime_supports":
                print("    supports:", r)
EOF
cat campaign/day8/phase1/only_pyright_relations.txt
