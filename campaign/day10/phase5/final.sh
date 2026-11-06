#!/bin/bash
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
R=campaign/day10/phase5
rm -f $R/final.done
timeout 1500 .venv/bin/python -m pytest tests -q -p no:cacheprovider > $R/pytest.out 2>&1; echo "rc=$?" >> $R/pytest.out
timeout 600 .venv/bin/typediff --python-version 3.13 kb-selftest > $R/kb-selftest.out 2>&1; echo "rc=$?" >> $R/kb-selftest.out
grep -c "^PASS" $R/kb-selftest.out > $R/kb-pass-count.out; grep -c "^FAIL" $R/kb-selftest.out >> $R/kb-pass-count.out
timeout 600 .venv/bin/python campaign/day4m/check_hits.py 0.80 > $R/check_hits-final.out 2>&1; echo "rc=$?" >> $R/check_hits-final.out
.venv/bin/typediff --version > /dev/null 2>&1
for t in mypy ty pyright; do echo "$t: $(timeout 60 .venv/bin/$t --version 2>&1 | head -1)"; done > $R/pins.out
touch $R/final.done
