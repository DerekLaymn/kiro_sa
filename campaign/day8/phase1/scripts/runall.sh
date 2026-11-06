#!/bin/bash
# usage: runall.sh file.py [more files]  -> output of cpython, mypy, ty, pyright (pinned, pipeline flags)
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
for f in "$@"; do
d=$(mktemp -d /tmp/d8/w.XXXXXX)
cp "$f" "$d/case.py"
echo "##### $f"
echo "--- cpython"; (cd "$d" && timeout 20 /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.venv/bin/python case.py 2>&1 | tail -5)
echo "--- mypy"; (cd "$d" && timeout 120 /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.venv/bin/mypy --python-version 3.13 --check-untyped-defs --show-column-numbers --show-error-codes --no-error-summary --no-color-output --hide-error-context --no-incremental case.py 2>&1 | head -30)
echo "--- ty"; (cd "$d" && timeout 120 /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.venv/bin/ty check --python-version 3.13 --output-format concise --no-progress --color never case.py 2>&1 | head -30)
echo "--- pyright"; (cd "$d" && timeout 120 /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.venv/bin/pyright --pythonversion 3.13 case.py 2>&1 | head -30)
rm -rf "$d"
done
