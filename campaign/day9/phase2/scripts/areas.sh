#!/usr/bin/env bash
# usage: areas.sh before|after  -> areas without a parent and the hit-similarity check (threshold 0.80)
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
R=campaign/day9/phase2/results
mkdir -p "$R"
.venv/bin/python campaign/day7/partB/areas_without_hits.py > "$R/areas-without-hits-$1.txt" 2>&1
.venv/bin/python campaign/day4m/check_hits.py 0.80 > "$R/check_hits-$1.out" 2>&1
echo "check_hits rc=$?" >> "$R/check_hits-$1.out"
tail -4 "$R/check_hits-$1.out"
ls runs/hits/*.py | wc -l
