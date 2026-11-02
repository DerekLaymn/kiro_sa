#!/usr/bin/env bash
# usage: calib_run.sh before|after K N   (chunk K of N of the positives; chunk 0 also runs the negatives)
export TYPEDIFF_LLM=null
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
PY=$R/.venv/bin/python
which_run=$1; K=$2; N=$3
if [ "$which_run" = "before" ]; then
  WD=/tmp/s3base
  SCRIPT=/tmp/s3base/kbloop_calib_subset.py
else
  WD=$R
  SCRIPT=$R/scripts/kbloop_calib_subset.py
fi
OUT=$R/runs/day2/calib-$which_run-$K
cd $WD || exit 1
IDS=$($PY -c "import json;c=json.load(open('calibration/positives.json'));print(' '.join(x['id'] for i,x in enumerate(c) if i % $N == $K))")
NEG=""
if [ "$K" = "0" ]; then NEG="--negatives"; fi
date > $R/campaign/s3-r1-calib-$which_run-$K.start
$PY $SCRIPT $OUT $IDS $NEG > $R/campaign/s3-r1-calib-$which_run-$K.txt 2>&1
echo "exit=$?" >> $R/campaign/s3-r1-calib-$which_run-$K.txt
date > $R/campaign/s3-r1-calib-$which_run-$K.done
