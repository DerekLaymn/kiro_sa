#!/usr/bin/env bash
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
G=$ROOT/runs/day10/gen
cd /tmp/d10p5/reduce || exit 1
cp "$G/paramspec_concatenate/hv_paramspec_concatenate__conformance__generics_paramspec_components__mut0_66a0b5b8.py" c.py
cp "$G/overloads/hv_overloads__conformance__overloads_definitions__mut1_59eaed87.py" d.py
echo "=== c mypy"; timeout 120 "$ROOT/.venv/bin/mypy" --python-version 3.13 --no-incremental c.py 2>&1 | head -12
echo "=== a ty full"; timeout 60 "$ROOT/.venv/bin/ty" check --python-version 3.13 --output-format concise a.py 2>&1 | head
echo "=== d ty"; timeout 60 "$ROOT/.venv/bin/ty" check --python-version 3.13 --output-format concise d.py 2>&1 | head -12
