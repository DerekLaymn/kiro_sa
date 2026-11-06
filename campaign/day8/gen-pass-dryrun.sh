#!/usr/bin/env bash
# Dry run of campaign/day8/gen_pass.sh against a scratch inbox/out (no LLM answers, nothing under runs/day8/{inbox,gen},
# no status file for the real gate). Records the prompt count: expected pending=250.
# It rebuilds runs/day8/parents with mk_groups.sh (that directory is only used by Day 8).
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd "$ROOT" || exit 1
S=/tmp/d8-dryrun
rm -rf "$S"; mkdir -p "$S"
bash campaign/day8/mk_groups.sh || exit 1
export DAY8_INBOX=$S/inbox DAY8_OUT=$S/gen DAY8_GATE=$S/status.json DAY8_LOG=$S/gen-pass.log DAY8_RETRIES=1 DAY8_SLEEP=0
bash campaign/day8/gen_pass.sh dryrun
echo "--- prompt files"
ls "$S/inbox"/*.prompt.md | wc -l
echo "--- answers"
ls "$S/inbox"/*.answer.json 2>/dev/null | wc -l
cat "$S/status.json"
