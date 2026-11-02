#!/usr/bin/env bash
export TYPEDIFF_LLM=null
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
PY=.venv/bin/python
$PY scripts/kbloop_stats.py runs/day2/out0 --split runs/day2/split > campaign/s3-r1-baseline-stats.txt 2>&1
.venv/bin/typediff triage runs/day2/out0 --top 30 --details > campaign/s3-r1-triage-top30.txt 2>&1
$PY scripts/kbloop_patterns.py runs/day2/out0 --split runs/day2/split --top 40 --md campaign/s3-r1-patterns-tuning.md > campaign/s3-r1-patterns-tuning.txt 2>&1
$PY scripts/kbloop_patterns.py runs/day2/out0 --split runs/day2/split --set holdout --top 40 > campaign/s3-r1-patterns-holdout.txt 2>&1
echo done > campaign/s3-r1-baseline.done
