#!/usr/bin/env bash
# How many of the dry-run prompts have the same key (= same prompt text) as a prompt of Days 3 to 9? A shared key would
# only reproduce an earlier program. Reads /tmp/d10-dryrun/inbox (campaign/day10/gen-pass-dryrun.sh).
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
ls /tmp/d10-dryrun/inbox | grep '\.prompt\.md$' | sort > /tmp/d10_keys.txt
echo "day10 prompts: $(wc -l < /tmp/d10_keys.txt)  distinct: $(sort -u /tmp/d10_keys.txt | wc -l)"
TOTAL=0
for d in 3 4 5 6 7 8 9; do
  ls runs/day$d/inbox | grep '\.prompt\.md$' | sort > /tmp/d10_prior_d${d}.txt
  n=$(comm -12 /tmp/d10_keys.txt /tmp/d10_prior_d${d}.txt | wc -l)
  TOTAL=$((TOTAL+n))
  echo "day$d prompts: $(wc -l < /tmp/d10_prior_d${d}.txt)  same key as day10: $n"
done
echo "shared with Days 3-9 in total: $TOTAL"
