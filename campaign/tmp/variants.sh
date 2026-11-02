#!/usr/bin/env bash
export TYPEDIFF_LLM=null
V=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.venv/bin
D=$(mktemp -d /tmp/s3var.XXXXXX)
cd $D
printf 'class F(E): pass\nclass E: pass\n' > v1_base.py
printf 'a = C()\nclass C: pass\n' > v2_call.py
printf 'def f(x: C) -> None: ...\nclass C: pass\n' > v3_annot.py
printf 'x: C\nclass C: pass\n' > v4_varannot.py
printf 'class A:\n    y = C\nclass C: pass\n' > v5_classbody.py
printf '@d\ndef f(): ...\ndef d(fn): return fn\n' > v6_decorator.py
printf 'from typing import Generic, TypeVar\nT = TypeVar("T")\nclass F(Generic[T], E): pass\nclass E: pass\n' > v7_base_mixed.py
printf 'X = E\nclass E: pass\n' > v8_alias.py
for f in v1_base v2_call v3_annot v4_varannot v5_classbody v6_decorator v7_base_mixed v8_alias; do
  echo "######## $f: $(tr '\n' '|' < $f.py)"
  echo "--- mypy"; $V/mypy --python-version 3.13 --no-incremental --show-error-codes --no-error-summary $f.py 2>&1 | head -4
  echo "--- ty"; $V/ty check --python-version 3.13 --output-format concise --no-progress --color never $f.py 2>&1 | head -3
  echo "--- pyright"; $V/pyright --pythonversion 3.13 $f.py 2>&1 | grep -E "error|warning" | head -3
  echo "--- cpython"; $V/python -I $f.py 2>&1 | tail -1
done
rm -rf $D
