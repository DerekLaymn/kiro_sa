#!/usr/bin/env bash
# Day 8 phase 4: run campaign/day8/judge.sh while sampling MemAvailable once per second.
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd "$ROOT" || exit 1
D=campaign/day8/phase4
rm -f campaign/day8/judge.done $D/mem.done
date '+%Y-%m-%d %H:%M:%S' > $D/window.start
date --iso-8601=seconds > $D/window.start.iso
: > $D/memavail.tsv
( while true; do echo "$(date +%s) $(awk '/MemAvailable/{print $2}' /proc/meminfo)" >> $D/memavail.tsv; sleep 1; done ) &
SP=$!
bash campaign/day8/judge.sh > $D/judge-sh.out 2>&1
echo "judge.sh exit=$?" >> $D/judge-sh.out
kill $SP
date '+%Y-%m-%d %H:%M:%S' > $D/window.end
date --iso-8601=seconds > $D/window.end.iso
touch $D/mem.done
