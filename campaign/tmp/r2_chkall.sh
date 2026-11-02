#!/usr/bin/env bash
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
OUT=$R/campaign/s3-r2-chk-reps.txt
: > $OUT
for f in rec intlit tupcmp; do
  CHK_OUT=20 bash $R/campaign/tmp/chk.sh $R/campaign/tmp/r2rep/$f.py >> $OUT 2>&1
done
