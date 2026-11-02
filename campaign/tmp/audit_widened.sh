#!/usr/bin/env bash
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
$R/.venv/bin/python $R/campaign/tmp/audit_widened.py $R/runs/day2/out1 > $R/campaign/s3-r1-audit-widened.txt 2>&1
