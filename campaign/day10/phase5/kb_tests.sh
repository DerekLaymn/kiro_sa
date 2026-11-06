#!/bin/bash
# Day 10 phase 5: run only the new KB test file (iteration), output to kb_tests.out
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
timeout 900 .venv/bin/python -m pytest tests/test_day10_morning.py -q -p no:cacheprovider -x -q > campaign/day10/phase5/kb_tests.out 2>&1
echo "rc=$?" >> campaign/day10/phase5/kb_tests.out
