#!/bin/bash
# Day 9 phase 7: group yield from the saved judge output (no judge re-run) and the final checks. Output in results/.
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
R=campaign/day9/phase7/results
mkdir -p "$R"
git rev-parse --short HEAD > "$R/head.out" 2>&1
git branch --show-current >> "$R/head.out" 2>&1
timeout 120 .venv/bin/python campaign/day9/phase7/group_yield.py > "$R/group_yield.out" 2>&1
echo "rc=$?" >> "$R/group_yield.out"
timeout 600 .venv/bin/python -m pytest tests -q > "$R/pytest.out" 2>&1
echo "rc=$?" >> "$R/pytest.out"
timeout 600 .venv/bin/typediff --python-version 3.13 kb-selftest > "$R/kb.out" 2>&1
echo "rc=$?" >> "$R/kb.out"
grep -c 'PASS' "$R/kb.out" > "$R/kb-pass-count.out" 2>&1
grep -c 'FAIL' "$R/kb.out" > "$R/kb-fail-count.out" 2>&1
timeout 300 .venv/bin/python campaign/day4m/check_hits.py 0.80 > "$R/hits.out" 2>&1
echo "rc=$?" >> "$R/hits.out"
ls runs/hits | wc -l > "$R/hits-count.out" 2>&1
echo finished > "$R/done"
