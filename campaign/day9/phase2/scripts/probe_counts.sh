#!/usr/bin/env bash
# Counts from the crash probe TSV (ty rows by location and rc).
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
T=campaign/day9/phase2/results/crash-parents-probe.tsv
echo "ty rows total: $(awk -F'\t' '$3=="ty"' $T | wc -l)"
echo "ty rows in hits: $(awk -F'\t' '$3=="ty" && $2=="hits"' $T | wc -l)"
echo "ty rows in hits-dropped: $(awk -F'\t' '$3=="ty" && $2=="hits-dropped"' $T | wc -l)"
echo "ty rc by value:"; awk -F'\t' '$3=="ty"{print $4}' $T | sort | uniq -c
echo "ty rows with rc>=100: $(awk -F'\t' '$3=="ty" && $4>=100' $T | wc -l)"
echo "ty rows rc<100: $(awk -F'\t' '$3=="ty" && $4<100' $T | wc -l)"
cp /tmp/d9p2/live.py campaign/day9/phase2/scripts/live_by_area.py
cp /tmp/d9p2/show.py campaign/day9/phase2/scripts/show_live_rows.py
cp /tmp/d9p2/live.out campaign/day9/phase2/results/day8-live-by-area.txt
cp /tmp/d9p2/live2.out campaign/day9/phase2/results/day8-live-programs.txt
cp /tmp/d9p2/show1.out campaign/day9/phase2/results/reserve-candidates-rows.txt
cp /tmp/d9p2/show2.out campaign/day9/phase2/results/reserve-candidates-rows-2.txt
ls campaign/day9/phase2/results
