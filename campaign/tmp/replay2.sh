#!/usr/bin/env bash
export TYPEDIFF_LLM=null
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd $R || exit 1
date > campaign/s3-r2-replay.start
rm -f campaign/s3-r2-replay.done
$R/.venv/bin/python scripts/kbloop_replay.py runs/day2/out1 runs/day2/out2 --jobs 14 --verify-sample 100 > campaign/s3-r2-replay.log 2>&1
echo "replay exit=$?" >> campaign/s3-r2-replay.log
$R/.venv/bin/python scripts/kbloop_stats.py runs/day2/out2 --split runs/day2/split --json runs/day2/out2-stats.json > runs/day2/out2-stats.txt 2>&1
date > campaign/s3-r2-replay.done
