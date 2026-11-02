#!/usr/bin/env bash
# Stage 3 round 2, step 3a: triage runs/day2/out1 + pattern tables (tuning + hold-out)
export TYPEDIFF_LLM=null
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd $R || exit 1
source $R/.venv/bin/activate
typediff triage runs/day2/out1 --top 30 --details > campaign/s3-r2-triage-top30.txt 2>&1
python scripts/kbloop_patterns.py runs/day2/out1 --set tuning --top 40 --md campaign/s3-r2-patterns-tuning.md > campaign/s3-r2-patterns-tuning.txt 2>&1
python scripts/kbloop_patterns.py runs/day2/out1 --set holdout --top 40 > campaign/s3-r2-patterns-holdout.txt 2>&1
echo done > campaign/s3-r2-triage.done
