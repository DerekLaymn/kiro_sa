F=/tmp/d3v-master/lib/python3.13/site-packages/mypy/binder.py
grep -n "def assign_type" $F
N=$(grep -n "def assign_type" $F | head -1 | cut -d: -f1)
sed -n "${N},$((N+75))p" $F
