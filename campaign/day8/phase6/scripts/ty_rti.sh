K=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd $K/campaign/day8/phase6/repro
CFG='analysis.return-type-inference = "always"'
echo "== ty 0.0.97, c9.py, default config"
$K/.venv/bin/ty check --python-version 3.13 c9.py 2>&1 | grep -E "^(info|error|warning)|\^\^\^|Found|All checks"
echo "== ty 0.0.97, c9.py, $CFG"
$K/.venv/bin/ty check --python-version 3.13 --config "$CFG" c9.py 2>&1 | grep -E "^(info|error|warning)|\^\^\^|Found|All checks|TOML|unknown"
echo "== ty 0.0.97, c8ctl.py, $CFG"
$K/.venv/bin/ty check --python-version 3.13 --config "$CFG" c8ctl.py 2>&1 | grep -E "^(info|error|warning)|\^\^\^|Found|All checks|TOML|unknown"
echo "== ty 0.0.97, p_delete_f631bce3.py, $CFG"
$K/.venv/bin/ty check --python-version 3.13 --config "$CFG" p_delete_f631bce3.py 2>&1 | grep -E "^(info|error|warning)|\^\^\^|Found|All checks|TOML|unknown|^[0-9]+ \|"
echo "== ty 0.0.98, c9.py, $CFG"
/tmp/d7pd/ty98/bin/ty check --python-version 3.13 --config "$CFG" c9.py 2>&1 | grep -E "^(info|error|warning)|\^\^\^|Found|All checks|TOML|unknown"
