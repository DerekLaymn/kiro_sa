#!/usr/bin/env bash
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
$R/.venv/bin/python $R/campaign/tmp/diff_runs.py $R/runs/day2/out0 $R/runs/day2/out1 $R/runs/day2/split > $R/campaign/s3-r1-diff-out0-out1.txt 2>&1
