#!/usr/bin/env bash
export TYPEDIFF_LLM=null
V=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.venv/bin
D=$(mktemp -d /tmp/s3p8.XXXXXX)
cd $D
cat > fwd.py <<'EOF'
class F(E): pass
class E: pass
EOF
cat > emptyloop.py <<'EOF'
def f() -> None:
    for x in []:
        c = 789
    del c
EOF
cat > cond.py <<'EOF'
def g(flag: bool) -> None:
    if flag:
        c = 789
    print(c)
EOF
cat > fwdfn.py <<'EOF'
print(h())
def h() -> int:
    return 1
EOF
cat > fwdvar.py <<'EOF'
print(v)
v = 1
EOF
cat > undef.py <<'EOF'
print(nothere)
EOF
for f in fwd emptyloop cond fwdfn fwdvar undef; do
  echo "######## $f"
  echo "--- mypy default";  $V/mypy --python-version 3.13 --no-incremental --show-error-codes --no-error-summary $f.py 2>&1 | head -5
  echo "--- mypy +used-before-def"; $V/mypy --python-version 3.13 --no-incremental --show-error-codes --no-error-summary --enable-error-code used-before-def $f.py 2>&1 | head -5
  echo "--- mypy +possibly-undefined +used-before-def"; $V/mypy --python-version 3.13 --no-incremental --show-error-codes --no-error-summary --enable-error-code possibly-undefined --enable-error-code used-before-def $f.py 2>&1 | head -5
  echo "--- ty"; $V/ty check --python-version 3.13 --output-format concise --no-progress --color never $f.py 2>&1 | head -5
  echo "--- cpython"; $V/python -I $f.py 2>&1 | tail -1
done
rm -rf $D
