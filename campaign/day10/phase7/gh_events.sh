#!/bin/bash
O=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/day10/phase7/results/gh_events_4934.out
: > $O
for i in 1 2 3; do
  res=$(timeout 60 gh api repos/astral-sh/ty/issues/4934/timeline --paginate -q '.[] | "\(.event) | \(.actor.login // .user.login // "-") | \(.created_at // "-") | \(.commit_id // "") | \(.source.issue.number // "") \(.source.issue.title // "")"' 2>&1) && { echo "$res" >> $O; break; }
  echo "attempt $i failed: $res" >> $O; sleep 4
done
echo finished >> $O
