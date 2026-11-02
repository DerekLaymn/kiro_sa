#!/usr/bin/env bash
export TYPEDIFF_LLM=null
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
B=/tmp/s3base
cd $R || exit 1
head -c 120 campaign/s3-r1-calib-fetch.txt; echo
$R/.venv/bin/python - <<'EOF'
import json
c = json.load(open("calibration/positives.json"))
from collections import Counter
print(len(c), Counter(x["faulty_tool"] for x in c))
EOF
# baseline workspace: pre-change package + the same positives + baseline-era negatives (HEAD) + the runner script
mkdir -p $B/calibration $B/scripts
cp calibration/positives.json $B/calibration/
rm -rf $B/calibration/negatives && mkdir -p $B/calibration/negatives
git archive HEAD calibration/negatives | tar -x -C $B
cp scripts/kbloop_calib_subset.py $B/kbloop_calib_subset.py
ls $B $B/calibration/negatives
cd $B && $R/.venv/bin/python -c "import typediff; print('baseline typediff from', typediff.__file__)"
# is gitignored? positives.json
cd $R && git check-ignore -v calibration/positives.json
