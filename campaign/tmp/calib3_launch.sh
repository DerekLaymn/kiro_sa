#!/usr/bin/env bash
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd $R || exit 1
for k in 0 1 2 3; do
  nohup bash campaign/tmp/calib3_run.sh $k 4 > /dev/null 2>&1 &
done
wait
