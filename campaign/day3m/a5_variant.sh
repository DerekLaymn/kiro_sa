#!/bin/bash
# Does mypy still crash on A5 when the instance is actually bound (so CPython runs the call instead of raising NameError)?
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
D=$(mktemp -d)
cd $D
cat > orig.py <<'EOF'
from typing import Self
class C:
    __call__: Self | None
x: C
x()
EOF
cat > bound.py <<'EOF'
from typing import Self
class C:
    __call__: Self | None = None
x: C = C()
x()
EOF
for f in orig.py bound.py; do
  echo "== $f"
  echo "-- python"; $R/.venv/bin/python $f 2>&1 | tail -1
  echo "-- mypy"; $R/.venv/bin/mypy --python-version 3.13 --no-incremental --cache-dir=$D/.mc $f 2>&1 | tail -3; echo "exit=${PIPESTATUS[0]}"
  echo "-- ty"; $R/.venv/bin/ty check --python-version 3.13 --output-format concise --no-progress $f 2>&1 | tail -3
done
