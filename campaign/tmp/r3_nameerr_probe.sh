#!/usr/bin/env bash
# toggle experiment: does mypy report the name when the opt-in checks are enabled?
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
for f in "$@"; do
  echo "== $f"
  echo "-- mypy default"
  .venv/bin/mypy --python-version 3.13 "$f" | tail -3
  echo "-- mypy --enable-error-code possibly-undefined --enable-error-code used-before-def"
  .venv/bin/mypy --python-version 3.13 --enable-error-code possibly-undefined --enable-error-code used-before-def "$f" | tail -3
  echo "-- ty"
  .venv/bin/ty check "$f" 2>&1 | grep -E "^(error|warning)"
  echo "-- cpython"
  .venv/bin/python "$f" 2>&1 | tail -1
done
