#!/bin/bash
K=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
for n in gen0_b82d2e9e gen21_6ee04c3a gen8_88778d35; do
  f=$(find $K/runs/day9/gen -name "$n.py" | head -1)
  echo "=============== $f"
  cat "$f"
  echo "--- pyright 1.1.414"
  timeout 120 $K/.venv/bin/pyright --pythonversion 3.13 "$f" 2>&1 | head -20
  echo "--- ty 0.0.97"
  timeout 90 $K/.venv/bin/ty check --python-version 3.13 "$f" 2>&1 | head -30
  echo "--- mypy 2.4.0"
  timeout 90 $K/.venv/bin/mypy --python-version 3.13 --no-incremental "$f" 2>&1 | head -10
  echo "--- cpython"
  (cd "$(dirname "$f")" && timeout 30 $K/.venv/bin/python "$(basename "$f")" 2>&1 | tail -5)
done
