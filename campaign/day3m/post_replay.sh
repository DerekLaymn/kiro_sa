#!/bin/bash
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd $R
$R/.venv/bin/python $R/scripts/kbloop_stats.py $R/runs/day3/replay > campaign/day3m/stats-day3-replay.txt 2>&1
$R/.venv/bin/typediff --out $R/runs/day3/replay triage $R/runs/day3/replay --top 30 --details > campaign/day3m/triage-top30-details.txt 2>&1
$R/.venv/bin/typediff --out $R/runs/day3/replay triage $R/runs/day3/replay --top 60 > campaign/day3m/triage-top60.txt 2>&1
echo finished > campaign/day3m/post_replay.done
