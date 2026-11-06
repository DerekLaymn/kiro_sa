#!/usr/bin/env bash
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
echo "== partC"; ls campaign/day7/partC
echo "== partD"; ls campaign/day7/partD
echo "== group_yield"; head -60 campaign/day7/partC/group_yield.out
echo "== crash probe"; cat campaign/day7/partB/crash-parents-probe.tsv
echo "== probe script"; cat campaign/day7/partB/probe_ty_crash_parents.sh
echo "== dryrun script"; cat campaign/day7/partB/gen-pass-dryrun.sh
echo "== hits"; ls runs/hits | wc -l; ls runs/hits
echo "== hits-dropped"; ls runs/hits-dropped
echo "== day7 parents"; ls runs/day7 runs/day7/parents
echo "== pins"; .venv/bin/ty --version; .venv/bin/mypy --version; .venv/bin/pyright --version 2>&1 | head -2
