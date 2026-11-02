#!/usr/bin/env bash
export TYPEDIFF_LLM=null
V=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.venv/bin
D=$(mktemp -d /tmp/s3ex.XXXXXX)
cd $D
printf 'from typing import Any, assert_type\n\nassert_type(slice(1234, None), "slice[int, Any, Any]")\n' > c1.py
printf 'from typing import assert_type\n\nassert_type((1, 2) < (3, 4), bool)\n' > c2.py
printf 'from typing import assert_type\n\nassert_type(max(1, 2), int)\n' > c3.py
for f in c1 c2 c3; do
  echo "######## $f"
  echo "--- mypy"; $V/mypy --python-version 3.13 --no-incremental --show-error-codes --no-error-summary $f.py 2>&1 | head -4
  echo "--- ty"; $V/ty check --python-version 3.13 --output-format concise --no-progress --color never $f.py 2>&1 | head -3
  echo "--- pyright"; $V/pyright --pythonversion 3.13 $f.py 2>&1 | grep -E "error" | head -3
  echo "--- cpython"; $V/python -I $f.py 2>&1 | tail -1
done
rm -rf $D
