#!/bin/bash
# read-only: issues and PRs by the drafting account, to see which drafts were filed since Day 9
out=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/day10/phase6/search/author.out
: > $out
for kind in issues prs; do
  echo "##### $kind" >> $out
  for try in 1 2 3; do
    res=$(timeout 60 gh search $kind --author DerekLaymn --limit 40 --json repository,number,title,state,createdAt -q '.[] | "\(.repository.nameWithOwner)#\(.number)\t\(.state)\t\(.createdAt[0:10])\t\(.title)"' 2>&1) && break
    sleep $((try * 4))
  done
  echo "$res" >> $out
done
echo finished >> $out
