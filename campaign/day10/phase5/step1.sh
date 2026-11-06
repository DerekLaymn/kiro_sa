#!/usr/bin/env bash
# Day 10 phase 5 step 1 (read-only): check_hits before, strong-evidence list, parent yield.
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd "$ROOT" || exit 1
P=campaign/day10/phase5
timeout 600 .venv/bin/python campaign/day4m/check_hits.py 0.80 > $P/check_hits-before.out 2>&1
echo "check_hits rc=$?" >> $P/check_hits-before.out
timeout 300 .venv/bin/python $P/strong_live.py > $P/strong_live.out 2>&1
echo "strong_live rc=$?"
timeout 300 .venv/bin/python $P/parent_yield.py > $P/parent_yield.out 2>&1
echo "parent_yield rc=$?"
tail -n 4 $P/check_hits-before.out
