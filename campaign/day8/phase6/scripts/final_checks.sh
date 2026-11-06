K=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd $K
R=campaign/day8/phase6/results
echo "start $(date -Is)" > $R/final-checks.start
.venv/bin/python -m pytest tests -q > $R/pytest.out 2>&1
echo "pytest rc=$?" >> $R/pytest.out
.venv/bin/typediff --python-version 3.13 kb-selftest > $R/kb-selftest.out 2>&1
echo "kb-selftest rc=$?" >> $R/kb-selftest.out
.venv/bin/python campaign/day4m/check_hits.py 0.80 > $R/check_hits.out 2>&1
echo "check_hits rc=$?" >> $R/check_hits.out
echo "end $(date -Is)" > $R/final-checks.done
