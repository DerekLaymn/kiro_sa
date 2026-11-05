#!/bin/bash
# Run the full (no-LLM) pipeline over runs/hits to confirm each promoted parent still shows its disagreement/crash.
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd $R
rm -rf runs/day3/hitscheck
export TYPEDIFF_LLM=null
date > campaign/day3m/run_hits.start
$R/.venv/bin/typediff --out $R/runs/day3/hitscheck --python-version 3.13 seeds $R/runs/hits > campaign/day3m/run_hits.log 2>&1
echo "exit $?" >> campaign/day3m/run_hits.log
$R/.venv/bin/typediff --out $R/runs/day3/hitscheck triage $R/runs/day3/hitscheck --top 80 --details > campaign/day3m/run_hits_triage.txt 2>&1
date > campaign/day3m/run_hits.done
