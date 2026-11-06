#!/bin/bash
K=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
P=$K/campaign/day9/phase6
cd $K || exit 1
timeout 900 .venv/bin/python -m pytest tests -q > $P/results/pytest.out 2>&1
echo "pytest rc=$?" >> $P/results/pytest.out
timeout 600 .venv/bin/typediff --python-version 3.13 kb-selftest > $P/results/kb-selftest.out 2>&1
echo "kb-selftest rc=$?" >> $P/results/kb-selftest.out
timeout 300 .venv/bin/python campaign/day4m/check_hits.py 0.80 > $P/results/check_hits.out 2>&1
echo "check_hits rc=$?" >> $P/results/check_hits.out
echo finished > $P/results/final_checks.done
