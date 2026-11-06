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
/tmp/d3v-master/bin/mypy --version 2>&1
echo "== ty98 (Day 7 install)"
ls /tmp/d7pd 2>&1
ls /tmp/d7pd/ty98/bin 2>&1
/tmp/d7pd/ty98/bin/ty --version 2>&1
echo "== gh release list ty"
timeout 40 gh release list --repo astral-sh/ty --limit 4 2>&1
echo "== gh release list mypy"
timeout 40 gh release list --repo python/mypy --limit 3 2>&1
echo "== gh release list pyright"
timeout 40 gh release list --repo microsoft/pyright --limit 3 2>&1
echo "== pypi latest"
timeout 40 curl -s https://pypi.org/pypi/ty/json | .venv/bin/python -c "import json,sys; d=json.load(sys.stdin); print('ty', d['info']['version'], d['releases'][d['info']['version']][0]['upload_time'])"
timeout 40 curl -s https://pypi.org/pypi/mypy/json | .venv/bin/python -c "import json,sys; d=json.load(sys.stdin); print('mypy', d['info']['version'], d['releases'][d['info']['version']][0]['upload_time'])"
timeout 40 curl -s https://pypi.org/pypi/pyright/json | .venv/bin/python -c "import json,sys; d=json.load(sys.stdin); print('pyright', d['info']['version'], d['releases'][d['info']['version']][0]['upload_time'])"
date -u
