#!/bin/bash
# read-only: what the drafting account has filed (issues and PRs), to see which drafts are already filed
out=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/day9/phase6/search/author.out
: > "$out"
for kind in issues prs; do
  echo "### $kind author DerekLaymn" >> "$out"
  timeout 90 gh search $kind --author DerekLaymn --limit 60 --json repository,number,title,state,createdAt \
    --jq '.[] | "\(.repository.nameWithOwner)#\(.number)\t\(.state)\t\(.createdAt[0:10])\t\(.title)"' >> "$out" 2>&1
  echo "rc=$?" >> "$out"
  sleep 2
done
echo finished >> "$out"
