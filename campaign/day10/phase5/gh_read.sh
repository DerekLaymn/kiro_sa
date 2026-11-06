#!/usr/bin/env bash
# Day 10 phase 5 (Plan §3 "add an upstream entry ... only after a read-only gh issue view"). Read-only gh calls only.
for n in 8595 14122 15182; do
  echo "=== python/mypy#$n"
  timeout 60 gh issue view "$n" --repo python/mypy --json number,title,state,closedAt,stateReason,labels,url,body --jq '{number,title,state,closedAt,stateReason,url,labels:[.labels[].name],body:(.body|.[0:900])}'
  echo "--- comments (last 3)"
  timeout 60 gh issue view "$n" --repo python/mypy --comments 2>/dev/null | tail -n 40 | cut -c1-300
done
echo "=== mypy search: unquoted forward reference in own class body annotation (candidate gen1_5c366404)"
timeout 60 gh search issues "forward reference annotation class body NameError not reported" --repo python/mypy --limit 8 --json number,title,state,url
timeout 60 gh search issues "undefined name annotation method return own class" --repo python/mypy --limit 8 --json number,title,state,url
