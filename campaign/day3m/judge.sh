cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
export TYPEDIFF_LLM=null
P=.venv/bin/python
$P scripts/kbloop_run.py runs/day3/out runs/day3/gen --jobs 14 --progress runs/day3/out-progress.log
echo RUNDONE
$P scripts/kbloop_stats.py runs/day3/out > campaign/day3-stats.txt 2>&1
.venv/bin/typediff --out runs/day3/out triage runs/day3/out --top 30 --details > campaign/day3-triage.txt 2>&1
echo ALLDONE
