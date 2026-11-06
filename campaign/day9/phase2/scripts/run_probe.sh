cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
mkdir -p campaign/day9/phase2/results
bash campaign/day9/phase2/scripts/probe_crash_parents.sh > campaign/day9/phase2/results/crash-parents-probe.tsv 2> campaign/day9/phase2/results/crash-parents-probe.err
echo "probe rc=$?" > campaign/day9/phase2/results/crash-parents-probe.done
.venv/bin/ty --version >> campaign/day9/phase2/results/crash-parents-probe.done 2>&1
