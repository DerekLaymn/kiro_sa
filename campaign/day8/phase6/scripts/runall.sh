#!/bin/bash
# usage: runall.sh file.py   -> runs CPython and all checkers, prints exit codes
K=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
f="$1"
d=$(dirname "$f")
b=$(basename "$f")
echo "##### $f"
echo "--- cpython 3.13.16"
(cd "$d" && $K/.venv/bin/python "$b" 2>&1 | tail -8; echo "rc=${PIPESTATUS[0]}")
echo "--- ty 0.0.97 (.venv, the pin)"
$K/.venv/bin/ty check --python-version 3.13 "$f" 2>&1 | head -60; echo "rc=${PIPESTATUS[0]}"
echo "--- ty 0.0.98 (/tmp/d7pd/ty98, newest release, verification only)"
/tmp/d7pd/ty98/bin/ty check --python-version 3.13 "$f" 2>&1 | head -60; echo "rc=${PIPESTATUS[0]}"
echo "--- mypy 2.4.0 (.venv, the pin)"
$K/.venv/bin/mypy --python-version 3.13 --no-incremental "$f" 2>&1 | head -40; echo "rc=${PIPESTATUS[0]}"
echo "--- mypy 2.4.1 (/tmp/d3v-latest)"
/tmp/d3v-latest/bin/mypy --python-version 3.13 --no-incremental "$f" 2>&1 | head -40; echo "rc=${PIPESTATUS[0]}"
echo "--- mypy master 2.5.0+dev.879da562 (/tmp/d3v-master)"
/tmp/d3v-master/bin/mypy --python-version 3.13 --no-incremental "$f" 2>&1 | head -40; echo "rc=${PIPESTATUS[0]}"
echo "--- pyright 1.1.414 (.venv, the pin)"
$K/.venv/bin/pyright --pythonversion 3.13 "$f" 2>&1 | head -40; echo "rc=${PIPESTATUS[0]}"
