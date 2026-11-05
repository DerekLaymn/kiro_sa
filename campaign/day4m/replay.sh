#!/bin/bash
# Day-4 morning: re-judge the Day-3 outputs under the final KB, then stats and the diff against the pre-change replay.
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
V=.venv/bin
$V/python scripts/kbloop_replay.py runs/day3/out runs/day4/replay-d3 --jobs 14 --verify-sample 30
echo "replay exit $?"
$V/python scripts/kbloop_stats.py runs/day4/replay-d3
$V/python campaign/day4m/live_dump.py runs/day4/replay-d3 --diff runs/day4/replay-d3-base
