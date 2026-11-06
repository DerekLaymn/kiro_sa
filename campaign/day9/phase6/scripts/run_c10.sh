#!/bin/bash
# swallowing context manager: default config and with the opt-in possibly-undefined checks
K=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
MG=/home/derek/.config/kiro-hooks/memguard.sh
P=$K/campaign/day9/phase6
for n in ${@:-c10 c10b c10ctl}; do
  f=$P/repro/$n.py
  echo "##### $n extra flags"
  echo "--- ty 0.0.97 --warn possibly-unresolved-reference"
  timeout 90 $K/.venv/bin/ty check --python-version 3.13 --warn possibly-unresolved-reference "$f" 2>&1 | head -30; echo "rc=${PIPESTATUS[0]}"
  echo "--- ty 0.0.99 --warn possibly-unresolved-reference"
  timeout 90 $MG /tmp/d9v/ty99/bin/ty check --python-version 3.13 --warn possibly-unresolved-reference "$f" 2>&1 | head -30; echo "rc=${PIPESTATUS[0]}"
  echo "--- mypy 2.4.0 --enable-error-code possibly-undefined"
  timeout 90 $K/.venv/bin/mypy --python-version 3.13 --no-incremental --enable-error-code possibly-undefined "$f" 2>&1 | head -10; echo "rc=${PIPESTATUS[0]}"
  echo "--- mypy master --enable-error-code possibly-undefined"
  timeout 90 $MG /tmp/d3v-master/bin/mypy --python-version 3.13 --no-incremental --enable-error-code possibly-undefined "$f" 2>&1 | head -10; echo "rc=${PIPESTATUS[0]}"
done
