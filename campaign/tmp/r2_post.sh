#!/usr/bin/env bash
export TYPEDIFF_LLM=null
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd $R || exit 1
PY=$R/.venv/bin/python
$PY campaign/tmp/diff_runs.py runs/day2/out1 runs/day2/out2 runs/day2/split > campaign/s3-r2-diff-out1-out2.txt 2>&1
$PY campaign/tmp/diff_runs.py runs/day2/out0 runs/day2/out2 runs/day2/split > campaign/s3-r2-diff-out0-out2.txt 2>&1
$PY campaign/tmp/r2_audit.py runs/day2/out2 runs/day2/split > campaign/s3-r2-audit.txt 2>&1
$PY campaign/tmp/r2_raised.py runs/day2/out2 > campaign/s3-r2-raised.txt 2>&1
$PY campaign/tmp/r2_trans.py runs/day2/out1 runs/day2/out2 > campaign/s3-r2-trans.txt 2>&1
$PY scripts/kbloop_patterns.py runs/day2/out2 --set tuning --top 25 --md campaign/s3-r2-patterns-after-tuning.md > campaign/s3-r2-patterns-after-tuning.txt 2>&1
$PY scripts/kbloop_patterns.py runs/day2/out2 --set holdout --top 15 > campaign/s3-r2-patterns-after-holdout.txt 2>&1
date > campaign/s3-r2-post.done
