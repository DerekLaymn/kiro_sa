#!/usr/bin/env bash
# Dry run of campaign/day7/gen_pass.sh against a scratch inbox/out (no LLM answers, nothing under runs/day7/{inbox,gen},
# no status file for the real gate). Records the pass-1 prompt count: expected pending=224.
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd "$ROOT" || exit 1
S=/tmp/d7-dryrun
rm -rf "$S"; mkdir -p "$S"
bash campaign/day7/mk_groups.sh
export DAY7_INBOX=$S/inbox DAY7_OUT=$S/gen DAY7_GATE=$S/status.json DAY7_LOG=$S/gen-pass.log DAY7_RETRIES=1 DAY7_SLEEP=0
bash campaign/day7/gen_pass.sh dryrun
echo "--- prompts by file count"
ls "$S/inbox"/*.prompt.md | wc -l
cat "$S/status.json"
