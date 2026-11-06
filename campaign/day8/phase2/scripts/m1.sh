#!/usr/bin/env bash
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
F=campaign/day8/phase2/repro/m1.py
echo "== ty 0.0.97"; .venv/bin/ty check --output-format concise --python-version 3.13 $F 2>&1 | head -30
echo "== mypy"; .venv/bin/mypy --python-version 3.13 $F 2>&1 | head -20
echo "== pyright"; .venv/bin/pyright --pythonversion 3.13 $F 2>&1 | head -20
