#!/usr/bin/env bash
# usage: r2_redef.sh FILE  -> mypy reveal output with and without --allow-redefinition, and ty/pyright for reference
export TYPEDIFF_LLM=null
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
V=$R/.venv/bin
F="$1"
D=$(mktemp -d /tmp/s3redef.XXXXXX)
cp "$F" "$D/case.py"
cd "$D" || exit 1
M="--python-version 3.13 --check-untyped-defs --show-column-numbers --show-error-codes --no-error-summary --no-color-output --hide-error-context --no-incremental"
echo "--- mypy default"; $V/mypy $M case.py 2>&1 | head -${CHK_OUT:-60}
echo "--- mypy --allow-redefinition"; $V/mypy $M --allow-redefinition case.py 2>&1 | head -${CHK_OUT:-60}
echo "--- ty"; $V/ty check --python-version 3.13 --output-format concise --no-progress --color never case.py 2>&1 | head -${CHK_OUT:-60}
rm -rf "$D"
