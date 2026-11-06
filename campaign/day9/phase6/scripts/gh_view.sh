#!/bin/bash
# read-only: gh issue view / gh pr view. usage: gh_view.sh <out-file> <spec-file>   (lines: issue|repo|number or pr|repo|number)
out="$1"
spec="$2"
: > "$out"
while IFS='|' read -r kind repo num; do
  [ -z "$kind" ] && continue
  case "$kind" in \#*) continue;; esac
  echo "################ $kind $repo#$num" >> "$out"
  timeout 60 gh $kind view "$num" --repo "$repo" \
    --json number,title,state,author,createdAt,closedAt,labels,body,comments \
    --jq '"#\(.number) [\(.state)] \(.title)\nauthor: \(.author.login)  created: \(.createdAt)  closed: \(.closedAt)\nlabels: \([.labels[].name] | join(","))\n--- body\n\(.body[0:2500])\n--- comments (\(.comments|length))\n\(.comments | map("[\(.author.login) \(.createdAt[0:10])] \(.body[0:700])") | join("\n---\n"))"' >> "$out" 2>&1
  echo "rc=$?" >> "$out"
  sleep 2
done < "$spec"
echo "finished" >> "$out"
