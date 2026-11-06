#!/usr/bin/env bash
# Day 8 phase 5: tool output on the pins for the candidates that were not promoted (evidence for run-log item 41).
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
W=/tmp/d8p5/probe
rm -rf "$W"; mkdir -p "$W"; cd "$W" || exit 1
cp "$ROOT/runs/day8/gen/overloads/rsv_overloads_d41747bd__mut0_1de657a6.py" ov.py
cp "$ROOT/runs/day8/gen/overloads/gen12_a368580c.py" g12.py
cp "$ROOT/runs/day8/gen/descriptors_properties/d4p_descriptors_readonly_prop_never__mut1_17c399aa.py" m1.py
cat > m2.py <<'EOF'
class Counter:
    def __init__(self, start: int) -> None:
        self.base = start

    @property
    def readonly(self) -> int:
        return self.base


def try_write(c: Counter) -> bool:
    try:
        c.readonly = 0
    except AttributeError:
        return True
    return False
EOF
for f in ov g12 m1 m2; do
  for t in mypy ty pyright; do
    echo "=== $f.py $t"
    case $t in
      mypy) "$ROOT/.venv/bin/mypy" --python-version 3.13 $f.py 2>&1 | head -30 ;;
      ty) "$ROOT/.venv/bin/ty" check --python-version 3.13 --output-format concise $f.py 2>&1 | head -30 ;;
      pyright) "$ROOT/.venv/bin/pyright" --pythonversion 3.13 $f.py 2>&1 | head -30 ;;
    esac
  done
done
