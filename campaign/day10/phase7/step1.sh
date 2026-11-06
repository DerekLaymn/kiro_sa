#!/bin/bash
# Day 10 phase 7: group yield from the saved judge output (no judge re-run), the stats of the replayed (final-KB) reports,
# and the group sizes. Output in results/.
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
R=campaign/day10/phase7/results
mkdir -p "$R"
git rev-parse --short HEAD > "$R/head.out" 2>&1
git branch --show-current >> "$R/head.out" 2>&1
timeout 120 .venv/bin/python campaign/day10/phase7/group_yield.py runs/day10/out > "$R/group_yield.out" 2>&1
echo "rc=$?" >> "$R/group_yield.out"
ls runs/day10/replay2 > "$R/replay2-ls.out" 2>&1
if [ -d runs/day10/replay2/day10 ]; then
  timeout 120 .venv/bin/python campaign/day10/phase7/group_yield.py runs/day10/replay2/day10 > "$R/group_yield_replayed.out" 2>&1
  echo "rc=$?" >> "$R/group_yield_replayed.out"
  TYPEDIFF_LLM=null timeout 120 .venv/bin/python scripts/kbloop_stats.py runs/day10/replay2/day10 > "$R/stats_replayed.out" 2>&1
  echo "rc=$?" >> "$R/stats_replayed.out"
fi
for g in runs/day10/parents/*; do echo "$(basename $g) $(ls $g | wc -l)"; done > "$R/group_sizes.out" 2>&1
ls runs/hits | wc -l > "$R/hits-count.out" 2>&1
ls runs/hits-dropped | wc -l >> "$R/hits-count.out" 2>&1
timeout 300 .venv/bin/python campaign/day4m/check_hits.py 0.80 > "$R/hits.out" 2>&1
echo "rc=$?" >> "$R/hits.out"
echo finished > "$R/step1.done"
