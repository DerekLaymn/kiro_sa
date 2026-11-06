#!/usr/bin/env bash
# Which dry-run prompt shares its key with a prompt of Days 3 to 9? (run after overlap_prior.sh, which writes /tmp/d10_*.txt)
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
for d in 3 4 5 6 7 8 9; do
  for k in $(comm -12 /tmp/d10_keys.txt /tmp/d10_prior_d${d}.txt); do
    echo "day$d shares $k"
    grep -m3 -n "Feature area\|Mutations to apply\|^Variant" "/tmp/d10-dryrun/inbox/$k" | cut -c1-220
  done
done
