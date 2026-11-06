#!/bin/bash
# draft 11 evidence: pyright on `class X(TypedDict, closed=True)` with typing.TypedDict at several target versions, plus extra_items= and typing_extensions controls
K=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
P=$K/campaign/day10/phase6
MG=/home/derek/.config/kiro-hooks/memguard.sh
D=$P/repro2
cat > $D/t1.py <<'EOF'
from typing import TypedDict


class Config(TypedDict, closed=True):
    name: str


cfg: Config = {"name": "a"}
bad: Config = {"name": "a", "extra": 1}
print(cfg)
EOF
cat > $D/t2.py <<'EOF'
from typing import TypedDict


class Config(TypedDict, extra_items=int):
    name: str


print(Config)
EOF
cat > $D/t3.py <<'EOF'
from typing_extensions import TypedDict


class Config(TypedDict, closed=True):
    name: str


bad: Config = {"name": "a", "extra": 1}
print(Config)
EOF
{
for f in t1 t2 t3; do
  echo "##### $f.py"
  cat $D/$f.py | head -0
  echo "--- cpython 3.13.16"; (cd $D && timeout 30 $K/.venv/bin/python $f.py 2>&1 | tail -2)
  for v in 3.12 3.13 3.14 3.15; do
    echo "--- pyright 1.1.414 --pythonversion $v"; timeout 120 $K/.venv/bin/pyright --pythonversion $v $D/$f.py 2>&1 | sed "s#$D/##" | head -8
  done
  for v in 3.13 3.15; do
    echo "--- mypy 2.4.0 --python-version $v"; timeout 120 $K/.venv/bin/mypy --python-version $v --no-incremental $D/$f.py 2>&1 | sed "s#$K/campaign/day10/phase6/repro2/##" | head -6
    echo "--- ty 0.0.97 --python-version $v"; timeout 90 $K/.venv/bin/ty check --python-version $v $D/$f.py 2>&1 | grep -E "^(error|warning)|Found|All checks" | head -6
  done
done
} > $P/results2/td_versions.txt 2>&1
echo done
