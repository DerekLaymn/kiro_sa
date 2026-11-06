#!/usr/bin/env bash
# Day 8 phase 5: read-only look (gh issue view) at the upstream issues behind the duplicate classification.
# No GitHub write. Output: gh_read.out
for n in 2792 4656 4673; do
  echo "=================== astral-sh/ty#$n"
  gh issue view "$n" --repo astral-sh/ty --json number,title,state,stateReason,closedAt,labels,updatedAt,body,comments \
    --jq '"\(.number) \(.title) | state=\(.state) \(.stateReason) closed=\(.closedAt) updated=\(.updatedAt) labels=\([.labels[].name])\n--- body:\n\(.body)\n--- comments: \(.comments|length)\n\([.comments[]|"[\(.author.login) \(.createdAt)] \(.body)"]|join("\n---\n"))"' 2>&1 | head -150
done
