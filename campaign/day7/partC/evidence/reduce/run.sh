cd /tmp/d7/tp
cat > v1.py <<'EOF'
from typing import reveal_type
def f(items: tuple[int, ...]) -> None:
    value: int | str = 1
    try:
        value, (a, b) = "bad", items
    except ValueError:
        reveal_type(value)
f((1,))
EOF
cat > v2.py <<'EOF'
from typing import reveal_type
def f() -> None:
    value: int | str = 1
    try:
        value = "bad"
        int("x")
    except ValueError:
        reveal_type(value)
f()
EOF
cat > v3.py <<'EOF'
from typing import reveal_type
def f() -> None:
    value: int | str = 1
    try:
        value = "bad"
        raise ValueError
    except ValueError:
        reveal_type(value)
f()
EOF
cat > v4.py <<'EOF'
from typing import reveal_type
def g() -> int:
    raise ValueError
def f() -> None:
    value: int | str = 1
    try:
        value, other = "bad", g()
    except ValueError:
        reveal_type(value)
f()
EOF
cat > v5.py <<'EOF'
from typing import reveal_type
def f() -> None:
    value: int | str = 1
    try:
        value = "bad"
        value = 2
        int("x")
    except ValueError:
        reveal_type(value)
f()
EOF
cat > v6.py <<'EOF'
from typing import reveal_type
def f(items: list[int]) -> None:
    value: int | str = 1
    try:
        value, a, b = "bad", *items
    except ValueError:
        reveal_type(value)
f([1])
EOF
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.venv/bin
for v in v1 v2 v3 v4 v5 v6; do
  echo "######## $v"
  python3 $v.py 2>&1 | tail -n 1
  echo "-- mypy"; $R/mypy --python-version 3.13 $v.py 2>&1 | grep -E "Revealed|error" | head -3
  echo "-- ty"; $R/ty check --python-version 3.13 --output-format concise $v.py 2>&1 | grep -E "revealed|Revealed|error" | head -3
  echo "-- pyright"; $R/pyright --pythonversion 3.13 $v.py 2>&1 | grep -E "Type of|error" | head -3
done
