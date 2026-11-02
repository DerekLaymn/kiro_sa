#!/usr/bin/env bash
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd $R || exit 1
ls -la calibration calibration/results | head -30
cat scripts/kbloop_calib_subset.py
grep -n -i "dismissed\|false dismissal\|0/80\|4/76" calibration/RESULTS.md | head -20
grep -rn -i "calibration" README.md | head -10
tail -3 campaign/s3-r1-replay.log
