K=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd $K
echo "== pyproject ty config"
grep -n "tool.ty" -A6 pyproject.toml
mkdir -p /tmp/d8x
cp campaign/day8/phase6/repro/c9c.py /tmp/d8x/
cd /tmp/d8x
echo "== ty 0.0.97 outside the project dir"
$K/.venv/bin/ty check --python-version 3.13 c9c.py 2>&1 | head -50
echo "== ty 0.0.98 outside"
/tmp/d7pd/ty98/bin/ty check --python-version 3.13 c9c.py 2>&1 | grep -E "^\s+\|\s+\^|Revealed" | head -20
