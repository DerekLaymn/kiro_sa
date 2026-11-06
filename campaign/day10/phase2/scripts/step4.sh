#!/usr/bin/env bash
# Counts from the crash probe TSV (Day 10 vs Day 9) and the areas that have no parent in runs/hits after the promotion.
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
R=campaign/day10/phase2/results
T=$R/crash-parents-probe.tsv
T9=campaign/day9/phase2/results/crash-parents-probe.tsv
{
echo "ty rows total: $(awk -F'\t' '$3=="ty"' $T | wc -l)"
echo "ty rows in hits: $(awk -F'\t' '$3=="ty" && $2=="hits"' $T | wc -l)"
echo "ty rows in hits-dropped: $(awk -F'\t' '$3=="ty" && $2=="hits-dropped"' $T | wc -l)"
echo "ty rc by value:"; awk -F'\t' '$3=="ty"{print $4}' $T | sort | uniq -c
echo "ty rows with rc>=100: $(awk -F'\t' '$3=="ty" && $4>=100' $T | wc -l)"
echo "ty rows rc<100: $(awk -F'\t' '$3=="ty" && $4<100' $T | wc -l)"
echo "non-ty rows:"; awk -F'\t' '$3!="ty" && NR>1' $T
echo "files probed on both days: $(cut -f1,3 $T | sort -u | comm -12 - <(cut -f1,3 $T9 | sort -u) | wc -l)"
echo "files probed on both days whose rc differs:"
join -t "$(printf '\t')" -j1 <(awk -F'\t' 'NR>1{print $1"|"$3"\t"$4}' $T | sort) <(awk -F'\t' 'NR>1{print $1"|"$3"\t"$4}' $T9 | sort) | awk -F'\t' '$2!=$3'
echo "(end of rc differences)"
} > $R/probe-counts.out 2>&1
.venv/bin/python campaign/day7/partB/areas_without_hits.py > $R/areas-without-hits-after.txt 2>&1
echo "step4 done" > $R/step4.done
