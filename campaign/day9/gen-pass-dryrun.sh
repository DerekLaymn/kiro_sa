#!/usr/bin/env bash
# Dry run of campaign/day9/gen_pass.sh against a scratch inbox/out (no LLM answers, nothing under runs/day9/{inbox,gen},
# no status file for the real gate). Records the prompt count: expected pending=250.
# It rebuilds runs/day9/parents with mk_groups.sh (that directory is only used by Day 9).
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd "$ROOT" || exit 1
S=/tmp/d9-dryrun
rm -rf "$S"; mkdir -p "$S"
bash campaign/day9/mk_groups.sh || exit 1
export DAY9_INBOX=$S/inbox DAY9_OUT=$S/gen DAY9_GATE=$S/status.json DAY9_LOG=$S/gen-pass.log DAY9_RETRIES=1 DAY9_SLEEP=0
bash campaign/day9/gen_pass.sh dryrun
echo "--- prompt files"
ls "$S/inbox"/*.prompt.md | wc -l
echo "--- answers"
ls "$S/inbox"/*.answer.json 2>/dev/null | wc -l
cat "$S/status.json"
