#!/bin/bash
# Day 10 phase 7: stats of the replayed Day 9 / 8 / 7 reports on the final Day-10 KB (saved by phase 5 in runs/day10/replay2),
# and the final checks (pytest, kb-selftest). Output in results/.
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
R=campaign/day10/phase7/results
mkdir -p "$R"
for d in day9 day8 day7; do
  TYPEDIFF_LLM=null timeout 120 .venv/bin/python scripts/kbloop_stats.py runs/day10/replay2/$d > "$R/stats_replayed_$d.out" 2>&1
  echo "rc=$?" >> "$R/stats_replayed_$d.out"
done
.venv/bin/python --version > "$R/pins.out" 2>&1
.venv/bin/ty --version >> "$R/pins.out" 2>&1
.venv/bin/mypy --version >> "$R/pins.out" 2>&1
.venv/bin/pyright --version >> "$R/pins.out" 2>&1
echo "stats done" > "$R/step2.stats.done"
timeout 900 .venv/bin/python -m pytest tests -q > "$R/pytest.out" 2>&1
echo "rc=$?" >> "$R/pytest.out"
timeout 600 .venv/bin/typediff --python-version 3.13 kb-selftest > "$R/kb.out" 2>&1
echo "rc=$?" >> "$R/kb.out"
grep -c 'PASS' "$R/kb.out" > "$R/kb-pass-count.out" 2>&1
grep -c 'FAIL' "$R/kb.out" > "$R/kb-fail-count.out" 2>&1
echo finished > "$R/step2.done"
