#!/bin/bash
# tool versions + newest releases (read-only; gh release list, PyPI json)
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
echo "== pins (.venv)"
.venv/bin/python --version
.venv/bin/ty --version
.venv/bin/mypy --version
.venv/bin/pyright --version
echo "== /tmp/d9v/ty99"
/tmp/d9v/ty99/bin/ty --version 2>&1
echo "== /tmp/d3v-latest"
/tmp/d3v-latest/bin/mypy --version 2>&1
echo "== /tmp/d3v-master"
/tmp/d3v-master/bin/mypy --version 2>&1
echo "== gh release list ty"
timeout 40 gh release list --repo astral-sh/ty --limit 4 2>&1
echo "== gh release list mypy"
timeout 40 gh release list --repo python/mypy --limit 3 2>&1
echo "== gh release list pyright"
timeout 40 gh release list --repo microsoft/pyright --limit 3 2>&1
echo "== pypi latest"
for p in ty mypy pyright; do
timeout 40 curl -s https://pypi.org/pypi/$p/json | .venv/bin/python -c "import json,sys; d=json.load(sys.stdin); print('$p', d['info']['version'], d['releases'][d['info']['version']][0]['upload_time'])"
done
date -u
