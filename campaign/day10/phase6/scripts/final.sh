#!/bin/bash
# phase 6 final checks: pytest (expect 730 passed), kb-selftest (expect 20 PASS), check_hits
K=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
P=$K/campaign/day10/phase6/results
cd $K || exit 1
echo started > $P/final.status
timeout 900 .venv/bin/python -m pytest tests -q > $P/pytest.out 2>&1
echo "pytest rc=$?" >> $P/final.status
timeout 600 .venv/bin/typediff --python-version 3.13 kb-selftest > $P/kb-selftest.out 2>&1
echo "kb-selftest rc=$?" >> $P/final.status
grep -c "PASS" $P/kb-selftest.out > $P/kb-pass-count.out 2>&1
grep -c "FAIL" $P/kb-selftest.out >> $P/kb-pass-count.out 2>&1
timeout 300 .venv/bin/python campaign/day4m/check_hits.py 0.80 > $P/check_hits.out 2>&1
echo "check_hits rc=$?" >> $P/final.status
echo finished >> $P/final.status
