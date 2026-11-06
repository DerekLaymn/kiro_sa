#!/usr/bin/env bash
# Answer every pending prompt in runs/day9/inbox with the headless generator (batches of 5, 4 sessions at once).
# Generator: kiro-cli --agent-engine v3 --model claude-haiku-5.5 --effort medium (see gen_worker.sh).
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
INBOX=$ROOT/runs/day9/inbox
cd "$ROOT" || exit 1
PEND=""
for p in "$INBOX"/*.prompt.md; do
  k=$(basename "$p" .prompt.md)
  [ -e "$INBOX/$k.answer.json" ] || PEND="$PEND $k"
done
echo "pending: $(echo $PEND | wc -w)"
echo $PEND | tr ' ' '\n' | xargs -n 5 -P 4 bash campaign/day9/gen_worker.sh
echo "answer_pending done"
