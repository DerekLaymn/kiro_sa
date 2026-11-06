#!/bin/bash
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
mkdir -p campaign/day8/phase1/iter2
.venv/bin/python -m pytest tests/test_day8_pipeline.py -q -x 2>&1 | tail -40
