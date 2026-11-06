#!/bin/bash
# usage: runall.sh file.py   -> CPython, ty 0.0.97 (pin) + 0.0.99 (newest), mypy 2.4.0 (pin) + 2.4.1 + master, pyright 1.1.414; prints exit codes
# every checker runs under the memguard shim (.venv/bin) or memguard.sh directly, plus a wall-clock timeout
K=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
MG=/home/derek/.config/kiro-hooks/memguard.sh
f="$1"
d=$(dirname "$f")
b=$(basename "$f")
echo "##### $b"
echo "--- cpython 3.13.16"
(cd "$d" && timeout 30 $K/.venv/bin/python "$b" 2>&1 | tail -8; echo "rc=${PIPESTATUS[0]}")
echo "--- ty 0.0.97 (.venv, the pin)"
timeout 90 $K/.venv/bin/ty check --python-version 3.13 "$f" 2>&1 | head -60; echo "rc=${PIPESTATUS[0]}"
echo "--- ty 0.0.99 (/tmp/d9v/ty99, newest release, verification only)"
timeout 90 $MG /tmp/d9v/ty99/bin/ty check --python-version 3.13 "$f" 2>&1 | head -60; echo "rc=${PIPESTATUS[0]}"
echo "--- mypy 2.4.0 (.venv, the pin)"
timeout 120 $K/.venv/bin/mypy --python-version 3.13 --no-incremental "$f" 2>&1 | head -40; echo "rc=${PIPESTATUS[0]}"
echo "--- mypy 2.4.1 (/tmp/d3v-latest)"
timeout 120 $MG /tmp/d3v-latest/bin/mypy --python-version 3.13 --no-incremental "$f" 2>&1 | head -40; echo "rc=${PIPESTATUS[0]}"
echo "--- mypy master 2.5.0+dev.879da562 (/tmp/d3v-master)"
timeout 120 $MG /tmp/d3v-master/bin/mypy --python-version 3.13 --no-incremental "$f" 2>&1 | head -40; echo "rc=${PIPESTATUS[0]}"
echo "--- pyright 1.1.414 (.venv, the pin)"
timeout 120 $K/.venv/bin/pyright --pythonversion 3.13 "$f" 2>&1 | head -40; echo "rc=${PIPESTATUS[0]}"
