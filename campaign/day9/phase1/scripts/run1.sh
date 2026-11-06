cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
# usage: run1.sh OUTDIR  (inputs in /tmp/d9/in1)
O=${1:-/tmp/d9/out1}
rm -rf "$O"
TYPEDIFF_LLM=null .venv/bin/python scripts/kbloop_run.py "$O" /tmp/d9/in1 --jobs 3 --pyright-only --progress "$O.progress"
for f in "$O"/*.json; do echo "== $f"; .venv/bin/python /tmp/d9/g.py "$f"; done
