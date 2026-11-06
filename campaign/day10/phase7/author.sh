#!/bin/bash
OUT=/tmp/p7_author.out
: > $OUT
for kind in issues prs; do
  echo "##### $kind" >> $OUT
  for i in 1 2 3; do
    res=$(timeout 60 gh search $kind --author DerekLaymn --limit 60 --json repository,number,title,state,createdAt -q '.[] | "\(.repository.nameWithOwner)#\(.number)\t\(.state)\t\(.createdAt[0:10])\t\(.title)"' 2>&1) && { echo "$res" >> $OUT; break; }
    echo "attempt $i failed: $res" >> $OUT; sleep 5
  done
done
echo finished >> $OUT
