#!/usr/bin/env bash
export TYPEDIFF_LLM=null
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd $R || exit 1
rm -rf /tmp/s3base && mkdir -p /tmp/s3base
git archive HEAD typediff | tar -x -C /tmp/s3base
echo "baseline package files:"; ls /tmp/s3base/typediff | head -3
PYTHONPATH=/tmp/s3base $R/.venv/bin/python -c "import typediff; print('baseline typediff from', typediff.__file__)"
$R/.venv/bin/python campaign/tmp/calib_fetch.py > campaign/s3-r1-calib-fetch.txt 2>&1
tail -c 600 campaign/s3-r1-calib-fetch.txt
git status --short | head
