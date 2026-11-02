#!/usr/bin/env bash
export TYPEDIFF_LLM=null
V=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.venv/bin
D=$(mktemp -d /tmp/s3p4.XXXXXX)
cd $D
cat > t1.py <<'EOF'
x = 1
x = "a"
reveal_type(x)
EOF
cat > t2.py <<'EOF'
x = 1
x /= 2
EOF
cat > t3.py <<'EOF'
def f(flag: bool) -> None:
    y = 1
    if flag:
        y = "s"
    print(y)
EOF
cat > t4.py <<'EOF'
x: int = 1
x = "a"
EOF
cat > t5.py <<'EOF'
def f(a: int) -> None:
    a = "s"
EOF
cat > t6.py <<'EOF'
for i in range(3):
    pass
i = "s"
EOF
cat > t7.py <<'EOF'
class A:
    z = 1
    z = "s"
EOF
for f in t1 t2 t3 t4 t5 t6 t7; do
  echo "######## $f: $(tr '\n' '|' < $f.py)"
  echo "--- mypy default"; $V/mypy --python-version 3.13 --no-incremental --show-error-codes --no-error-summary $f.py 2>&1 | head -4
  echo "--- mypy +allow-redefinition-new"; $V/mypy --python-version 3.13 --no-incremental --show-error-codes --no-error-summary --allow-redefinition-new --local-partial-types $f.py 2>&1 | head -4
  echo "--- mypy +allow-redefinition"; $V/mypy --python-version 3.13 --no-incremental --show-error-codes --no-error-summary --allow-redefinition $f.py 2>&1 | head -4
  echo "--- ty"; $V/ty check --python-version 3.13 --output-format concise --no-progress --color never $f.py 2>&1 | head -3
  echo "--- pyright"; $V/pyright --pythonversion 3.13 $f.py 2>&1 | grep -E "error|information" | head -3
  echo "--- cpython"; $V/python -I $f.py 2>&1 | tail -1
done
rm -rf $D
