#!/usr/bin/env bash
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
for d in runs/day7/parents/*/; do echo "$(basename $d) $(ls $d | wc -l)"; done
ls -la --time-style=full-iso runs/day7/parents | head
ls runs/day7/parents/A_ty_4148 runs/day7/parents/A_ty_protocol_capped
ls /tmp/d7-dryrun 2>&1 | head
echo "hits $(ls runs/hits/*.py | wc -l)"
git status --short | head
