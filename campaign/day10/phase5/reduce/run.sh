#!/usr/bin/env bash
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd /tmp/d10p5/reduce || exit 1
for f in a b; do
  echo "=== $f ty"; timeout 60 "$ROOT/.venv/bin/ty" check --python-version 3.13 $f.py 2>&1 | grep -E "error|warning|info" | head -12
  echo "=== $f mypy"; timeout 120 "$ROOT/.venv/bin/mypy" --python-version 3.13 --no-incremental $f.py 2>&1 | head -12
  echo "=== $f pyright"; timeout 120 "$ROOT/.venv/bin/pyright" $f.py 2>&1 | grep -E "error|information|warning" | head -12
done
