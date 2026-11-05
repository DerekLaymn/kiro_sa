#!/bin/bash
# usage: runall.sh file.py   -> runs CPython and all checkers
K=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
f="$1"
d=$(dirname "$f")
echo "##### $f"
echo "--- cpython"
(cd "$d" && $K/.venv/bin/python "$f" 2>&1 | tail -6)
echo "--- ty 0.0.97 (.venv)"
$K/.venv/bin/ty check --python-version 3.13 "$f" 2>&1 | head -40
echo "--- ty latest (/tmp/d3v-latest)"
/tmp/d3v-latest/bin/ty --version
/tmp/d3v-latest/bin/ty check --python-version 3.13 "$f" 2>&1 | head -40
echo "--- ty 0.0.98 (/tmp/d7pd/ty98)"
/tmp/d7pd/ty98/bin/ty check --python-version 3.13 "$f" 2>&1 | head -40
echo "--- mypy 2.4.0 (.venv)"
$K/.venv/bin/mypy --python-version 3.13 --no-incremental "$f" 2>&1 | head -30
echo "--- mypy 2.4.1 (latest)"
/tmp/d3v-latest/bin/mypy --python-version 3.13 --no-incremental "$f" 2>&1 | head -30
echo "--- mypy master"
/tmp/d3v-master/bin/mypy --python-version 3.13 --no-incremental "$f" 2>&1 | head -30
echo "--- pyright (.venv)"
$K/.venv/bin/pyright --pythonversion 3.13 "$f" 2>&1 | head -30
echo "--- pyright (latest)"
/tmp/d3v-latest/bin/pyright --version 2>&1 | head -2
/tmp/d3v-latest/bin/pyright --pythonversion 3.13 "$f" 2>&1 | head -30
