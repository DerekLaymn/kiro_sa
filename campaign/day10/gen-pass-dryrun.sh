#!/usr/bin/env bash
# Dry run of campaign/day10/gen_pass.sh against a scratch inbox/out (no LLM answers, nothing under runs/day10/{inbox,gen},
# no status file for the real gate). Records the prompt count: expected pending=250.
# It rebuilds runs/day10/parents with mk_groups.sh (that directory is only used by Day 10).
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd "$ROOT" || exit 1
S=/tmp/d10-dryrun
rm -rf "$S"; mkdir -p "$S"
bash campaign/day10/mk_groups.sh || exit 1
export DAY10_INBOX=$S/inbox DAY10_OUT=$S/gen DAY10_GATE=$S/status.json DAY10_LOG=$S/gen-pass.log DAY10_RETRIES=1 DAY10_SLEEP=0
bash campaign/day10/gen_pass.sh dryrun
echo "--- prompt files"
ls "$S/inbox"/*.prompt.md | wc -l
echo "--- answers"
ls "$S/inbox"/*.answer.json 2>/dev/null | wc -l
cat "$S/status.json"
