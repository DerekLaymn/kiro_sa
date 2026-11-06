#!/bin/bash
# Read-only status of the issues listed by the author search (state, reason, labels, comment count, last comment head).
O=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/day10/phase7/results/gh_status.out
: > $O
for spec in astral-sh/ty#4933 astral-sh/ty#4934 python/mypy#22377 astral-sh/ty#4941 python/mypy#22375 astral-sh/ty#4958 microsoft/pyright#11984 python/mypy#22385 python/mypy#22386 astral-sh/ty#4656 astral-sh/ty#4882 astral-sh/ty#4883 astral-sh/ty#4884 astral-sh/ty#4898 astral-sh/ty#4899 astral-sh/ty#4900 python/mypy#22339 python/mypy#22343 python/mypy#22344 python/mypy#22360 python/mypy#22361 microsoft/pyright#11851 microsoft/pyright#11960 microsoft/pyright#11961; do
  repo=${spec%%#*}; num=${spec##*#}
  ok=0
  for i in 1 2 3; do
    res=$(timeout 60 gh issue view "$num" --repo "$repo" --json number,title,state,stateReason,closedAt,labels,author,comments -q '"\(.title[0:90]) | \(.state) \(.stateReason // "") | closed \(.closedAt // "-") | labels: \([.labels[].name] | join(",")) | author \(.author.login) | comments \(.comments | length) | last: \(if (.comments|length)>0 then (.comments[-1] | "[\(.author.login) \(.createdAt[0:10])] \(.body[0:260] | gsub("\n";" "))") else "-" end)"' 2>&1) && { echo "$spec :: $res" >> $O; ok=1; break; }
    sleep 4
  done
  [ $ok = 0 ] && echo "$spec :: NOT VERIFIED (gh failed 3 times): $res" >> $O
done
echo finished >> $O
