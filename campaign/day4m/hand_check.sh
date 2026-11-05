#!/bin/bash
# Hand check of the findings closed by the Day-4 entries: print each program, its saved crash/diagnostic data, and a fresh
# run of the real checkers (pinned venv binaries) plus CPython.
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
V=$PWD/.venv/bin
for seed in 0032056ba741 3e7d6fb5688c 6cb04c1e6fbc 887c42f07fb0 e4277cc03f53; do
  echo "################ seed-$seed"
  $V/python - "$seed" <<'EOF'
import json, sys
r = json.load(open(f"runs/day4/replay-d3/seed-{sys.argv[1]}.json"))
print("runtime status:", r["runtime"]["status"], "| exc:", r["runtime"].get("exc_type"))
print("crashes:", [(c["tool"], c["kind"], c["signature"], c["returncode"] if "returncode" in c else c.get("exit_code")) for c in r["crashes"]])
print("findings:", [(f["discrepancy_id"], f["tier"], f["dismissal"], f["decided_by"]) for f in r["findings"]])
print("----- source (header comments dropped)")
for i, ln in enumerate(r["source"].split("\n"), 1):
    if not ln.startswith("# "):
        print(f"{i:3d} {ln}")
EOF
  f=$(ls runs/day3/gen/*/*"$(echo $seed | cut -c1-0)"* 2>/dev/null | head -0)
  $V/python - "$seed" > /tmp/d4m/hc_case.py <<'EOF'
import json, sys
print(json.load(open(f"runs/day4/replay-d3/seed-{sys.argv[1]}.json"))["source"])
EOF
  mkdir -p /tmp/d4m/hc/$seed && cp /tmp/d4m/hc_case.py /tmp/d4m/hc/$seed/case.py
  ( cd /tmp/d4m/hc/$seed
    echo "----- ty"; timeout 60 $V/ty check --python-version 3.13 --output-format concise --no-progress --color never case.py 2>&1 | tail -4; echo "ty exit ${PIPESTATUS[0]}"
    echo "----- mypy"; timeout 60 $V/mypy --python-version 3.13 --check-untyped-defs --no-incremental --no-error-summary --show-error-codes case.py 2>&1 | tail -4; echo "mypy exit ${PIPESTATUS[0]}"
    echo "----- pyright"; timeout 90 $V/pyright --pythonversion 3.13 case.py 2>&1 | tail -4
    echo "----- cpython"; timeout 30 $V/python -W ignore case.py 2>&1 | tail -3; echo "python exit ${PIPESTATUS[0]}" )
done
