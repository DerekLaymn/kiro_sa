#!/usr/bin/env bash
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
F=campaign/day8/phase2/repro/d1.py
echo "== CPython"; .venv/bin/python $F 2>&1 | head
echo "== ty 0.0.97"; .venv/bin/ty check --output-format concise --python-version 3.13 $F 2>&1 | head -20
echo "== mypy"; .venv/bin/mypy --python-version 3.13 $F 2>&1 | head -20
echo "== pyright"; .venv/bin/pyright --pythonversion 3.13 $F 2>&1 | head -20
echo "== gh search (read-only)"
gh search issues --repo astral-sh/ty "__post_init__" --limit 15 --json number,title,state 2>&1 | head -40
gh search issues --repo astral-sh/ty "InitVar post_init" --limit 15 --json number,title,state 2>&1 | head -40
