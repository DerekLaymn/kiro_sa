K=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
D=$K/campaign/day8/phase6/repro/draft
mkdir -p $D
cp $K/campaign/day8/phase6/repro/c7.py $D/test_bug.py
cp $K/campaign/day8/phase6/repro/c7d.py $D/test_control.py
cd $D
echo "### mypy 2.4.0 test_bug.py"
$K/.venv/bin/mypy --python-version 3.13 --no-incremental test_bug.py; echo "rc=$?"
echo "### mypy 2.4.1 test_bug.py"
/tmp/d3v-latest/bin/mypy --python-version 3.13 --no-incremental test_bug.py; echo "rc=$?"
echo "### mypy master test_bug.py"
/tmp/d3v-master/bin/mypy --python-version 3.13 --no-incremental test_bug.py; echo "rc=$?"
echo "### python test_bug.py"
$K/.venv/bin/python test_bug.py; echo "rc=$?"
echo "### mypy 2.4.0 test_control.py"
$K/.venv/bin/mypy --python-version 3.13 --no-incremental test_control.py; echo "rc=$?"
echo "### mypy master test_control.py"
/tmp/d3v-master/bin/mypy --python-version 3.13 --no-incremental test_control.py; echo "rc=$?"
echo "### ty 0.0.97 / 0.0.98 / pyright on test_bug.py"
$K/.venv/bin/ty check --python-version 3.13 test_bug.py; echo "rc=$?"
/tmp/d7pd/ty98/bin/ty check --python-version 3.13 test_bug.py; echo "rc=$?"
$K/.venv/bin/pyright --pythonversion 3.13 test_bug.py; echo "rc=$?"
