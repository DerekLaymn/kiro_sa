cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
for f in constructors_metaclasses/gen1_c86958a8.py typevartuple_unpack/gen1_4d7d067f.py; do
  echo "=== $f"
  echo "-- mypy"; .venv/bin/mypy --python-version 3.13 runs/day9/gen/$f 2>&1 | head -20
  echo "-- ty"; .venv/bin/ty check --python-version 3.13 runs/day9/gen/$f 2>&1 | head -40
  echo "-- pyright"; .venv/bin/pyright --pythonversion 3.13 runs/day9/gen/$f 2>&1 | head -20
  echo "-- run"; .venv/bin/python runs/day9/gen/$f 2>&1 | head
done
