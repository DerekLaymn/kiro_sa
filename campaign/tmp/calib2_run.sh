#!/usr/bin/env bash
# usage: calib2_run.sh K N   (chunk K of N of the positives; chunk 0 also runs the negatives). Current working-tree code.
# Same settings as `typediff --no-pyright calibrate` (scripts/kbloop_calib_subset.py).
export TYPEDIFF_LLM=null
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
PY=$R/.venv/bin/python
K=$1; N=$2
OUT=$R/runs/day2/calib2-after-$K
cd $R || exit 1
IDS=$($PY -c "import json;c=json.load(open('calibration/positives.json'));print(' '.join(x['id'] for i,x in enumerate(c) if i % $N == $K))")
NEG=""
if [ "$K" = "0" ]; then NEG="--negatives"; fi
date > $R/campaign/s3-r2-calib-after-$K.start
$PY $R/scripts/kbloop_calib_subset.py $OUT $IDS $NEG > $R/campaign/s3-r2-calib-after-$K.txt 2>&1
echo "exit=$?" >> $R/campaign/s3-r2-calib-after-$K.txt
date > $R/campaign/s3-r2-calib-after-$K.done
