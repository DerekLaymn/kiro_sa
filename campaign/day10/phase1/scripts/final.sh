#!/bin/bash
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
R=campaign/day10/phase1/results
rm -f $R/final.done
.venv/bin/python -m pytest tests -q -p no:cacheprovider > $R/pytest.out 2>&1; echo "rc=$?" >> $R/pytest.out
.venv/bin/typediff --python-version 3.13 kb-selftest > $R/kb-selftest.out 2>&1; echo "rc=$?" >> $R/kb-selftest.out
grep -c "^PASS" $R/kb-selftest.out > $R/kb-pass-count.out; grep -c "^FAIL" $R/kb-selftest.out >> $R/kb-pass-count.out
.venv/bin/python campaign/day4m/check_hits.py 0.80 > $R/check_hits.out 2>&1; echo "rc=$?" >> $R/check_hits.out
touch $R/final.done
