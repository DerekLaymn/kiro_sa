cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
R=campaign/day10/phase2/results
mkdir -p $R
.venv/bin/python campaign/day4m/check_hits.py 0.80 > $R/check_hits-before.out 2>&1
echo "check_hits rc=$?" >> $R/check_hits-before.out
bash campaign/day10/phase2/scripts/probe_crash_parents.sh > $R/crash-parents-probe.tsv 2> $R/crash-parents-probe.err
echo "probe rc=$?" > $R/crash-parents-probe.done
.venv/bin/ty --version >> $R/crash-parents-probe.done 2>&1
.venv/bin/mypy --version >> $R/crash-parents-probe.done 2>&1
.venv/bin/pyright --version >> $R/crash-parents-probe.done 2>&1
