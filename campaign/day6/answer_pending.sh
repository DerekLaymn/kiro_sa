#!/usr/bin/env bash
# Answer every pending prompt in runs/day6/inbox with the haiku-5.5 stand-in (batches of 5, 4 sessions at once).
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
INBOX=$ROOT/runs/day6/inbox
cd "$ROOT" || exit 1
PEND=""
for p in "$INBOX"/*.prompt.md; do
  k=$(basename "$p" .prompt.md)
  [ -e "$INBOX/$k.answer.json" ] || PEND="$PEND $k"
done
echo "pending: $(echo $PEND | wc -w)"
echo $PEND | tr ' ' '\n' | xargs -n 5 -P 4 bash campaign/day6/gen_worker.sh
echo "answer_pending done"
