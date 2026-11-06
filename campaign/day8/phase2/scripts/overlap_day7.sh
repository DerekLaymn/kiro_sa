#!/usr/bin/env bash
# How many of the 250 dry-run prompts have the same key (= same prompt text) as a Day-7 prompt? Same key would only
# reproduce a Day-7 program.
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
ls /tmp/d8-dryrun/inbox | grep '\.prompt\.md$' | sort > /tmp/d8_keys.txt
ls runs/day7/inbox | grep '\.prompt\.md$' | sort > /tmp/d7_keys.txt
echo "day8 prompts: $(wc -l < /tmp/d8_keys.txt)  day7 prompts: $(wc -l < /tmp/d7_keys.txt)"
echo "same key in both: $(comm -12 /tmp/d8_keys.txt /tmp/d7_keys.txt | wc -l)"
echo "distinct day8 keys: $(sort -u /tmp/d8_keys.txt | wc -l)"
