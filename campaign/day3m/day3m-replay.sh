#!/bin/bash
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd $R
date > campaign/day3m-replay.start
$R/.venv/bin/python $R/scripts/kbloop_replay.py $R/runs/day2/out3 $R/runs/day3/replay --jobs 14 --verify-sample 50 > campaign/day3m-replay.log 2>&1
echo "exit $?" >> campaign/day3m-replay.log
date > campaign/day3m-replay.done
