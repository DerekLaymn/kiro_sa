#!/bin/bash
# usage: run_all.sh file...   (runs cpython, ty0.0.97, mypy 2.4.0/2.4.1/master, pyright)
K=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
for f in "$@"; do
  echo "################ $f"
  echo "--- CPython $($K/.venv/bin/python --version 2>&1)"
  (cd "$(dirname "$f")" && timeout 60 $K/.venv/bin/python "$(basename "$f")" 2>&1 | tail -4; echo "exit=${PIPESTATUS[0]}")
  echo "--- ty $($K/.venv/bin/ty --version 2>&1 | tail -1)"
  timeout 120 $K/.venv/bin/ty check --python-version 3.13 "$f" 2>&1 | grep -v '^$'; echo "exit=${PIPESTATUS[0]}"
  echo "--- mypy 2.4.0"
  timeout 120 $K/.venv/bin/mypy --python-version 3.13 --no-incremental --no-error-summary "$f" 2>&1; echo "exit=${PIPESTATUS[0]}"
  echo "--- mypy 2.4.1"
  timeout 120 /tmp/d3v-latest/bin/mypy --python-version 3.13 --no-incremental --no-error-summary "$f" 2>&1; echo "exit=${PIPESTATUS[0]}"
  echo "--- mypy master 2.5.0+dev.879da562"
  timeout 120 /tmp/d3v-master/bin/mypy --python-version 3.13 --no-incremental --no-error-summary "$f" 2>&1; echo "exit=${PIPESTATUS[0]}"
  echo "--- pyright"
  timeout 120 $K/.venv/bin/pyright --pythonversion 3.13 "$f" 2>&1 | grep -v '^$' | tail -12; echo "exit=${PIPESTATUS[0]}"
done
