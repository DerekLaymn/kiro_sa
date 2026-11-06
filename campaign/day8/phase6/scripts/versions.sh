cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
echo "== pins (.venv)"
.venv/bin/python --version
.venv/bin/ty --version
.venv/bin/mypy --version
.venv/bin/pyright --version
echo "== /tmp/d3v-latest"
ls /tmp/d3v-latest/bin 2>&1 | head -20
/tmp/d3v-latest/bin/ty --version 2>&1
/tmp/d3v-latest/bin/mypy --version 2>&1
echo "== /tmp/d3v-master"
ls /tmp/d3v-master/bin 2>&1 | head -20
/tmp/d3v-master/bin/mypy --version 2>&1
echo "== ty98 (Day 7 install)"
ls /tmp/d7pd 2>&1
find /tmp/d7pd -maxdepth 5 -name ty -type f 2>&1 | head
echo "== gh release list ty"
timeout 40 gh release list --repo astral-sh/ty --limit 4 2>&1
echo "== uv"
which uv
