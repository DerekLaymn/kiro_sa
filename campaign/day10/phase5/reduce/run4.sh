#!/usr/bin/env bash
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd /tmp/d10p5/reduce || exit 1
grep -v "^assert describe(3) == 4" d.py > f.py
grep -v "^assert issubclass" d.py > g.py
grep -v "^assert describe" d.py > h.py
grep -v "^assert describe('a')" d.py > i.py
for f in d f g h i; do
  echo "=== $f ty"; timeout 60 "$ROOT/.venv/bin/ty" check --python-version 3.13 --output-format concise $f.py 2>&1
done
