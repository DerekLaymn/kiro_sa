#!/usr/bin/env bash
# How many of the dry-run prompts have the same key (= same prompt text) as a prompt of Days 3 to 8? A shared key would
# only reproduce an earlier program. Reads /tmp/d9-dryrun/inbox (campaign/day9/gen-pass-dryrun.sh).
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
ls /tmp/d9-dryrun/inbox | grep '\.prompt\.md$' | sort > /tmp/d9_keys.txt
echo "day9 prompts: $(wc -l < /tmp/d9_keys.txt)  distinct: $(sort -u /tmp/d9_keys.txt | wc -l)"
for d in 3 4 5 6 7 8; do
  ls runs/day$d/inbox | grep '\.prompt\.md$' | sort > /tmp/d${d}_keys.txt
  echo "day$d prompts: $(wc -l < /tmp/d${d}_keys.txt)  same key as day9: $(comm -12 /tmp/d9_keys.txt /tmp/d${d}_keys.txt | wc -l)"
done
