#!/usr/bin/env bash
# Which dry-run prompt shares its key with a Day-3 / Day-4 prompt? (run after overlap_prior.sh, which writes /tmp/d*_keys.txt)
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
for d in 3 4; do
  for k in $(comm -12 /tmp/d9_keys.txt /tmp/d${d}_keys.txt); do
    echo "day$d shares $k"
    grep -m3 -n "Feature area\|area:\|Mutations to apply\|variant" "/tmp/d9-dryrun/inbox/$k" | cut -c1-220
  done
done
