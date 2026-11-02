#!/usr/bin/env bash
# usage: chk.sh FILE [extra mypy flags...]   (runs mypy, ty, pyright, CPython on FILE copied to an isolated dir)
export TYPEDIFF_LLM=null
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
V=$R/.venv/bin
F="$1"; shift
D=$(mktemp -d /tmp/s3chk.XXXXXX)
cp "$F" "$D/case.py"
cd "$D" || exit 1
echo "===== $F"
echo "--- source"; cat -n case.py | head -${CHK_LINES:-60}
echo "--- mypy"; $V/mypy --python-version 3.13 --check-untyped-defs --show-column-numbers --show-error-codes --no-error-summary --no-color-output --hide-error-context --no-incremental "$@" case.py 2>&1 | head -${CHK_OUT:-25}
echo "--- ty"; $V/ty check --python-version 3.13 --output-format concise --no-progress --color never case.py 2>&1 | head -${CHK_OUT:-25}
echo "--- pyright"; $V/pyright --pythonversion 3.13 case.py 2>&1 | head -${CHK_OUT:-25}
echo "--- cpython"; $V/python -I case.py 2>&1 | tail -4
rm -rf "$D"
