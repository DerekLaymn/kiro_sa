#!/usr/bin/env bash
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
ls $R/campaign/s3-r1-calib-*.done 2>/dev/null | wc -l
tail -n 2 $R/campaign/s3-r1-calib-before-0.txt $R/campaign/s3-r1-calib-after-0.txt
$R/.venv/bin/python $R/campaign/tmp/calib_compare.py > $R/campaign/s3-r1-calib-compare.txt 2>&1
