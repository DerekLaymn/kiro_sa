#!/usr/bin/env bash
# launches 8 detached calibration workers (4 baseline-code, 4 current-code)
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
for w in before after; do
  for k in 0 1 2 3; do
    setsid nohup bash $R/campaign/tmp/calib_run.sh $w $k 4 > /dev/null 2>&1 < /dev/null &
  done
done
sleep 2
pgrep -f kbloop_calib_subset | wc -l
